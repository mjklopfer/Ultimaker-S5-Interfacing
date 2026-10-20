# Utilimaker S5 Interfacing

A local MCP platform for the **UltiMaker S5** and **Cura**, with a loopback Cura
plugin, a dependency-free Node stdio MCP server, guarded printer operations, and
S5 R1 hardware/protocol research. Independent community project; not affiliated
with or supported by UltiMaker.

## What it provides

- Inspect Cura's machine, extruders, settings, scene and slicer state.
- Load models/projects, change settings, request slicing and export G-code.
- Save a native full-workspace 3MF project: Save, Save As with a new filename,
  Save As in another folder, and asynchronous completion/status.
- Inspect a catalog of **130 local API paths / 161 HTTP operations**, including
  queue/status, temperatures, materials, diagnostics and system configuration.
- Read bounded printer endpoints and perform explicitly confirmed writes through
  the catalog. Upload and start are separate actions; uploading may still trigger
  the printer's own queue policy when idle.
- Review original S5 R1 PCB/serial/GPIO notes and a disabled-by-default Arduino
  UMB accessory-controller draft.

No printer address, account, credential, serial number, wireless network, job,
device image or private workspace history is shipped. Set the printer origin
explicitly; there is no built-in printer host. Job uploads use a generic owner
label rather than the workstation hostname.

```text
MCP client --stdio--> Node MCP server --loopback token--> Cura plugin --> Cura
                              |
                              +--configured LAN HTTP API--> S5
```

## Start here

1. Read [deployment](docs/DEPLOYMENT.md) and install the plugin while Cura is closed.
2. Set `CURA_PRINTER_BASE_URL`, the staging folder and connection-file path.
3. Start `node src/server.mjs` through your MCP client's stdio configuration.
4. Begin with `cura_status` and `printer_api_catalog`. Writes require exact-action
   authorization and a matching short-lived confirmation token.

See the [18-tool reference](docs/TOOLS.md), [tested versions](docs/TESTED.md),
[known shortcomings and TODOs](docs/KNOWN_ISSUES.md), and [security/privacy](SECURITY.md).
Hardware notes start at [S5 R1 interfaces](hardware/S5_R1_INTERFACES.md);
the [UMB controller](hardware/umb-controller/README.md) is a separate offline draft.

## Requirements and checks

- Cura **5.13.0** is the tested base; other versions are not established compatible.
- Node.js 20+ and Python 3.10+; Cura supplies its own Qt/Python plugin runtime.
- macOS Keychain or Windows Credential Manager for printer Digest pairing.
- A C++11 compiler is needed only for the optional offline controller tests.

From the repository root:

```sh
node --test
python -m unittest discover -s tests -p 'test_*.py'
python scripts/privacy_check.py
```

From `hardware/umb-controller`, run `python tools/run_tests.py` for native/stub
controller checks. These tests do not connect to a real printer. Never treat
offline tests, an accepted request or a sliced file as proof of a successful print.

## Release and attribution

Public source release **0.1.5** derives from a Windows-verified 0.1.4 bridge and
adds publication privacy/configuration changes. It starts a new Git history.
See [changelog](CHANGELOG.md), [sanitization policy](docs/SANITIZATION.md),
[source references](hardware/SOURCES.md), [notices](NOTICE.md) and [MIT license](LICENSE).
Vendor firmware, recovery images, service source dumps, raw device captures,
printed models and proprietary schematics are not redistributed.
