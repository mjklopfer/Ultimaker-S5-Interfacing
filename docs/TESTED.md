# Tested versions and evidence boundaries

| Component | Baseline | What is established |
|---|---|---|
| Cura | 5.13.0 | Windows desktop workflow: settings changes, staged load, slice/export, native Save and both Save As destination cases |
| Bridge | Public source 0.1.6 | Bridge and deployment helpers tested offline; public-build desktop checks pending |
| Printer | UltiMaker S5 R1, firmware 9.0.3.0 | Read-only API/source inspection and printing/recovery research; not every cataloged write tested |
| Node | 20+ required; offline checks on Node 22 | Dependency-free stdio server and mock transport tests |
| Python | 3.10+ recommended | File/archive/transport fixtures and privacy checks; Cura uses bundled Python |
| macOS | Hosted macOS offline CI; deployment guide/helpers provided | Platform launch paths and Keychain code provided; updated live Cura/tunnel installation not verified |
| Linux | Offline server checks | Hosted offline CI; not a supported credential-pairing desktop deployment |
| Arduino | Portable C++11/native + stub sketch tests | No target AVR compile, timing/memory, electrical or accessory interoperability result |

No raw logs, screenshots, printer UUIDs, firmware dumps, backup metadata, project
files, workstation paths or personal test evidence are included. Public test
results contain aggregate outcomes only. Test addresses are loopback; fixture
secrets are deterministic dummy strings and are not working credentials.

The offline suites cover exact-request confirmation, one-use/expiry checks,
busy-printer restrictions, staging symlink boundaries, native save planning and
atomic archive validation. They never require the actual printer. Hardware/native
tests model protocol, calibration and control logic; they do not prove physical IO.

For the reproducible setup, see [platform configurations](PLATFORM_CONFIGURATIONS.md),
[macOS](MACOS.md) and [Windows](WINDOWS.md). Hosted runner tests do not establish
a live Cura GUI install or actual Keychain pairing on either Mac architecture.
