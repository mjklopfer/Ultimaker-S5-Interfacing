# UMB operational protocol draft

Source: `/usr/share/umbus/umbus/protocol/umbus.py` and `crc8.py` installed on S5 R1 firmware 9.0.3. This describes the Linux side of an operational link. It does not establish external connector signaling or complete boot compatibility.

## Frames

UART framing: 115200 baud, eight data bits, even parity, one stop bit. Requests:

```text
FF | address | command | N | N payload bytes | CRC8
```

CRC covers address through payload, excluding FF. CRC8 parameters: width 8, polynomial 0x07, initial zero, MSB first, no final XOR. The known check string `123456789` gives F4.

Replies:

```text
FF | command/status | N | N payload bytes | CRC8
```

Reply CRC covers command/status through payload. Replies have **no address or sequence number**. Use one outstanding request globally on the wire. After a timeout or corrupted response, drain stale data and re-establish a measured idle boundary before another transaction; do not confuse a delayed reply from a previous address with the next request. Automatic retries of state-changing commands are not implemented because their outcome can be ambiguous.

The payload length is one byte, maximum 255. A request totals at most 260 bytes; a response 259. A raw FF can appear inside a length-delimited payload. The C++ parser resets on explicit interbyte timeout at the sketch layer; it does not restart a frame on each FF found inside a payload.

## Commands

| Byte | Request payload | Reply payload |
|---|---|---|
| 00 next register | Empty for first; otherwise current two-byte index | Next two-byte index, 0000 at end |
| 01 name | Two-byte index | ASCII name |
| 02 read | Two-byte index | ASCII value |
| 03 write | See below | Success payload not interpreted by source; draft returns empty |
| 10 monitor enable | Two-byte index | Draft returns empty |
| 11 monitor disable | Two-byte index | Draft returns empty |
| 1F poll | Empty | Zero or more index/value records |

Error responses use response code FE. Installed constants describe FE unknown command and FD bad payload; the draft conservatively returns FD for refused/unavailable operations as well. It does not invent stock-specific diagnostic error numbers. Exact accessory write acknowledgments and application error conventions remain to be captured.

Write payload:

```text
L | ASCII value | 00 | index_byte_0 | index_byte_1
```

`L = number of ASCII bytes + 1`, including NUL. Example value `48` plus opaque index bytes `12 34`:

```text
03 34 38 00 12 34
```

Maximum value string is 251 bytes after overhead. Register names and values are ASCII. Preserve discovered index bytes exactly; the stock index's numeric byte order is not assumed. The replacement server's local indices are explicitly chosen as ordinal+1, high byte then low byte. They are not known original device addresses.

## Monitoring ambiguity

The preserved Python source parses the monitor record terminator using the **four literal ASCII bytes** backslash,x,0,0 (`b'\\x00'`), whereas register writes append an actual zero byte. No real accessory capture exists to settle whether monitoring uses that literal delimiter or the host has a parser defect. The draft implements both separators and tests both. The disabled bench sketch uses NUL as a hypothesis; a validated stock integration must select the correct separator explicitly.

Each draft monitor record is two index bytes, ASCII value, selected separator. Whole records are packed into the 255-byte payload with a cursor to avoid splitting records or starving later registers. Values too large for a single record are omitted and remain readable with 02. The draft sends current monitored values on polling, rather than implementing changed-only caching. It must be measured for host compatibility, traffic and keepalive timing.

## Profiles and access

`endpoint_catalog.json` contains 13 Air Manager and 82 Material Station entries referenced in the inspected host source, with source locations. It is **not an exhaustive firmware register inventory**. Firmware-string-only Air Manager names (`fanSpeedTarget`, `fanAirflowMeasured`, `fanCurrentMeasured`) are documented as candidates without guessed paths or permissions and are not compiled into the register table.

The generic server dispatches every catalog entry to the hardware backend. Only source-observed writes are allowed by the profile, and global writes start disabled. Stock fields not supplied by a backend return unavailable. Read-only custom sensor fields cannot become actuators through a generic register write.

Source `led_driver/led_pwm_output.n` is preserved literally because it is how the Linux consumer names its proxy. Dot-to-slash D-Bus mapping makes the exact original wire name ambiguous; validate through enumeration before treating the spelling as definitive. Dynamic configuration-driven fields may exist beyond the catalog.

## Material Station commands

These numbers are **register values** written to `prefeeder_n.printer_command.0`, not top-level UMB opcodes:

| Value | Action |
|---|---|
| 1 | LOAD |
| 2 | UNLOAD |
| 3 | EJECT |
| 4 | PAUSE |
| 5 | RESUME |
| 6 | END_OF_FILAMENT_RESET |
| 7 | PARK |
| 8 | RECOVER_ERROR |
| 9 | EXPECT_RETRACT |
| 10 | LOAD_TO_PRINTHEAD |
| 11 | ERROR |
| 12 | BREAK_FAILED_ASSIST |

