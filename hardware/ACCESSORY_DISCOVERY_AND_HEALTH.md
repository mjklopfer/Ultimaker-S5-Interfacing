# Accessory startup, identity and health

Reference: S5 R1 host firmware 9.0.3.0. These are observations from captured host
consumers and configuration, not a capture of a working replacement accessory.
No manufacturer implementation or firmware image is included here.

## Required architecture: two STM32 controllers

The project uses two physical STM32 controllers, one fixed role per controller.
The observed stock Linux host expects an STM32 bootloader interface and uses
distinct STM32 chip-ID/memory profiles to identify and start the accessories.
This makes STM32 the required target for the selected native-interface design.

Suggested bench boards are NUCLEO-F072RB and NUCLEO-F303ZE. See the
[STM32 development plan](umb-controller/STM32_DEPLOYMENT.md). Matching silicon
alone does not solve boot entry, custom-firmware handling, chain control or
operational behavior. Neither board has been validated as an S5 replacement.

## Observed normal startup sequence

1. Linux opens the accessory UART using the configured 115200 baud, 8E1 framing.
2. For the first device, it asserts a serial BREAK, then attempts STM32 bootloader
   communication. One host branch requests roughly 0.7 seconds of BREAK; another
   branch has a source comment about inconsistent timing. Actual wire timing and
   the circuit translating BREAK into peripheral reset/boot selection need capture.
3. It reads the chip ID and looks it up in host MCU configuration. That mapping
   supplies the device type/name and memory layout. It is not merely an accessory
   sending a friendly model name over the operational protocol.
4. It reads configured memory/option information and checks the expected accessory
   firmware. The observed comparison reads the final 256-byte page of the
   configured flash region and compares it with the corresponding expected image
   data, padded with zero bytes when needed. This is not proof of whole-image
   integrity and is not a simple firmware-version query.
5. A mismatch can lead to erase/program operations. The host then leaves programming
   mode using configured RAM/application-entry information.
6. It assigns a bus address and instructs that device to enable the next chain
   link. For later devices, it uses the preceding device's RESET_NEXT command
   rather than the first-device BREAK procedure.
7. When the next bootloader does not answer, the host broadcasts ENTER_OPERATIONAL
   twice, waits, and clears its serial input. This is the observed end-of-chain
   behavior, not proof that every timeout represents a healthy absent device.
8. For every discovered device it walks register indices, retrieves names and
   initial values, publishes a UMB D-Bus object, and starts configured Linux
   services according to that device's type.

Startup is potentially state-changing. Do not restart enumeration or send BREAK,
reset, programming or discovery-control traffic on an operating printer to probe
presence. This document was prepared from existing local captures.

## Address and startup message structure

| Item | Observed contract |
|---|---|
| Address width | One byte in the startup and operational request formats |
| Assigned addresses | Chain order starting at 0x00, then 0x01, etc. |
| Initial address | 0xFF |
| General-call/broadcast address | 0xFE |
| SET_DEVICE_ADDRESS | Startup command 0x00; argument is the assigned address |
| ENABLE_NEXT | Startup command 0x01; observed enable argument 1 |
| RESET_NEXT | Startup command 0x02; host sends 1, waits, then 0 |
| ENTER_OPERATIONAL | Startup command 0x80; observed argument 0 |

The observed startup control envelope is seven bytes:

`21 DE FF address command argument checksum`

The checksum is the XOR of `FF`, address, command and argument. The host expects
an ASCII `!` acknowledgement when a reply is requested. This describes the
chain-control envelope, **not the complete STM32 programming protocol**. Its
commands and checksum must not be confused with the operational protocol's
length field and CRC8, even where numeric command values overlap.

Addresses are chain positions, not a printer MAC, serial number or persistent
accessory identity. Do not assume the practical device count or every reserved
address rule from the one-byte field alone.

Both role configurations were found in the saved host captures:

| Host configuration field | Air Manager | Material Station |
|---|---|---|
| Chip ID | `0x0448` | `0x0446` |
| Configured family label | STM32F070xB/F071xx/F72xx | STM32F302xD(E)/F303xD(E)/F398xx |
| Device type/name | `airmanager` | `misp` |
| Linux service template | `airmanager@{id}.service` | `misp@{id}.service` |
| Flash start | `0x08000000` | `0x08000000` |
| Configured flash end | `0x08020000` | `0x08060000` |
| Region size | 128 KiB | 384 KiB |
| Compared 256-byte block start | `0x0801FF00` | `0x0805FF00` |
| Configured RAM start argument | `0x20001800` | `0x20001800` |
| Configured RAM end/stack argument | `0x20004000` | `0x20010000` |
| Configured erase page size | `0x800` bytes | `0x800` bytes |
| Mass erase supported in host config | true | true |
| Configured option-memory range | `0x1FFFF800` to `0x1FFFF80F` | `0x1FFFF800` to `0x1FFFF80F` |
| Configured system-memory range | `0x1FFFC800` to `0x1FFFF800` | `0x1FFFD800` to `0x1FFFF800` |
| OTP read configured | none | none |

