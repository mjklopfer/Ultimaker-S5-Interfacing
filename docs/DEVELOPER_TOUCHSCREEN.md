# Developer-mode touchscreen access

This is an optional, advanced **printer-side SSH/D-Bus procedure**, separate from
the workstation Cura bridge and its 18 MCP tools. Reference: S5 R1,
firmware 9.0.3.0. Qt/Okuda interfaces are firmware-dependent developer internals, not a
supported general touchscreen HTTP API.

| Operation | Evidence |
|---|---|
| Capture the actual Okuda UI through its Qt window | Verified during the reference investigation |
| Read /dev/fb0 as a current touchscreen image | Returned a stale logo; not a reliable live UI capture |
| Select a button using synthesized Qt mouse input | Experimental approach below; **not tested on the printer** |
| Select arbitrary buttons by a stable API name | No general endpoint established |

## Developer access and password

Enable Developer mode using the printer's settings. Use the login information
and **printer-provided SSH password** for that printer/firmware. UltiMaker's
[firmware notes](https://support.ultimaker.com/articles/Knowledge/1667410781982)
state that firmware 9 generates a random SSH password when Developer mode is
enabled. Do not assume an old shared/default password still applies.

Use a trusted LAN. Connect from macOS Terminal or Windows OpenSSH/PowerShell,
replacing both placeholders locally:

```sh
ssh -l SSH_USER PRINTER_HOST
```

Verify the SSH host key using a trusted record and enter the password at SSH's
hidden prompt. Do not put it in a command, URL, script, environment variable or
repository. SSH/developer credentials are separate from HTTP Digest pairing and
the Cura loopback token. The bridge's HTTP credential-store code does not provide
an SSH password cache. No SSH password or account is supplied by this project.

Run the following Python snippets **inside the printer's Linux environment**,
using its existing `dbus` bindings. Calls reach the running printer UI process;
do not run them in the workstation's Cura Python console. The printer UI uses
PyQt5 in this procedure, whereas the Cura 5.13 plugin uses PyQt6.

## Capture the actual touchscreen

Okuda exposes the following developer interface in the reference firmware:

| Item | Value |
|---|---|
| System D-Bus service | nl.ultimaker.okuda |
| Object | /nl/ultimaker/okuda |
| Interface | nl.ultimaker |
| Developer method | debugExecCode |

The method evaluates an expression in the existing UI process. The capture
expression grabs the Qt window, encodes it as PNG in memory and returns base64
plus dimensions. The caller decodes the PNG into a temporary file:

```python
import ast
import base64
from pathlib import Path
import dbus

bus = dbus.SystemBus()
iface = dbus.Interface(
    bus.get_object('nl.ultimaker.okuda', '/nl/ultimaker/okuda'),
    'nl.ultimaker',
)
window_expr = (
    "__import__('PyQt5.QtGui', fromlist=['QGuiApplication'])"
    ".QGuiApplication.allWindows()[0]"
)
capture_expr = (
    "(lambda w: (lambda image, buffer: "
    "(image.save(buffer, 'PNG'), "
    "bytes(buffer.data().toBase64()).decode('ascii'), "
    "w.width(), w.height(), image.width(), image.height()))"
    "(w.grabWindow(), __import__('PyQt5.QtCore', "
    "fromlist=['QBuffer']).QBuffer()))(" + window_expr + ")"
)
saved, encoded, window_w, window_h, image_w, image_h = ast.literal_eval(
    str(iface.debugExecCode(capture_expr, timeout=20))
)
if not saved:
    raise RuntimeError('Qt PNG encoding failed')
png = base64.b64decode(encoded, validate=True)
if not png.startswith(b'\x89PNG\r\n\x1a\n'):
    raise RuntimeError('Unexpected capture format')
Path('/tmp/touchscreen.png').write_bytes(png)
print({'logical_size': [window_w, window_h], 'image_size': [image_w, image_h]})
```

The core Qt capture method was verified; the dimensions are useful for mapping
coordinates. Window selection `[0]` is the reference behavior, not a guarantee
for every firmware or multi-window state. Check the returned image before use.

After exiting the SSH shell, retrieve the image from the workstation:

```sh
scp SSH_USER@PRINTER_HOST:/tmp/touchscreen.png local_captures/touchscreen.png
```

Create `local_captures` first (`mkdir -p local_captures` on macOS, or
`New-Item -ItemType Directory -Force local_captures` in PowerShell). View the
result locally. Images may contain job/operator text; the capture folder is
ignored by Git. Captures are not automatically redacted.

The chamber-camera snapshot API is a different image source. Likewise,
`/system/display_message` changes a message; it is not a screenshot getter.
`/dev/fb0` may not mirror the Qt compositor, so framebuffer/VNC assumptions need
independent verification. No VNC server is required by the Qt capture procedure.

## Experimental button selection

**Not tested on S5 hardware. Do not treat this as a verified button-control
feature.** Qt Test supports a mouse click addressed to a `QWindow`; this suggests
a developer technique for controls that accept mouse input. It requires the
printer's PyQt5 QtTest module, correct logical coordinates and the same current
window/layout. Some touchscreen-only controls may ignore synthesized mouse input.
No firmware modification or QtTest installation is prescribed here.

For an authorized idle-system bench test, take and inspect a fresh screenshot,
identify the intended button, then adapt the following in the same printer-side
Python session. It sends one click only after explicit typed confirmation:

```python
# Requires bus, iface and window_expr from the capture example above.
width, height = ast.literal_eval(str(iface.debugExecCode(
    '(lambda w: (w.width(), w.height()))(' + window_expr + ')', timeout=10
)))
x = int(input('Logical x coordinate: '))
y = int(input('Logical y coordinate: '))
if not (0 <= x < width and 0 <= y < height):
    raise ValueError('Coordinate outside the current window')
if input('Type SEND ONE CLICK to continue: ') != 'SEND ONE CLICK':
    raise SystemExit('No input sent')
click_expr = (
    "(lambda w, core, test: test.QTest.mouseClick("
    "w, core.Qt.LeftButton, core.Qt.NoModifier, "
    f"core.QPoint({x}, {y})))(" + window_expr + ", "
    "__import__('PyQt5.QtCore', fromlist=['Qt', 'QPoint']), "
    "__import__('PyQt5.QtTest', fromlist=['QTest']))"
)
iface.debugExecCode(click_expr, timeout=10)
# Capture again and inspect the actual result; a return value does not prove selection.
```

If screenshot pixels and logical window dimensions differ, convert using
`x_logical = x_image * window_w / image_w` and the corresponding height ratio.
Account for cropping/rotation and confirm the actual layout; do not reuse fixed
coordinates blindly. There is no binding here between screenshot content and a
later click, so an intervening dialog or UI change can invalidate the target.

`debugExecCode` is general code evaluation, not an intrinsically read-only
endpoint. Input injection can dismiss warnings or start/abort operations and
bypasses the MCP server's confirmation/busy-state guards. Do not use it to bypass
printer interlocks. Prefer documented printer APIs for supported actions. Do not
test clicks on an active job; this project has not done so. Disable Developer
mode when no longer needed according to your operating policy.

Qt reference: [Qt Test mouse input](https://doc.qt.io/qt-6/qtest.html) and the
[Qt 5.15 QWindow mouse-click interface](https://github.com/qt/qtbase/blob/5.15/src/testlib/qtestmouse.h).
The reference links describe Qt behavior, not an S5 compatibility certification.
