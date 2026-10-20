# Developer SSH access and capabilities

Developer-mode SSH provides an authenticated shell on the **printer's Linux
board**. It is an optional troubleshooting/engineering channel, distinct from
both Cura automation on the workstation and the printer's HTTP API. Available
commands and permissions depend on the firmware and the authorized login.

Reference platform: S5 R1, firmware 9.0.3.0. Use the printer-provided password
and the firmware's developer login instructions. See [developer connection and
screen access](DEVELOPER_TOUCHSCREEN.md#developer-access-and-password) for SSH
placeholders, host-key verification and password handling.

## What access enables

| Capability | Available information or operation | Evidence / limits |
|---|---|---|
| Remote Linux shell | Run installed system tools and original inspection scripts | Developer SSH connection established in the reference investigation; permissions still apply |
| Service inspection | Check printer, accessory-bus, touchscreen and camera service state | Verified inspection; a running service does not establish subsystem health |
| Logs and configuration | Inspect local diagnostics and installed configuration; retrieve selected files with SCP | Verified file access; contents may include confidential network/operator details |
| Kernel/device inventory | Inspect /dev, /proc and /sys for serial, GPIO, I2C, display, camera, audio and storage mappings | Verified metadata access; presence is not electrical availability or safe ownership |
| System D-Bus inspection | Enumerate services/objects and query supported properties/methods | Verified; service names and interfaces can vary with firmware |
| Fault diagnosis | Query the printer's fault service for details beyond a general HTTP status | Verified fault query; not every touchscreen message is a user-set display message |
| Actual touchscreen capture | Ask the running Okuda/Qt window for a PNG and retrieve it | Verified capture method; raw framebuffer reads may show stale content |
| Touchscreen button input | Possible Qt-based mouse event injection through the developer UI interface | **Experimental, not tested on the printer**, not a stable named-button API |
| Accessory protocol research | Inspect the Linux-side UMB consumer/register interface and service ownership | Host-side observations; not proof of a connected accessory or its electrical layer |
| Audio inspection | Discover the Linux ALSA codec/PCM device and routing metadata | Device/configuration observed; physical speaker routing and audibility unresolved |
| Backup/maintenance work | Access storage and model-specific controller interfaces with suitable tools/permissions | Separate maintenance workflow; complete restoration is unvalidated and not supplied by this MCP platform |

SSH access does not itself create reliable fan, material-feeding, motor or UI
automation. Those functions still need validated interfaces, state checks and
appropriate permissions. It also does not establish the external UMB connector's
voltage, signaling standard or pinout.

## Three separate control paths

| Path | Where it operates | Typical purpose |
|---|---|---|
| MCP stdio + loopback Cura plugin | Workstation | Model/project/settings/slice/export and native project saves |
| Documented printer HTTP APIs | Printer application services over the LAN | Status, jobs, materials and authorized cataloged controls |
| Developer SSH + local Linux/D-Bus | Printer Linux board and its services | Inspection, troubleshooting, actual printer-screen capture and advanced engineering |

The repository's **18 MCP tools do not include an SSH shell or arbitrary D-Bus
executor**. These are documented manual developer workflows, not additional
implemented MCP endpoints. HTTP pairing keys, the Cura loopback token and the
developer SSH password are separate credentials; one does not authenticate the
other. No automatic SSH login, password cache or general remote-command proxy
is provided by the bridge.

## Read-only starting points

After establishing the SSH session, these commands inspect the reference Linux
environment without intentionally changing printer configuration:

```sh
uname -sr
systemctl is-active griffin.printer.service umbus.service okuda.touchui@0.service
ls -l /dev/ttyS0 /dev/ttyS1 /dev/ttyS2
busctl --no-pager tree nl.ultimaker.UMBus1
busctl --no-pager introspect nl.ultimaker.Marvin1 /nl/ultimaker/Marvin1
busctl --no-pager call nl.ultimaker.Marvin1 /nl/ultimaker/Marvin1 nl.ultimaker.Marvin1 getAllFaults
```

These are reference service/device names, not discovery results for every S5.
Inspect a method's signature before calling it; an arbitrary D-Bus method need
not be read-only. An empty UMB tree does not prove physical/electrical absence,
and an overall HTTP status may not explain the detailed fault state.

Retrieve selected files with SCP using locally supplied SSH account/host values.
Keep diagnostic output and screenshots local unless reviewed/redacted; do not
include password-bearing configuration files or full device images in issues.

## Maintenance and control boundaries

Service stop/restart, process termination, GPIO writes, AVR reset/programming,
serial traffic and UI input can disrupt a print even though SSH authentication
succeeds. Developer shell commands are **outside the MCP confirmation and
busy-printer guards**. Do not interpret shell access as permission to bypass
thermal protections, interlocks or normal application ownership.

The printer application owns the AVR operational UART and the UMB daemon owns
the accessory UART. Opening a second writer on either port can corrupt ongoing
communication. Device metadata inspection is different from sending bytes or
driving a GPIO. Controller backup/readback may require a reset and exclusive
transport access; storage consistency and a tested restore path are separate
requirements. No claim of a turnkey bare-metal restore follows from SSH access.

Use documented HTTP controls when they cover the task. Reserve intrusive work
for an explicitly authorized maintenance window, and distinguish command
acceptance from verified physical results.

## Related documentation

- [Touchscreen capture and experimental input](DEVELOPER_TOUCHSCREEN.md)
- [S5 R1 Linux, serial and GPIO mappings](../hardware/S5_R1_INTERFACES.md)
- [Accessory interfaces](../hardware/ACCESSORIES.md) and [Air Manager values](../hardware/AIR_MANAGER_VALUES.md)
- [MCP tool reference](TOOLS.md), [tested versions](TESTED.md) and [known limitations](KNOWN_ISSUES.md)
