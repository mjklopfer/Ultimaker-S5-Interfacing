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

## Air Manager pinout discussion: reported behavior, unresolved wiring

The [2022 Air Manager / SMB pinout discussion](https://community.ultimaker.com/topic/39588-air-manager-andor-smb-pinout/)
reports a user's experience of chamber temperature being converted through a
static fan-speed table rather than closed-loop chamber regulation. This is a
dated user report, not proof of behavior for every firmware revision. It provides
context for the draft's optional local temperature loop, not a tested integration.

The author asks for a connector pinout and speculates about I2C; the replies do
not supply a verified pinout or establish I2C, CAN, RJ45, voltage levels or
transceiver hardware. Suggestions to use base-fan signals are proposals, not
verified S5 enable interfaces. The source-observed UMB host UART framing and
external electrical-interface uncertainty remain separate findings.

## Linux debug console is separate from UMB

The [UM3 repair discussion, page 2](https://community.ultimaker.com/topic/42861-ultimaker-3-suddenly-no-display-and-unresponsive-button/page/2/)
reports successful Olimex USB-SERIAL-F console access and shows boot/recovery
output. It is useful related-platform troubleshooting evidence, not a verified
S5 R1 recovery procedure, image or external UMB pinout.

[Olimex's adapter specification](https://www.olimex.com/Products/USB-Modules/Interfaces/USB-SERIAL-F/)
states 3.3 V serial output levels. Newer adapters have a separate 5 V supply wire;
that is not the signaling voltage. Cable revisions differ, and the page itself
lists different ground colors in different sections: identify the exact cable
revision and target header before connection, rather than relying on color alone.
Neither the adapter specification nor the UM3 report establishes the external
S5 UMB transceiver voltage. The Linux console, motion link and UMB host UART are
distinct interfaces in the [S5 device map](S5_R1_INTERFACES.md).

The [S3 UMB pinout discussion](https://community.ultimaker.com/topic/38938-s3-umb-out-port-pinouts-data-protocol/)
also asks for interface information without establishing CAN or a verified
connector pin assignment. The photographed Material Station cable has circular
multi-pin ends, not RJ45 Ethernet ends. UART framing observed in Linux does not
by itself identify the external electrical line driver or its voltage.

## S5 R1-specific recovery and serial references

The manufacturer's [S5 R1 firmware-recovery guide](https://um-support-files.ultimaker.com/manuals/repair-calibration/S-Series-Firmware-Recovery/20200625%20Work%20instruction%20S5R1%20Firmware%20Recovery.pdf)
describes microSD imaging and automatic recovery boot for the R1. It is an older
guide referencing firmware 5.7.2, not a verified current-image recommendation.
Recovery erases settings and requires recalibration. The current
[general S-series recovery article](https://support.ultimaker.com/s/article/1877434822572)
explicitly excludes R1 from its supplied recovery images and directs R1 owners to
support for the model-specific precautions. Do not substitute an R2 or UM3 image.

The firsthand [S5-oriented recovery notes](https://gr5.org/unbricking/) include
a console-connection photograph, 115200-baud terminal guidance and boot-script
failure discussion. The [pre-2020 S5 thread](https://community.ultimaker.com/topic/34825-s5-pre-2020-web-server-running-printers-not-accessible-582/)
also discusses console access when network access is unavailable. These are
community observations, not validation of this project's header wiring or restore
procedure. No bare-metal restoration was tested here. Opening the R1 exposes
mains circuitry; follow the manufacturer's model-specific service precautions.

The older [232 Communication thread](https://community.ultimaker.com/topic/11480-232-communication/)
concerns an Ultimaker Original+ and a modified Marlin serial selection at J22.
It is not an S5 pinout or proof of RS-232 voltage levels. On the S5 R1, the saved
device map distinguishes console ttyS0, motion ttyS2 and UMB ttyS1. A possible
internal UART observation point before the external UMB interface is a hypothesis:
pad/header routing, voltage and reset/chain-control requirements remain untraced.
Do not equate header labels with Linux device numbers without tracing them.
