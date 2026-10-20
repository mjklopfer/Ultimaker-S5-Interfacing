# S5 R1 Linux and hardware connectivity

General operational descriptions from an S5 R1 / firmware 9.0.3 investigation.
These are reusable interface observations, not the identity or raw configuration
of any particular printer. No vendor implementation source or binary is included.
Firmware/kernel revisions can change names and allocations.

## Processor split

| Subsystem | General role | Confidence |
|---|---|---|
| Olimex A20-OLinuXino-LIME2 / Allwinner A20 | Linux application, UI, networking, configuration, jobs and accessory coordination | Model/configuration observed |
| ATmega2560 | Real-time motion, heater control, temperature/sensor telemetry and printer IO | Controller family confirmed during prior research |
| Air Manager accessory MCU | Fan/airflow actuation behind accessory registers | Host-side contract observed; fitted accessory hardware not validated |
| Material Station accessory MCU | Feeder/rewinder/decoupler, environmental/dryer and NFC state machines | Host-side contract observed; full accessory implementation not recovered |

The AVR does more than motion. General Marlin-facing functions include M104 hotend
target, M140 bed target, M301 PID configuration, M105 temperature telemetry and
M106 material-cooling demand. The head's material-cooling fan is separate from
the Air Manager path. This document is descriptive and does not instruct running
those commands on a live printer.

## Generic Linux structure

| Location/service | Purpose |
|---|---|
| /usr/share/griffin/griffin | Main application, printer policy, drivers and accessory-facing services |
| /usr/share/umbus | Accessory bus service and operational protocol support |
| /usr/lib/python3/dist-packages/ucFirmwareUpgrade | Controller upgrade/bootloader support |
| /dev | Kernel devices and logical GPIO aliases |
| /sys | Device/driver/GPIO metadata; paths are kernel-version dependent |
| /proc | Kernel/runtime metadata |
| griffin.printer.service | Normal owner of the AVR operational transport |
| umbus.service | Accessory transport ownership and initialization |
| okuda.touchui@0.service | Touchscreen/UI |
| mjpg-streamer@0.service | Camera stream service |

Service/module names describe operational structure; none of the implementations
are distributed here. Presence of a device node or an open service does not prove
an accessory is fitted, a connector is electrically compatible, or a port is free.
Do not open a second master on a UART owned by a running service.

## Serial and peripheral mapping

| Device | Observed configuration/use | Boundary |
|---|---|---|
| /dev/ttyS2 | AVR operational Marlin link, 250000 baud, 8N1 | Model configuration overrides matter; bootloader traffic is a different protocol |
| /dev/ttyS1 | UMB accessory link, 115200 baud, 8E1 | Serial framing does not establish RS-232/RS-485/TTL voltage or pinout |
| /dev/ttyS0 | Linux/U-Boot console, boot arguments use 115200 baud | Physical header position/electricals not confirmed |
| /dev/i2c-2 | Linux NFC reader configuration | No active bus scan is needed to describe the configured role |
| /sys/bus/i2c/devices/1-0050/eeprom | at24/24c16, 2048-byte EEPROM interface | Field layout and device-specific contents excluded |
| /dev/video0 | UVC camera | Hardware product class only; no device IDs/images included |
| /dev/dri/card0, /dev/fb0 | Display/framebuffer | A framebuffer read can be a stale boot image rather than the current UI |
| /dev/input/event* | Touchscreen, display remote input, power key and camera controls | Event numbering can change |
| /dev/snd/pcmC0D0p | Allwinner analog codec PCM playback | Existence does not prove audible speaker routing |

Hardware SPI was driver-bound without a general-purpose spidev node. No exported
Linux PWM channel was observed; that does not establish that the SoC lacks PWM.
USB/HDMI support front-panel/display functions. Storage is eMMC plus removable
media support; storage identifiers, partitions' unique IDs and contents are omitted.

## GPIO aliases observed for AVR ISP/reset

| Alias | Legacy sysfs GPIO number | Function |
|---|---|---|
| /dev/gpio/avr_sck | 84 | ISP clock |
| /dev/gpio/avr_mosi | 85 | ISP data to AVR |
| /dev/gpio/avr_miso | 86 | ISP data from AVR |
| /dev/gpio/avr_reset | 87 | Active-low reset |

These are logical Linux aliases/numbers, not Arduino pins, connector positions,
package-pad numbers or voltage specifications. Generic sysfs paths are
`/sys/class/gpio/gpioNUMBER/value`. Verify aliases and resolved paths on the target
system. GPIO renumbering and symlinks matter. Driving/resetting these lines can
interrupt the controller; the public MCP tools do not expose GPIO programming.

## PCB/connector context

Page 10 of the [R1 repair manual](https://um-support-files.ultimaker.com/manuals/repair-calibration/S-series/UMS5R1%20-%20Electronics.pdf)
provides additional photographic trace targets: `J28` is labeled `UMBus` and
neighboring `J13` is labeled `NFC`. `U9` is near the UMB connector; its identity
and connections are not established by this photo. Internal labels include
`A_UART0`, `A_UART2`, `A_UART3`, `OLI_CAN`, `OLI_IR` and `OLI_UEXT` on headers or
footprints. Population varies. These labels do not prove software ownership,
voltage, spare availability, connector pin order or a CAN implementation of UMB.
Use them to plan power-isolated continuity/component identification, not wiring.

The manufacturer's repair reference identifies connections for the heated bed,
PT100 sensor, motion/extrusion motors, endstops, filament flow, printhead, system
fans, lighting, speaker and Olimex display/USB/network functions. It locates the
speaker connector on the carrier board. Its location alone does not identify
which processor generates the audio signal. Use the original linked reference
for board orientation; no proprietary drawings are copied here.

Linux exposes an enabled analog codec/playback path. Prior software inspection
and a related older board drawing favor an analog path, but exact R1 continuity
and audible routing remain unresolved. No general-purpose AVR tone command was
established. Do not present the absence of a found handler as proof of no circuit.

The actual Qt/Okuda touchscreen can be captured through its developer D-Bus
interface; raw framebuffer reads may be stale. See the [developer-mode procedure](../docs/DEVELOPER_TOUCHSCREEN.md)
for SSH access, image retrieval and the untested Qt input approach.

The R1 base electronics include 24 V power/system-fan connections. That fact does
not establish the external Air Manager connector pinout, fan model or PWM/tach
electrical levels. Inspect the actual accessory before choosing a driver.

The base contains exposed mains/power circuitry when opened. Board inspection
requires power isolation and the manufacturer's repair precautions. This is not
a construction-ready schematic or a replacement for qualified repair guidance.

## Recovery research boundary

See [miscellaneous service notes](MISC_NOTES.md) for print-core EEPROM identity,
Cura nozzle settings and the applicability limits of older UM2 board drawings.

The Linux storage and AVR program/EEPROM are separate recovery domains. eMMC user
area/boot regions, board EEPROM, MCU flash/EEPROM/fuses/lock state and compatible
boot media must be considered separately. Capturing files is not proof of a
bare-metal restore. No device images, readbacks, identity data, recovery-specific
credentials or flashing scripts are part of this public project. Maintenance-SD
boot and full restoration were not validated. See [sources](SOURCES.md).
