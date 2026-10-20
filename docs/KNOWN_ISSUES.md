# Known shortcomings and TODO

## Cura bridge

- Only Cura 5.13.0 has a live desktop baseline. Public privacy/configuration changes
  have offline coverage; a fresh public-build desktop check is still required.
- Native 3MF machine/material/settings conflict resolution can require Cura's UI.
- Current-project path tracking is reliable for bridge loads/saves; a native UI
  project open may clear the known path. Use explicit Save As rather than guessing.
- Scene inspection lacks stable object IDs, detailed transforms, bounds and units.
- Move/rotate/scale/mirror/lay-flat, grouping/arrangement, undo/redo, per-object
  settings/extruder assignment, and multiple-plate workflows need native wrappers.
- Named material/core/nozzle/quality/intent/profile selection and machine/network
  printer selection need wrappers. Numeric effective-setting edits are available.
- Detailed slice progress, cancellation, validation errors and stale-result identity
  are not exposed as complete workflows. Successful slicing is not a physical test.
- Exports beyond G-code/native project save need native writer wrappers.
- Save jobs should be observed until completion; workspace edits during saving are
  unsupported. Request retry after a timeout requires inspecting current state.

## Printer API

- Catalog inclusion does not prove firmware support, permission or safe execution.
  Firmware-specific behavior and many hazardous writes have not been exercised.
- The URL must be configured locally. No network discovery or automatic host is
  shipped. Printer HTTP may be cleartext; use a trusted LAN and secure local files.
- Secure Digest credential storage exists on Windows/macOS, not Linux.
- No automatic stale pairing cleanup or comprehensive reconnect UI is supplied.
- Camera streams and active diagnostic sampling are intentionally restricted.
- Cloud/team/registration routes found in shared web code are not exposed as local
  APIs: a local HTML fallback was not evidence of a functioning cloud endpoint.
- The three schemas are interface inventories, not complete request-body validators.
  Catalog parameters are checked for presence; callers must still follow their types.
- The stdio protocol is dependency-free and intentionally limited. Test compatibility
  with your MCP client; a public hosted MCP service or tunnel is not included.
- Developer-mode UI capture is a separate SSH/D-Bus procedure, not an MCP tool.
  Coordinate-based button input is untested and is not covered by MCP write guards;
  see [touchscreen access](DEVELOPER_TOUCHSCREEN.md).

## Hardware/controller research

- Exact external UMB pinout, voltage/signaling standard, electrical isolation,
  chaining and stock bootstrap remain unresolved. 115200 8E1 proves framing only.
- Accessory register permissions, delimiter behavior and dynamic indices need actual
  accessory captures. Linux consumer code is not complete accessory MCU firmware.
- The optional two-STM32 controller draft is disabled by default and has not passed real STM32 builds,
  SRAM/timer analysis, fan/motor test, stock enumeration or S5-connected test.
- Confirm fan model, power and control/tach levels before wiring; an assumed 24 V
  industrial fan does not establish the printer accessory connector's electricals.
- Add actual PWM/tach drivers, calibrated airflow conversion, motor/solenoid drivers,
  feeder/rewinder state machines, sensor fault handling and measured thermal tuning.
- Speaker routing remains unresolved without continuity or exact-board evidence.
- No bare-metal restoration or maintenance-SD boot was validated by this project.

Use existing Cura operations, scene/container APIs and documented printer routes
when extending the project. Keep UI operations on Cura's main thread, preserve
confirmation/staging guards, and add meaningful offline tests before hardware tests.
