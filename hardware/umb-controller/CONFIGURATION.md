# How the draft pieces connect

## Select role and endpoint behavior

Use `AirManagerBench.ino` on the Air STM32 and `MaterialStationBench.ino` on
the Material STM32. Each has one fixed role and a separate active-low enable
jumper after explicit pin configuration. No pins or peripherals are enabled by
default. See [STM32 build macros and board requirements](STM32_DEPLOYMENT.md).

`ReplacementDevice` looks up stock names in `ObservedCatalog.h` and delegates
hardware fields to `umb::Hardware`. The default backend rejects unsupported
reads/writes. Implement only real measurements and states. Command acceptance
does not prove motion completion; subsequent feedback must reflect hardware.
Global stock writes remain disabled in both sketches.

The shared router can model multiple addresses in native fixtures, but the
selected deployment uses one role per STM32. Each isolated fixture's address
zero must be replaced by working host-negotiated startup before real integration.
Do not use an accessory as a second master on the printer bus.

## Fan calibration

The first table maps nominal duty to output duty, in percent. Edit the ten knots in a `FanModel` instance or later load a versioned configuration:

```cpp
umb::FanModel fan;
fan.drive.points[5] = {50.0f,55.0f}; // illustrative calibration only
if (!fan.drive.valid()) { /* report config fault; don't apply invalid output */ }
```

All ten inputs must remain strictly increasing, outputs nondecreasing, range within 0..100%, input endpoints 0 and 100. Default table is identity. `fan.setPower(false)` requests zero even with a corrupt table. A nonzero offset at a zero nominal command may still run a powered fan; decide that deliberately during calibration.

The second table maps raw RPM to reported RPM:

```cpp
fan.reportedSpeed.points[3] = {3000.0f,3100.0f}; // example, use only measured correction
```

It must preserve 0->0. The default RPM knot domain 0..9000 is an illustrative identity domain, not the installed fan rating. A clamped mapping is diagnostic; do not silently publish a saturated result as an accurate measurement.

At runtime, atomically snapshot the tach edge counter and call `fan.sampleTach(totalEdges, nowMs)`. Call `fan.reportedRpm(nowMs)` to obtain a freshness-checked result. Read `fan.rawRpm()` for uncorrected diagnostics. The draft has no physical ISR, so do not treat an uninitialized zero counter as evidence of measured zero RPM.

## Optional local control

```cpp
umb::ThermalControl control;
control.config.mode=umb::ThermalMode::LocalFeedback;
control.config.sensorMask=0b0101; // chamber probes 0 and 2
control.config.aggregate=umb::Aggregation::Maximum;
control.config.targetC=35.0f; // proposed local setting, not extracted from S5
control.reset();
```

The configured gains are placeholders. Use `TrimFeedForward` to add bounded correction to calibrated nominal feed-forward, or `FollowFeedForward` for the default no-feedback mode. Reset when changing target/mode/sensor selection.

Proposed integration sequence, **not yet connected to outputs in the sketch**:

1. Read host fan-power and airflow requests from the backend.
2. Convert m3/h to nominal PWM using a measured plant map when follow/trim requires it.
3. Update environment.nowMs and obtain local loop demand with `control.update(...)`.
4. On an invalid result, execute the explicitly chosen fallback policy and report the reason; do not silently use zero or last-good forever.
5. On a valid result, set fan power/nominal demand, evaluate `fan.outputDuty()`, check validity/clamping and apply through a verified 25 kHz fan driver.
6. Snapshot tach, compute raw and reported RPM, and publish genuine fresh results through the Air Manager backend.
7. Publish/log control mode, ignored flow-demand status, calibration version, sensor validity and actuator faults.

No telemetry override should create plausible RPM when the rotor is stopped or stale. `data.fanSpeedMeasured.0` should represent measured speed with at most a documented measurement calibration. `data.fanSpeedRatio.0` and raw duty encoding need real host/accessory checks before implementation.

## Hardware I/O

The sensor sampler is the only included physical-I2C draft and starts disabled. It uses an explicit per-controller TwoWire bus at 100 kHz. Air samples four SHT45 0x44 probes through TCA9548A 0x70 channels 0..3; Material samples one SHT45 0x44 directly on its independent bus. The environment model stores these at slots 0..3 and 4 respectively; remote slots remain invalid. Board I2C pull-ups, cable length and library timing need validation. Keep UMB packet processing ahead of sensor work. A faulting I2C bus must not block UMB indefinitely.

No STEP/DIR, solenoid, selector, heater, valve or fan-output pins are driven in this version. All STM32 physical pins remain unassigned symbolic reservations. Choose actual pins after electrical review and timer/interrupt budgeting. Pin expanders may serve slow controls/indicators but not time-critical step generation or tach capture without a suitable dedicated controller.
