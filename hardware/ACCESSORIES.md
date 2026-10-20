# UMB, Air Manager and Material Station

This is an interface description, not UltiMaker accessory source code. The
sample peripheral implementation is original project code and is **untested on
physical STM32/S5 hardware**. Host-side observations do not prove full accessory
firmware behavior, electrical compatibility or startup interoperability.

## UMB operational link

Observed framing is 115200 baud, eight data bits, even parity, one stop bit.
Requests use `FF | address | command | payload length | payload | CRC8`.
Replies use `FF | command/status | payload length | payload | CRC8`, without an
address or sequence number. CRC excludes FF, uses polynomial 0x07, initial zero,
MSB-first and no final XOR. Keep one outstanding transaction on the whole link.

Discovery obtains indices then register names. Command 02 reads; 03 writes ASCII
values using a length/NUL/index layout; 10/11 control monitoring and 1F polls.
Indices are dynamically discovered, not universal hardcoded addresses. The host
startup also performs device-chain initialization and firmware/application checks.
A manually addressed operational parser alone is not a stock accessory emulator.
Monitor delimiter behavior remains ambiguous; see the [protocol draft](umb-controller/PROTOCOL.md).

## Air Manager

Connection detection includes bootloader discovery, host identity/firmware checks,
Linux service discovery and an advancing timestamp heartbeat. Filter presence is
a separate signal. See [startup, identity and health](ACCESSORY_DISCOVERY_AND_HEALTH.md)
for message structure, status registers and the unresolved controller architecture.

| Register | Value representation / units | Known values or limits | Source-observed consumer access |
|---|---|---|---|
| data.fanSwitchPower.0 | Integer-like ASCII, unitless | 0 off, 1 on; other states not established | Read/write |
| data.fanAirflowSetPoint.0 | Numeric ASCII, airflow in m3/h; host calculations include decimals | Host table spans 11.4-48.0; default 48; accepted device bounds/precision unverified | Read/write |
| data.fanSpeedMeasured.0 | Numeric ASCII, mapped to RPM by the HTTP interface; host feedback is float-oriented | Hardware maximum/resolution and fault values unverified | Read |
| data.fanDutyCycle.0 | Numeric ASCII; host feedback is float-oriented | Raw scaling/range unverified; do not assume 0-1, 0-100 or 0-255 | Read |
| data.fanSpeedRatio.0 | Signed integer-oriented ASCII; speed/target ratio in percent with status sentinels | 100 nominal match; 0 blocked; -1 off; -2 settling; -3 zero target; upper bound unverified | Read |

These are host-interface observations, not live accessory acceptance tests. See
[Air Manager value formats and limits](AIR_MANAGER_VALUES.md) for precision,
serialization, status interpretation and implementation guidance.

The Linux host selects an airflow target from temperature/material policy and a
lookup table; this is not simply a commanded PWM percentage. The described host
path does not establish a continuously measured chamber-temperature feedback loop.
Accessory PWM waveform generation and fan power electronics remain unverified.
Possible firmware-string names for other measurements are hypotheses without
established wire paths/permissions. No accessory live register inventory is claimed.

## Material Station

Six logical bays are indexed 0 through 5. Register values written to
`prefeeder_n.printer_command.0` request load, unload, eject, pause, resume, parking,
end-of-filament reset and recovery workflows. They initiate state machines, not
raw stepper movements. Feedback describes state, previous state, transitions and
filament direction. Linux and printer-side procedures coordinate the full handoff.

Other functional groups cover door state, dehumidifier humidity/temperature/state/
errors, NFC presence/command/sector data, rewinder selection, decouplers and LEDs.
These are candidates for implementing a compatible backend, not proven actuator
wiring. Environmental readings already fit the register-value wire format;
additional custom fields require host discovery and application/UI support.

## Proposed STM32 IO, not verified stock wiring

| Block | Potential sensors/actuators | Implementation status |
|---|---|---|
| Role enable | One active-low jumper per fixed-role STM32 controller | Separate bench entry points |
| Environment | Four chamber probes through Air-controller TCA9548A; one material probe on a separate Material-controller bus | Sampling draft; no physical validation |
| Fan | Conditioned PWM output and tach input through suitable interface electronics | Mathematical duty/RPM models; hardware timer/ISR/driver not implemented |
| Material feeder | Step/direction drivers, engagement/selector solenoids, arrival/exit/filament sensors | Hardware/backend not implemented |
| Rewinder/buffer | Motor driver and decoupler/buffer feedback | Sensor type, power and mechanism unresolved |
| Lights/NFC/drying | External LED driver, NFC reader; optional drying subsystem | Provisions only, not a complete design |

Two ten-knot interpolated maps default to identity: requested duty to driven duty,
and measured RPM to reported RPM. Optional follow/trim/local PI logic can use
selected environmental probes. This is an experimental local control model;
airflow conversion, real gains, fault policies and actual fan behavior need tests.

The design requires two STM32 controllers, one per accessory role, because native
startup uses distinct STM32 chip-ID/memory profiles. Suggested bench boards are
NUCLEO-F072RB and NUCLEO-F303ZE. See the [STM32 plan](umb-controller/STM32_DEPLOYMENT.md)
and [conceptual node list](umb-controller/CONCEPTUAL_CONNECTIONS.md). These are not
validated replacements. Stock bootstrap, firmware-update ownership, UMB interface
and real hardware drivers remain unresolved. Transport, outputs and stock writes
default disabled; never fabricate healthy states for missing hardware.

For other configured types, generic register/D-Bus operations and original
accessory concepts, see the [UMB extension map](UMB_EXTENSION_MAP.md).
