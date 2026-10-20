# Remaining work

## Evidence / hardware photographs

- [ ] Both sides of Air Manager PCB; board number/revision; chip markings near external UMB connectors.
- [ ] S5 R1 UMB connector/interface circuitry; any separate adapter board and cable labels.
- [ ] Actual fan model/rating label, connector orientation and wire order.
- [ ] Existing sensor connector and sensor PCB; check external ambient measurement source.
- [ ] If available, Material Station control PCB, feeder/rewinder mechanisms, selectors, dryer and driver labels.
- [ ] Identify transceivers, regulated rails, bus pinout, chain gating and power/current limits.
- [ ] Review CONCEPTUAL_CONNECTIONS.md and connection_nodes.csv against actual connector orientations, driver voltage domains, power/reset states and chosen mechanisms.


## Protocol / S5 integration

- [ ] Use [startup/health requirements](../ACCESSORY_DISCOVERY_AND_HEALTH.md) as an architecture gate before finalizing both STM32 front ends.
- [ ] Confirm both saved chip-ID mappings on candidate boards and full bootstrap exchange; resolve flash-check/update ownership without fabricated identity/version replies.
- [ ] Choose and document stock-compatible startup versus an explicitly adapted Linux host; neither is implemented.
- [ ] Validate timestamp freshness/reset/wrap, expected-accessory configuration, filter removal, service failure and truthful subsystem readiness.
- [ ] Validate Material Station calibration/error bitmaps, bay transitions and missing-backend behavior; no equivalent MISP timestamp heartbeat is established.

- [ ] Passive capture of genuine startup, address assignment, operational traffic and watchdog timing.
- [ ] Validate two separate fixed-role STM32 controllers in the real chain; one-IC dual identity is outside the selected design.
- [ ] Resolve monitor delimiter using raw captures; verify reply ACK/error semantics and values/types.
- [ ] Enumerate all actual register names/indices, permissions and any dynamic MISP configuration fields.
- [ ] Validate duty-cycle scaling, speed ratio algorithm and stock environmental field semantics.
- [ ] Find whether chamber target exists elsewhere; otherwise retain explicit local temperature target.
- [ ] Implement trustworthy hardware backends, truthful fault/state telemetry and missing-feature behavior.
- [ ] Add Linux logger/UI/API consumer for custom environmental/control diagnostics if desired.

## Fan and environment

- [ ] Both real STM32 target compiles; inspect linker report, SRAM/stack margin and UART timing under load.
- [ ] Choose 25 kHz PWM hardware driver, electrical interface and atomic tach acquisition.
- [ ] Calibrate fan tach; retain raw counts/RPM with reported RPM and calibration version.
- [ ] Build actual housing/filter airflow -> nominal PWM conversion; no implicit m3/h = percent rule.
- [ ] Calibrate both ten-point tables; retain identity defaults until measured.
- [ ] Fit/cross-check four chamber PTFE SHT45s and one material-compartment sensor.
- [ ] Validate sensor removal, stale readings, I2C faults, vapor exposure and cable noise.
- [ ] Integrate/test all three temperature modes and deliberate fallback policy; tune PI on real hardware.
- [ ] Check saturated/unreachable target, sensor failure, zero command, stall and communication loss.

## Material handling mechanics

- [ ] Inspect MakerWorld/eBay candidates; verify 2.85 mm bores, rollers, tube fit, and tip clearances.
- [ ] Choose powered feeder plus engagement/selection arrangement; passive guides alone are insufficient.
- [ ] Bench one path with measured arrival/departure, advance/retract/park and jam recovery.
- [ ] Identify two-path architecture to preserve simultaneous dual-extrusion capability.
- [ ] Define each drive, solenoid, selector endstop, filament sensor, buffer and rewinder function.
- [ ] Implement asynchronous load/unload/handoff/EOF/recovery state machines coordinated with S5.
- [ ] Decide NFC and storage drying scope; implement or explicitly reject unsupported functions.
- [ ] Scale to six bays only after one-path and two-path tests pass.

## Package status

- [x] Design/requirements and confidence-labeled hardware inventory.
- [x] Source-derived 95-entry stock register catalog and proposed 20-field environmental extension.
- [x] Operational peripheral packet parser/dispatcher; CRC, discovery, read/write/monitor handling.
- [x] Separate STM32 role sketches, active-low enables, unassigned pins and disabled peripherals.
- [x] Five-sensor sampling draft; tach/RPM model; two ten-point lookup tables.
- [x] Optional follow/trim/local PI control model.
- [x] Native C++ tests, Python reference tests and sketch syntax check.
- [ ] Actual STM32 compiles, electrical testing and physical printing/material handling.
