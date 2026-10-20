# Air Manager register value formats and limits

Reference: S5 R1, firmware 9.0.3.0 host interface. This describes observed host
behavior and table contents, not verified accessory MCU validation rules. No
register writes, range sweeps or physical fan tests were used to establish this
document. No vendor implementation source or lookup table is reproduced.

## Values on the operational wire

Registers carry **ASCII text**, not a binary IEEE float or a fixed-width integer.
The register's `.0` name suffix does not specify numeric precision or encoding.
The operational sender converts a value to text; individual consumers and the
accessory determine its meaning and accepted grammar.

For a write, the value occupies the following part of the command-03 payload:

```text
L | ASCII value | NUL | discovered index byte 0 | discovered index byte 1
```

`L` counts the value characters plus the NUL. For example, the text `14.45` has
five characters, so this illustrative payload uses length 6:

```text
06 | 31 34 2E 34 35 | 00 | I0 I1
```

`I0 I1` are placeholders for the discovered register index, not literal bytes or
a fixed Air Manager address. This example demonstrates encoding, not a command
that was sent or proof of device acceptance. Replies expose textual values;
do not assume writes' terminator/index layout is also a read-value layout.
See [operational framing](umb-controller/PROTOCOL.md).

For an experimental backend, preserve fractional values, use a decimal point,
omit units/thousands separators, and reject malformed/non-finite input. Exact
accepted decimal places, rounding/truncation, exponent notation and alternate
spellings of equivalent values still need accessory validation. A host type
annotation alone does not establish the D-Bus signature or the device's parser.

## Airflow target: data.fanAirflowSetPoint.0

- **Meaning:** requested airflow in cubic metres per hour, not PWM percent or RPM.
- **Host computation:** the table loader converts numeric fields to floating point;
  selection returns a table entry without an explicit integer rounding operation
  in that calculation. Entries include fractional values such as `11.4`, `14.45`
  and `20.55`. This contradicts an integer-only reading of the annotations.
- **Observed table domain:** 11.4 through 48.0 m3/h, with 13 distinct targets in
  the inspected table and one or two decimal places. This is a host selection
  domain, **not a proven device minimum/maximum, resolution or increment**.
- **Default/fallback:** 48 m3/h when the relevant lookup information is unavailable.
- **Type uncertainty:** wrappers include integer annotations/defaults. Actual
  coercion along the D-Bus/accessory path and exact on-wire formatting were not
  captured from a live accessory. Decimal input support is therefore an intended
  host behavior to validate, not a completed device acceptance test.
- **Unknown:** clamping/rejection outside the table domain, physical fan limits,
  accepted precision and whether the device normalizes the returned setpoint.

Use a real-valued representation in a new communications/backend design so table
precision is not silently lost. A conservative bench configuration can restrict
requests to the observed host domain until measured, but label that as a local
policy rather than a discovered firmware limit. Do not assume zero airflow means
power off; the separate power register is how the host commands off/on.

## Enable: data.fanSwitchPower.0

The host sends integer values 0 for off and 1 for on. Use the ASCII numeric
representation, rather than assuming the device accepts words such as `true` or
`false`. Other values, acknowledgment details and physical spin-down behavior
have not been validated. Enable and airflow setpoint are separate controls.

## Measured speed: data.fanSpeedMeasured.0

The host exposes float-oriented speed feedback; the HTTP Air Manager schema
identifies this quantity as RPM. Treat it as a numeric measurement. Integer-looking
text does not prove integer-only resolution. Maximum RPM, granularity, freshness,
stall behavior and any special error values are not established. Do not use an
assumed fan rating or the sample controller's calibration domain as a stock limit.

## Duty feedback: data.fanDutyCycle.0

The host callback is float-oriented, but the observed interface does not settle
whether a raw value means fraction, percent, timer count or another scale.
No justified 0-1, 0-100 or 0-255 range, step size or PWM carrier frequency was
established. It is read-only in the inspected consumer wrapper; that does not
prove every accessory firmware rejects a write to the underlying register.

The original sample controller uses percent internally for its own PWM mapping.
That is a proposed backend convention, not evidence that this stock feedback
register also uses percent. Add an explicit scaling adapter only after measuring.

## Ratio/status: data.fanSpeedRatio.0

Host documentation describes a signed integer ratio of measured speed to target
speed, in percent, plus the following special values:

| Value | Host-described interpretation |
|---|---|
| 100 | Measured speed equals target speed |
| 0 | Fan blocked |
| -1 | Fan power off |
| -2 | Fan still settling after power-on |
| -3 | Target speed zero |

The host description mentions roughly three seconds for stabilization; this was
not measured. Negative values are statuses, not negative RPM or PWM. Preserve
the sign and distinguish them from valid ratio data. A ratio is not a duty-cycle
command and need not be capped at 100%; accepted positive range is unconfirmed.
These meanings were not confirmed by forcing the physical fan into fault states.

## What remains to measure

With a correctly identified accessory/electrical interface and an idle authorized
bench setup, obtain the actual discovered names/indices and readback formats,
then determine units/scaling, accepted precision/ranges, update cadence and
enable/settling behavior. Record whether out-of-range values are rejected,
clamped or normalized; do not infer that from a successful transport response.
Keep these checks separate from an active print and do not substitute fabricated
RPM/healthy states for missing measurements.

Provenance is the inspected Linux Air Manager consumer interface, operational
register sender, HTTP interface schema and aggregate host-table observations.
Function annotations and comments are evidence with limits, not a substitute for
an accessory wire capture or firmware-side validation.
