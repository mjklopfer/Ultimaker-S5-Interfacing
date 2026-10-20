# UltiMaker public-source research map

Reviewed 2026-10-19: metadata for 149 public organization repositories, followed
by selected files in relevant projects. This is a bounded review, not a claim
that every source file or branch was examined. Nothing was installed or run on
Cura or the printer. Only authored descriptions and links are published here.

## Cura Live Scripting: useful reference, not the bridge runtime

[CuraLiveScriptingPlugin](https://github.com/Ultimaker/CuraLiveScriptingPlugin/tree/39ca0089e7c0023343ee0984e13f553b2f158819)
demonstrates importing Cura internals, obtaining the global/extruder settings
stacks and reading effective setting values. Its sample also reads print
information and displays messages. This supports the same native-container
approach already used by the bridge; it does not supply a documented HTTP/MCP API.

The inspected `plugin.json` declares SDK 7.0.0; QML imports QtQuick Controls 1.2.
`LiveScripting.py` runs arbitrary Python through `exec` on a background thread,
and can rerun on script edits. It persists a script using a backslash-containing
path. These are compatibility/threading/platform review points, not evidence of
Cura 5.13 compatibility. It has not been installed or tested here. Do not turn
its unrestricted script execution into a remotely exposed bridge endpoint.
Continue building explicit native wrappers with main-thread execution,
exact-action confirmation and observable completion.

## Concrete Cura/Uranium 5.13 wrapper leads

| Open feature | Source inspected at tag 5.13.0 | Useful contract / remaining implementation |
|---|---|---|
| Object movement with undo | [TranslateTool](https://github.com/Ultimaker/Uranium/blob/5.13.0/plugins/Tools/TranslateTool/TranslateTool.py), [TranslateOperation](https://github.com/Ultimaker/Uranium/blob/5.13.0/UM/Operations/TranslateOperation.py), [GroupedOperation](https://github.com/Ultimaker/Uranium/blob/5.13.0/UM/Operations/GroupedOperation.py) | Existing tool pushes undoable operations, groups multi-object moves and preserves selection-relative placement. Need stable scene identities, explicit units/coordinates and stale-selection checks |
| Named machine/core/material/quality/intent selection | [MachineManager](https://github.com/Ultimaker/Cura/blob/5.13.0/cura/Settings/MachineManager.py) | `setActiveMachine`, `setMaterialById`, `setVariantByName`, `setQualityGroupByQualityType`, `setIntentByCategory`; wrappers must resolve valid choices and preserve profile/conflict handling |
| Slice cancellation / lifecycle | [CuraEngineBackend](https://github.com/Ultimaker/Cura/blob/5.13.0/plugins/CuraEngineBackend/CuraEngineBackend.py) | `stopSlicing`, `forceSlice`, lifecycle signals and processing jobs; need operation identity, cancellation state and stale-result protection |
| Local printer selection / upload lifecycle | [LocalClusterOutputDevice](https://github.com/Ultimaker/Cura/blob/5.13.0/plugins/UM3NetworkPrinting/src/Network/LocalClusterOutputDevice.py) | Native target selection, upload progress/completion/error and job-state actions exist; using them is not authorization to bypass printer write confirmations |

These methods were read, not added as MCP endpoints. Additional rotate/scale,
arrangement, per-object settings and multi-plate behavior still need targeted
source review and desktop acceptance tests. The external MCP HTTP 429 issue is
not resolved by this scripting plugin or these internal methods.

## Hardware, NFC and boot leads

| Repository / source | What helps | Boundary |
|---|---|---|
| [um-kernel sun7i](https://github.com/Ultimaker/um-kernel/tree/master/sun7i) | A20-era boot scripts, initramfs and board device trees; use this branch rather than assuming default i.MX8 code describes R1 | Compare installed scripts and selected DTB before asserting exact wiring or boot behavior |
| [UMBus drive-enable fix](https://github.com/Ultimaker/um-kernel/commit/3590ec1a02d6bae1dad8d9ba356ece33f11ddcbd) | Explicit UMB drive-enable line and UART flow-control/pin-mux interaction; patch holds the line high | This patch is for i.MX8MM / Ultimainboard 5, not A20 S5 R1. It does not identify the R1 pad, pinout or electrical standard |
| [oib_testbench](https://github.com/Ultimaker/oib_testbench/tree/a813139284392f247f8f5d6a8cb050444a7780cb) | Older 2005-F interface-board GPIO/loopback map and a comment identifying a level translator on PC23 | Factory fixture actively drives GPIO and ADC registers. Not a passive tool or verified S5 R1 wiring map; do not run on an assembled printer |
| [nfc_test](https://github.com/Ultimaker/nfc_test/tree/560deb709b0241b5e267116a1a69463a5ab47bd2) | Configures `pn532_i2c:/dev/i2c-2`, showing an older direct-Linux NFC test path | Separate from Material Station NFC over UMB. Scripts install persistent tests and change lighting; none were run. Do not adopt old authentication examples |
| [m2m_certificates](https://github.com/Ultimaker/m2m_certificates/tree/8137ad12f508c80d22c5e97dd6916b70a51a48ab) | NFC NDEF M2M certificate parser/generator and ASN.1 definition | Certificate representation is not the complete spool material/usage schema, nor proof of an accessory authentication requirement |
| [UltimakerMarlin S-line](https://github.com/Ultimaker/UltimakerMarlin/tree/S-line) | Existing motion-controller interfaces and print-core EEPROM handlers | Upstream source is not proof of installed binary equivalence; preserve the stock MCU/replacement-controller distinction |
| [ulticontroller_interface_tester](https://github.com/Ultimaker/ulticontroller_interface_tester/tree/000d59e5b74ce246c9af3d3e747e9a583065d3c5) and [framebuffer-vncserver](https://github.com/Ultimaker/framebuffer-vncserver/tree/07401a8ef43325e288d3f8e5cb60bc4e9ace2d8e) | Touch/framebuffer diagnostics and remote display/input implementation references | Not demonstrated S5 live-UI capture: framebuffer may be stale. No test service or VNC listener was installed |

Other candidates for targeted follow-up are `fdm_materials`, `libnfc`, `nfcpy`,
`Ultimaker3` hardware, and platform-specific `linux` branches. Their names alone
do not settle the remaining protocol/electrical questions. No complete Material
Station/Air Manager accessory application source or R1 external UMB pinout was
established by this review.

### Provisioning and the earlier microSD question

The inspected `sun7i/scripts/bootscript.cmd` reads article/revision bytes from
U-Boot I2C device 0x51, offsets 0..7, reconstructs two values and selects device
trees. This is a partial boot-consumer description, not a validated writable
factory provisioning schema or a decoded offset map for the separate full Linux
EEPROM dump.

The inspected `sun7i/initramfs/init.sh` scans MMC partitions for an exact update
filename `um-update.swu` and recognizes a `recovery_data` partition label for
restore mode. The U-Boot source also contains MMC boot-target scanning. These
are reasons not to promise that inserting arbitrary media cannot affect boot.
They must be compared with the installed versions before use.

A deliberately non-bootable, data-only microSD is a plausible Linux storage
option, but successful unchanged boot, detection and mounting were not tested.
It does not automatically enlarge Cura Connect's job spool: the observed spool
is a separate internal eMMC filesystem mounted at `/var/spool/cluster`.
Application-supported relocation or a carefully tested mount migration would be
needed to use another filesystem for jobs. No fstab, boot script, storage layout
or job-storage configuration was changed. A separate removable-card boot test
and recovery plan remain required before relying on it.