Slot state strings and transition reason numbers come from `mispSlot.py` in the evidence. The application must preserve command acknowledgment versus completion as separate concepts and report transitions based on physical feedback.

## NFC over Material Station registers

The saved host NFC wrapper uses the same operational UMB register transport,
not a separate top-level NFC packet opcode. The following describes source-observed
host expectations; no live tag transaction or accessory acceptance is validated.

The integer written to `nfc_controller.command.0` packs:

```text
command_value = (page << 16) | (bay << 8) | operation
```

| Bits | Meaning |
|---|---|
| 23..16 | Page/address field, subject to the read/write caveat below |
| 15..8 | Bay 0..5, corresponding to A..F |
| 7..0 | Operation |

| Operation | Value |
|---|---|
| NOP / completion indication | 0 |
| SCAN_ONCE | 1 |
| SCAN_FOREVER | 2 |
| READ | 3 |
| WRITE | 4 |
| SCAN_FOREVER_SINGLE_POSITION | 5 |
| RF regulation test / selected antenna | 6 |

For example, READ page 2, bay B gives `(2 << 16) | (1 << 8) | 3`,
hexadecimal `0x020103`, decimal `131331`. The outer UMB command is register write
`03`; its value string is ASCII `131331`, not three raw packed bytes. Its payload
is `07 | ASCII 131331 | 00 | discovered index byte 0 | discovered index byte 1`.
The register-value string length includes its terminating NUL. No fixed original
register index or accessory address is supplied by this example.

| Register | Source-observed role |
|---|---|
| `nfc_controller.command.0` | Packed request; return to zero wakes the host completion event |
| `nfc_controller.tags_visible.0` | Visibility bitmask; host checks bit 0 for bay A through bit 5 for F |
| `nfc_controller.single_position_parameter.0` | Bay selection for single-position scanning/test operations |
| `nfc_controller.sector_data.0` through `.3` | Four unsigned 32-bit values representing a 16-byte transfer |

The numeric values use the ordinary ASCII register representation. For each data
word, byte conversion is little-endian. For example, value `67305985`
(`0x04030201`) represents tag bytes `01 02 03 04`.

The Linux service enables monitoring for all four data words and the command
register, watches the visibility mask, then requests an initial scan. A read
issues the packed command, waits for completion and gathers the four data words.
A write stages the four words first, then issues WRITE and waits. The wrapper
serializes access with a lock because these are shared staging registers.
Visibility does not establish mechanical filament presence or successful feeding.

### Addressing, timeout and tag-format boundaries

The read wrapper calls a page 16 bytes and increments its page argument once per
16-byte block. The write wrapper derives its address field as
`start_byte_offset // 4 + block_index`; the upper adapter also treats read and
write offsets differently. Do not normalize these into a supposedly verified
common address unit without real captures and NFC-controller evidence.

The saved wrapper waits for a command-completion event but does not check the
wait return value before collecting data or returning write success. Consequently
its return value alone is not proof of successful transfer or persistent storage.
Multi-block loops use integer division by 16; partial-block semantics are not
validated. Real completion/error sequencing, stale-data protection and monitoring
delimiter behavior still need verification.

This establishes a host-side transfer wrapper, not the complete spool-record
schema, tag authentication/integrity rules, RF protocol, antenna electronics or
an implemented STM32 NFC backend. Do not acknowledge persistent tag writes
without real hardware behavior and appropriate error handling.

## Proposed environmental extension (implemented as read-only fields)

| Name | Index range | Units/meaning |
|---|---|---|
| custom.chamberTemperature.n | 0..3 | Celsius |
| custom.chamberHumidity.n | 0..3 | Relative humidity percent |
| custom.materialTemperature.0 | 0 | Celsius |
| custom.materialHumidity.0 | 0 | Relative humidity percent |
| custom.sensorValid.n | 0..4 | 1 only when valid and fresh |
| custom.sensorAgeMs.n | 0..4 | Age since last successful measurement; FFFFFFFF decimal when invalid |

Invalid/stale temperature and humidity reads return an error instead of a plausible zero. These names are proposed by this project, not stock UltiMaker endpoints. They are implemented in both bench profiles; consumers must identify role/path to avoid double-counting the same physical probes.

## Explicit exclusions

No UART electrical adapter, RS-232/TTL/RS-485 assumption, bootstrap enumerator, reset/firmware upgrade writer, actual S5 device acceptance, GPIO output driver or printer mechanical procedure is implemented. The stock host may reset/reflash an unexpected device during startup; operational compatibility alone is not a reason to connect either STM32 controller directly to UMB.
