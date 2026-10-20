# Miscellaneous hardware and service notes

These are research notes, with evidence and unresolved boundaries stated per
topic. They are not additional implemented MCP tools or validated repair procedures.

## Print-core identity versus Cura nozzle settings

Two configurations need to agree with the physical nozzle:

| Configuration | Where it lives | What changing it does |
|---|---|---|
| Core type and nozzle diameter used for slicing | Cura machine/extruder variant and associated profiles | Changes the slicing configuration; does not rewrite the core |
| Core identity reported to the printer | EEPROM on the removable print core | Supplies the detected core type/nozzle size; does not change the physical nozzle or create suitable Cura profiles |

The manufacturer's [print-core overview](https://support.ultimaker.com/articles/Knowledge/000002903)
identifies the EEPROM as storing core type, nozzle size and printing hours. Its
[S-series exchange procedure](https://support.ultimaker.com/articles/Knowledge/1667411590923)
states that a replacement core is detected automatically. For a normal complete
core exchange, use the printer's guided procedure and match Cura's configuration.
A same-diameter nozzle replacement alone does not normally call for a diameter
identity change. UltiMaker's supported approach is exchanging the complete core;
changing only the nozzle is outside that documented support workflow.

For a custom nozzle-size conversion, the slicer must reflect the actual diameter.
Ideally the reported identity also remains truthful, but changing EEPROM bytes
alone does not establish material compatibility, thermal limits, calibration or
reliable extrusion. We have not decoded and validated a core-identity editing
procedure or tested a modified core.

### Upstream service commands found

The public [UltiMaker Marlin S-line source](https://github.com/Ultimaker/UltimakerMarlin/blob/S-line/Marlin/Marlin_main.cpp)
contains these handlers. They describe that source branch, not verified support
in the installed motion-controller binary:

| Command | Source-observed operation | Parameters / boundary |
|---|---|---|
| `M149` | Read hotend serial identifier | `T` selects tool 0 or 1; identity output should remain private |
| `M150` | Read a raw core EEPROM page as hexadecimal | `T` selects tool; `P` selects page 0 through 3 |
| `M151` | Write an eight-byte raw core EEPROM chunk | Explicit `T`, address `A`, and `D` containing 16 hexadecimal characters; no validated identity-field offsets or replacement payload are provided here |

These handlers were inspected, not executed. No EEPROM write was performed.
Before considering an edit, preserve the original contents privately, establish
the exact field layout and validation requirements, and verify the actual
firmware implementation and recovery path. Do not open a competing serial client
on the Linux service-owned motion UART.

The reviewed local HTTP catalog exposes hotend identity through GET at
`/api/v1/printer/heads/{head_id}/extruders/{extruder_id}/hotend`; no identity setter
was found there. Temperature target writes are a separate operation. Developer
SSH access does not turn raw EEPROM writes into a supported nozzle-size API.

## Ultimainboard v2.1.4 reference: Ultimaker 2 hardware

The [community documentation announcement](https://community.ultimaker.com/topic/21733-ultimainboard-v214-some-documentation-schematics-pinout-dimensions-step-3d-bom/)
describes derived schematics, pinout, dimensions, STEP and BOM outputs based on
the Ultimaker 2 repository. The official
[1546 Ultimainboard v2.1.4 directory](https://github.com/Ultimaker/Ultimaker2/tree/master/1546%20ultimainboard%20V2.1.4)
was checked and contains Altium project/PCB files and schematic sheets
`schema1.SchDoc` through `schema5.SchDoc`, plus a revisions sheet. The community
attachment set has not been independently validated in this investigation.

This is a related older board reference, not an S5 R1 schematic. Do not transfer
its connector numbers, pin assignments, power routing or spare-I/O claims to the
S5. It does not establish the S5's UMB electrical interface. The discussion also
illustrates why a firmware pin number, MCU port name and physical package pin
must be distinguished when tracing a circuit.

For S5-specific observations, use [S5 R1 interfaces](S5_R1_INTERFACES.md) and the
linked R1 repair manual. Exact UMB pinout/transceiver identification and physical
continuity checks remain pending. Only links and authored descriptions are
included here; no manufacturer source files or schematics are redistributed.