These are **host configuration values**, not a new custom-board linker script,
verified physical chip capacity, or directions to change option bytes. The family
labels reproduce the configured identification text; verify exact silicon before
board selection. Chip IDs identify families, not unique units. The saved service
configuration also routes `airmanager-r2` to the Air Manager service; a distinct
R2 MCU/memory profile is not established.

The saved `leaveProgrammingMode` helper has now been inspected. It writes a small
reset routine into SRAM at the configured RAM start, including initial stack and
Thumb entry vectors, then invokes Go at that SRAM address. The routine requests
a Cortex-M system reset through AIRCR. Even the firmware-match path therefore
requires SRAM write and execution. No vendor instruction payload is reproduced.
Do not treat `0x20001800` as a custom flash linker/vector-table address. Hardware
boot-pin/chain behavior on the subsequent reset still needs validation.

The operational Air Manager register `data.VersionSwBuildTime.0` supplies its
firmware-version property. It is separate from the bootloader chip-ID and flash
comparison. No fabricated build-time value is established as a compatibility key.

### Bootloader protocol knowledge and remaining work

ST's [AN3155 USART bootloader specification](https://www.st.com/resource/en/application_note/an3155-how-to-use-usart-protocol-in-bootloader-on-stm32-mcus-stmicroelectronics.pdf)
documents synchronization (`0x7F`), ACK (`0x79`), NACK (`0x1F`), Get (`0x00`),
Get Version (`0x01`), Get ID (`0x02`), Read Memory (`0x11`), Go (`0x21`),
Write Memory (`0x31`) and device-dependent erase commands. These are standard
reference values, not evidence that the captured host helper uses every command
or that its bootloader extensions exactly match an unmodified ST ROM. Check
device-specific boot entry and available UARTs against AN2606 and the selected
part documentation. The UMB chain-control `!` is separate from ST ACK `0x79`.

The host call sites establish reads of chip ID, option memory and the firmware
comparison region, plus optional erase and write/verify using 256-byte chunks.
The saved helper establishes the following additional contracts:

| Phase | Observed behavior |
|---|---|
| Sync | Up to five 0x7F attempts; ACK 0x79 or NACK 0x1F proceeds to Get |
| Base information | Get 0x00 supplies version and supported commands; this helper logs them without checking for one fixed version |
| Command | Byte plus bitwise complement; expect ACK |
| Data | Payload plus bytewise XOR checksum; expect ACK |
| Read | Four-byte big-endian address; chunk-length-minus-one and complement; up to 256 bytes per chunk |
| Get/Get-ID response | Length byte, length+1 data bytes, final ACK; chip-ID data converted directly to hexadecimal text |
| Ranges | High address is exclusive in the memory-read helper |
| Mass erase | Extended erase 0x44 with 0xFFFF selector and longer timeout |
| Reset to application | Write SRAM reset routine, then Go at its SRAM vector table |
| Host timeouts | Default 0.5 s; boot enumeration 0.3 s; erase 20 s; no-reply control 0.01 s |

Device-specific retries/error handling also exist. These observations do not
implement a complete bootstrap emulator or establish measured ROM timing.
Remaining work includes actual bootloader version/capabilities, reset/boot-pin
circuitry, reset/chain sequencing, protection/programming failures, and ownership
of custom firmware updates. Linux selects the expected image by device type
through a manifest reference; it is not selected from a returned version string.
No stock image is distributed.

## Presence versus health

These are separate conditions: device discovered, Linux service reachable,
accessory expected by saved configuration, telemetry fresh, subsystem ready,
and fault-free. A successful register reply does not establish all of them.

### Air Manager

The host searches the system D-Bus for `nl.ultimaker.airmanager1` and attempts to
access `flow_rate` before constructing its Air Manager controller. A persisted
preference records that an Air Manager is expected; this distinguishes expected
hardware from a printer that has never been configured with it.

| Signal | Host use / implementation implication |
|---|---|
| `data.timestamp_ms.0` | Advancing timestamp used as heartbeat; a constant reply does not establish liveness |
| `data.filterIsPresent.0` | Filter detection, distinct from accessory connection; integer zero means missing in the inspected consumer |
| `data.TimeCounter.0` | Filter age in seconds; host default lifetime is 1500 hours, with replacement-near threshold at 90% |
| `data.VersionSwBuildTime.0` | Firmware identity property; not the startup flash check |
| `data.fanSpeedMeasured.0` | Reported fan RPM; actual measurement/backend required |
| `data.fanSpeedRatio.0` | Speed/target feedback with off, settling and zero-target sentinels; see value-format notes |
| `data.ambientTemp.0`, `data.exhaustTemp.0` | Environmental telemetry consumed by the service; correct stock sensor locations still need verification |

