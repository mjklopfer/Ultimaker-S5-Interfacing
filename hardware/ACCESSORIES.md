# UMB, Air Manager and Material Station

This is an interface description, not UltiMaker accessory source code. The
sample peripheral implementation is original project code and is **untested on
physical Arduino/S5 hardware**. Host-side observations do not prove full accessory
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

## Proposed Arduino IO, not verified stock wiring

| Block | Potential sensors/actuators | Implementation status |
|---|---|---|
| Mode selection | Two active-low boot jumpers | Mode logic modeled |
| Environment | Four PTFE-protected SHT45 chamber probes plus one material-compartment probe via TCA9548A | Sampling draft; no physical validation |
| Fan | Conditioned PWM output and tach input through suitable interface electronics | Mathematical duty/RPM models; hardware timer/ISR/driver not implemented |
| Material feeder | Step/direction drivers, engagement/selector solenoids, arrival/exit/filament sensors | Hardware/backend not implemented |
| Rewinder/buffer | Motor driver and decoupler/buffer feedback | Sensor type, power and mechanism unresolved |
| Lights/NFC/drying | External LED driver, NFC reader; optional drying subsystem | Provisions only, not a complete design |

Two ten-knot interpolated maps default to identity: requested duty to driven duty,
and measured RPM to reported RPM. Optional follow/trim/local PI logic can use
selected environmental probes. This is an experimental local control model;
airflow conversion, real gains, fault policies and actual fan behavior need tests.

The Mega 2560 is a provisional first prototype. Classic Mini/Pro Mini RAM/IO are
restrictive for combined accessory roles. Expanders do not solve timing/memory.
Use external power stages and the correct, still-unresolved UMB transceiver.
The [conceptual node list](umb-controller/CONCEPTUAL_CONNECTIONS.md) is not a
stock pinout. Transport, actuator outputs and register writes remain disabled
by default. Do not report fabricated healthy/loaded states for missing hardware.
