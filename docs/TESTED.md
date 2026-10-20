# Tested versions and evidence boundaries

| Component | Baseline | What is established |
|---|---|---|
| Cura | 5.13.0 | Earlier Windows bridge: settings changes, staged load, slice/export, native Save and both Save As destination cases |
| Bridge | Private baseline 0.1.4; public source 0.1.5 | Public configuration/privacy changes tested offline; desktop public-build checks pending |
| Printer | UltiMaker S5 R1, firmware 9.0.3 family | Earlier read-only API/source inspection and separately authorized printing/recovery research; not every cataloged write tested |
| Node | 20+ required; offline checks on Node 22 | Dependency-free stdio server and mock transport tests |
| Python | 3.10+ recommended | File/archive/transport fixtures and privacy checks; Cura uses bundled Python |
| macOS | Deployment package prepared | Platform launch paths and Keychain code provided; updated live Cura/tunnel installation not verified |
| Linux | Offline server checks | Mock Node/Python tests; not a supported credential-pairing desktop deployment |
| Arduino | Portable C++11/native + stub sketch tests | No target AVR compile, timing/memory, electrical or accessory interoperability result |

No raw logs, screenshots, printer UUIDs, firmware dumps, backup metadata, project
files, workstation paths or personal test evidence are included. Public test
results contain aggregate outcomes only. Test addresses are loopback; fixture
secrets are deterministic dummy strings and are not working credentials.

The offline suites cover exact-request confirmation, one-use/expiry checks,
busy-printer restrictions, staging symlink boundaries, native save planning and
atomic archive validation. They never require the actual printer. Hardware/native
tests model protocol, calibration and control logic; they do not prove physical IO.