The normal heartbeat interval is 10 seconds. A failed advance starts up to six
checks spaced 30 seconds apart. The comparison is strictly increasing timestamp;
reset/wrap behavior requires testing. D-Bus property updates feed this check, so
preserving freshness through the monitoring/cache path matters as well as reads.
The slow-check interval alone is about 180 seconds; it is not a guaranteed total
failure-detection deadline because serial/service timeouts also contribute.

On lost response, the inspected host warns and permits an active print to
continue. Outside printing it disables its Air Manager controller, raises a
missing-accessory fault, halts the system and requests heater shutdown. Other
communication-error paths can also invoke fault handling; heartbeat timing is
not the only route to a fault.

Filter status is derived on Linux: missing, peak performance, replacement near,
or replacement required. Counter reset is a state-changing maintenance operation,
not a presence probe. Never report a filter as present without a truthful backend
or an explicitly documented alternative host policy.

### Material Station (MISP; called AMS in the design discussion)

The UMB service publishes the discovered device and starts its configured service.
`nl.ultimaker.MISP1` exposes service-level properties and six bay objects. Service
startup reads/monitors registers and eventually notifies systemd `READY=1`.
That Linux readiness notification is not an accessory wire command or a universal
healthy bit. No equivalent Air Manager-style timestamp heartbeat has been
established for MISP from the inspected consumer paths.

| Signal or group | Status/health role |
|---|---|
| `system_state.STATE.0` | Host simplifies state strings containing CALIBRATE to calibrating, OPERATIONAL to operational, others to error |
| `prefeeder_n.STATE.0`, `.PREV.0`, `.TRANSITION_EVENT.0`, `.filament_direction.0` | Per-bay workflow and transition feedback for n=0..5; commands alone are insufficient |
| `door_sensor.door_opened.0` | Door condition, converted from integer text to boolean |
| `dehumidifier.current_humidity.0`, `.current_temperature.0` | Numeric environment readings |
| `dehumidifier.dehumidifier_state.0` | Numeric state mapped by host to testing, drying, regenerating, operational, error or unknown categories |
| `dehumidifier.hw_error.0` | Integer bitmap; host treats mask 0x01 as hardware-error warning and reports other nonzero bits; full bit meanings remain unresolved |
| `decoupler_left/right.crc_error_counter.0`, `.write_error_counter.0` | Decoupler communication diagnostics; use separate left/right names |
| `decoupler_left/right_storage.error_count.0` | Storage diagnostics; left/right are separate register paths |
| Decoupler gain/offset calibration fields | Host checks calibration and can raise an uncalibrated fault |
| `rewinder.STATE.0`, `.PREV.0`, `.TRANSITION_EVENT.0`, `.current_prefeeder.0` | Rewinder workflow/selection feedback |
| `nfc_controller.tags_visible.0` | NFC tag visibility, not proof of filament mechanically present, loaded or feeding |

The inspected host also implements prolonged-high-humidity warnings with startup
suppression and repeat suppression. Thus not every warning is a direct device
error flag. Neither NFC visibility nor a default D-Bus property should be used to
fabricate readiness when the relevant hardware is absent.

## HTTP and D-Bus reporting

The existing local printer API has `GET /api/v1/airmanager`, including `status`,
`filter_status`, filter ages, firmware version and fan speed. Status schema values
are `available`, `unavailable`, `error`, and `installing_firmware`.

The cluster schema also contains Air Manager and Material Station summaries.
Its Material Station structure has `supported`, `status` (available/unavailable),
and material slots. `supported` describes capability and must not be interpreted
as proof that hardware is physically connected. Coarse HTTP summaries do not
expose every register, D-Bus state or fault. No new standalone Material Station
HTTP route is asserted here.

## Requirements for each independent device

A native STM32 chip has one silicon identity; the two observed profiles expect
different IDs. Use separate controllers with independent startup, reset, firmware
and recovery domains. One carrier PCB may hold both chips, but each remains a
separately discovered UMB device with one configured type and Linux service.

Each controller needs compatible ROM entry/UART access, identity and memory
behavior, firmware-check/update strategy, SRAM reset entry, chain enable/reset,
negotiated address and role-specific registers. The STM32 and its ROM alone do
not provide the entire accessory contract.

The host can replace a mismatched custom image with stock firmware. Resolve
firmware ownership before connecting a custom controller. A fabricated version
or comparison page is not an implemented update strategy. An explicit Linux
adaptation may be needed; no such deployment is currently implemented.

## Coverage and acceptance work

The existing catalog already includes the 13 Air Manager and 82 Material Station
register entries observed in host consumers, including the health fields above.
This review adds their startup/liveness meaning; it does not claim new live
endpoints or an exhaustive accessory register inventory.

Before enabling a replacement, obtain a genuine accessory startup capture,
confirm electrical levels and chain wiring, map both identity configurations,
resolve full programming/entry behavior and firmware-update ownership, and test
service startup with one role before attempting both roles. Then validate stale
telemetry, reboot/timestamp rollover, disconnect, filter removal, stalled fan,
uncalibrated decoupler, dryer faults and missing feeder sensors on a bench with
outputs inhibited. Advance readiness only from real initialized hardware.
