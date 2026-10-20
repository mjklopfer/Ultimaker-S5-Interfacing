# Partial conceptual schematic / connection nodes

Revision A â€” October 19, 2026. This is a **proposed replacement-controller connection plan**, not an extracted UltiMaker schematic or a construction-ready wiring diagram. The matching `connection_nodes.csv` gives each net's individual nodes in spreadsheet form.

**P = proposed allocation based on a known interface. R = reserved, hardware choice pending. H = hold/disconnected until measured.** No connection to the external UMB cable is approved by this document. The existing firmware sketch has not been changed to drive these new pins.

## Component and connector names

| Designator | Conceptual component |
|---|---|
| U_MCU | Arduino Mega 2560, 5 V logic; first-prototype allocation |
| U_PWR5 | Regulated 24 V -> 5 V converter, rating/protection TBD |
| U_PWR_SELECT | MCU/USB power-source selection; prevents competing VBUS/5 V sources |
| U_UMB | Unknown UMB electrical interface: transceiver/level shifting/isolation/chain control TBD |
| U_MUX | Adafruit TCA9548A breakout, 5 V upstream, address 0x70 |
| S_C0..S_C3 | Four Adafruit SHT45 PTFE-covered, level-shifted breakouts, one per chamber location |
| S_M0 | Fifth equivalent sensor, material compartment |
| U_PWM | Non-inverting 5 V CMOS fan PWM interface, exact circuit/part TBD |
| FAN1 | Reported Noctua industrial 24 V four-wire fan; exact model/OEM wiring pending |
| DRV_F0..DRV_F5 | Provision for six external STEP/DIR feeder drivers; a proposed custom architecture |
| DRV_RW | Rewinder motor driver; DC/H-bridge versus stepper remains undecided |
| U_GPIO_IN / U_GPIO_OUT | Optional slow sensor/actuator GPIO expansion, device/address TBD |
| U_LED | Optional multi-channel LED driver; electrical ratings/address TBD |
| U_NFC | Optional NFC reader and antenna-selection module; interface TBD |
| J_UMB | Physical UltiMaker connector: **pin numbers not assigned** |
| JP_AIR / JP_MATERIAL | Two independent role jumpers, closed to ground = enabled |

Naming `DRV_F0..5` reserves capacity; it does not establish that the original station has six independent stepper motors. A different mechanical backend may use fewer drives plus selectors, or a different motor technology.

## Power and return nodes

```text
NET P24_IN       : J_PWR24.PLUS -> F_MAIN.IN
NET P24_FUSED    : F_MAIN.OUT -> F_FAN.IN, F_LOGIC.IN
NET FAN_24V      : F_FAN.OUT -> FAN1.VCC
NET LOGIC_24V    : F_LOGIC.OUT -> U_PWR5.VIN
NET LOGIC_5V    : U_PWR5.VOUT -> U_PWR_SELECT.EXTERNAL_5V,
                  U_MUX.VIN, S_C0..3.VIN, S_M0.VIN, U_PWM.VCC
NET MCU_5V      : U_PWR_SELECT.SELECTED_5V -> U_MCU.5V
NET LOCAL_GND   : J_PWR24.MINUS, U_PWR5.GND, U_PWR_SELECT.GND,
                  U_MCU.GND, U_MUX.GND, S_C0..3.GND, S_M0.GND,
                  U_PWM.GND, FAN1.GND, local driver LOGIC_GND
NET ACTUATOR_V  : J_ACT_PWR.PLUS -> F_ACT.IN -> selected motor/coil driver power stages [R]
NET ACTUATOR_RETURN : J_ACT_PWR.MINUS -> selected motor driver POWER_RETURN nodes [R]
```

The proposed 24 V source is a separately identified supply. **Do not assume a UMB connector pin supplies it.** Fan rating, supply capacity, fuse values, converter, connectors and wire sizes await actual loads. Motor/solenoid voltage is a separate unresolved rail; do not automatically tie ACTUATOR_V to 24 V.

The Mega power selector is a design block, not just a wire: direct 5 V injection and simultaneous USB VBUS must not contend. An external source may feed the 5 V pin only through a reviewed power arrangement. Do not put 24 V on Mega VIN, 5V, logic or fan signal pins.

Fan/driver high-current returns should run to the power distribution return rather than through MCU/sensor ground wiring. Chassis, protective earth, cable shield and external UMB reference are separate unresolved nodes. Do not connect them to LOCAL_GND by assumption. If U_UMB is isolated, its bus-side reference stays separate from its MCU-side ground as required by the selected circuit.

## Core Mega allocation

| Mega pin | Net / destination | Direction | Status |
|---|---|---|---|
| D18 / TX1 | U_UMB.MCU_TX_INPUT | MCU -> interface | P; interface bus side H |
| D19 / RX1 | U_UMB.MCU_RX_OUTPUT | Interface -> MCU | P; interface bus side H |
| D20 / SDA | I2C_SDA backbone | Bidirectional | P |
| D21 / SCL | I2C_SCL backbone | MCU clock | P |
| D22 | JP_AIR.1 | Input with pull-up | P, matches draft sketch |
| D23 | JP_MATERIAL.1 | Input with pull-up | P, matches draft sketch |
| D5 / OC3A | FAN_PWM_MCU -> U_PWM.IN | Hardware PWM output | P, Timer3 reserved |
| D2 / interrupt | FAN_TACH_MCU | Pulse input | P |
| D3 / interrupt | IO_IRQ_MCU | Optional GPIO-expander interrupt | R |
| D6, D7, D8 | UMB_CTRL0/1/2 | Unassigned interface controls | R; not assumed DE/RE/reset |
| D46 | MUX_RESET_N | Output/reset control | R; breakout reset normally pulled high |
| D0 / D1 | Existing Mega USB serial bridge | Debug | Keep separate from UART1 |

```text
NET ROLE_AIR      : U_MCU.D22 -- JP_AIR.1
NET ROLE_MATERIAL : U_MCU.D23 -- JP_MATERIAL.1
NET LOCAL_GND     : JP_AIR.2, JP_MATERIAL.2
```

Use INPUT_PULLUP as in the sketch. Both jumpers open = disabled; AIR only closed = air; MATERIAL only closed = material; both closed = both logical roles. These inputs select firmware behavior, not load power directly.

## UMB boundary â€” deliberately incomplete

```text
U_MCU.D18/TX1 -> U_UMB.MCU_TX_INPUT
U_MCU.D19/RX1 <- U_UMB.MCU_RX_OUTPUT
U_MCU.D6..8   -> U_UMB.OPTIONAL_CONTROLS [reserved only]

U_UMB.BUS_SIDE_? <-> J_UMB.UNKNOWN_CONTACTS [H: NO PINOUT ASSIGNED]
U_UMB.BUS_REF_? <-> J_UMB.UNKNOWN_REFERENCE [H]
U_UMB.CHAIN_?   <-> optional downstream connector [H]
```

UART1 uses 115200, 8E1 at the software level. This does not identify the external voltage, single-ended/differential transport, direction controls, inversion, power pins or chain-gating arrangement. No MAX232/RS-485/TTL adapter is selected. Both-role startup/address assignment is still unresolved even after the correct electrical adapter is chosen.

## Five sensor branches

```text
NET I2C_SDA : U_MCU.D20, U_MUX.SDA,
              optional U_GPIO_IN.SDA, U_GPIO_OUT.SDA, U_LED.SDA
NET I2C_SCL : U_MCU.D21, U_MUX.SCL,
              optional U_GPIO_IN.SCL, U_GPIO_OUT.SCL, U_LED.SCL

NET C0_SDA : U_MUX.SD0 -- S_C0.SDA     NET C0_SCL : U_MUX.SC0 -- S_C0.SCL
NET C1_SDA : U_MUX.SD1 -- S_C1.SDA     NET C1_SCL : U_MUX.SC1 -- S_C1.SCL
NET C2_SDA : U_MUX.SD2 -- S_C2.SDA     NET C2_SCL : U_MUX.SC2 -- S_C2.SCL
NET C3_SDA : U_MUX.SD3 -- S_C3.SDA     NET C3_SCL : U_MUX.SC3 -- S_C3.SCL
NET M0_SDA : U_MUX.SD4 -- S_M0.SDA     NET M0_SCL : U_MUX.SC4 -- S_M0.SCL

U_MUX.A0/A1/A2 : retain breakout's default LOW address straps -> 0x70
U_MUX.RST     : retain default pull-up; optional U_MCU.D46 active-low reset
U_MUX.CH5..7  : unused/reserved; possible extra ambient probe later
```

Each SHT45 is 0x44 and has its own channel. All sensor breakouts receive LOGIC_5V at **VIN**, not at their regulated 3V output. This assumes the specified Adafruit level-shifted breakout; bare SHT45 chips and arbitrary 3.3 V-only modules must not receive these 5 V nets.

Sensor breakout SDA/SCL pull-ups service the downstream branches; the multiplexer does not provide downstream pull-ups itself. Check the actual upstream pull-ups and total parallel resistance before adding expansion boards. Start at 100 kHz, keep branch wiring short and select one sensor branch at a time. Proposed additional GPIO/LED devices need nonconflicting addresses on the upstream bus. I2C buffer selection remains a bench-test decision.

The five requested probes do not include a separate external ambient measurement. S_C3 may be positioned near the exhaust for exhaust-temperature feedback, but must be labeled by actual location. An extra channel-5 probe is a future option rather than pretending the material compartment is ambient.

## Fan PWM drive and tach feedback

For a standard Noctua four-pin 24 V fan, nominal pin functions are 1 ground, 2 supply, 3 tach, 4 PWM. Colors are normally black/yellow/green/blue. Verify the actual fan and any OEM cable before using those connector numbers.

```text
FAN1.VCC  <- FAN_24V
FAN1.GND -- LOCAL_GND

U_MCU.D5 -> U_PWM.IN
LOGIC_5V -- R_PWM_BOOT (proposed 10k) -- U_PWM.IN
U_PWM.OUT -> R_PWM_SERIES (proposed 100R) -> FAN1.PWM

FAN1.TACH -- FAN_TACH_RAW
LOGIC_5V  -- R_TACH_PULLUP (proposed 4.7k) -- FAN_TACH_RAW
FAN_TACH_RAW -> R_TACH_SERIES (proposed 1k) -> U_MCU.D2
```

U_PWM is a **non-inverting CMOS drive/interface**, exact part and enable wiring to be selected. Require appropriate powered-off/high-impedance behavior (for example specified Ioff protection) so the fan's internal PWM pull-up cannot back-power an unpowered logic rail through the buffer. The fan already pulls its PWM input up internally; R_PWM_BOOT is on the **buffer input**, not another pull-up at the fan pin. The proposed buffer input pull-up requests full-speed ventilation while Mega D5 is high-impedance at reset, provided the buffer is powered and enabled. Check the complete power-up/power-down behavior before relying on it. Do not apply open-collector drive simply because the tachometer is open collector; Noctua distinguishes those two circuits.

Generate a non-inverted 25 kHz PWM signal; 100% high means maximum command. A tach pull-up of 4.7k to 5 V draws approximately 1.06 mA when low, below Noctua's documented 2 mA maximum for the 24 V fan tach output. Series/pull-up values are starting design values, not validated EMI or edge-rate results. A future 3.3 V MCU needs the appropriate voltage-domain review.

Count tach edges in an interrupt and atomically snapshot the counter. Two pulses/revolution gives RPM = Hz*30. Apply the identity-default RPM calibration only after measuring raw RPM. Stop/enable behavior at 0% PWM is fan-model dependent and needs confirmation; an actual switched fan supply, if required, is a separate optional power stage.

Software order: S5 airflow request -> calibrated nominal PWM OR local temperature loop -> ten-point PWM correction -> D5 driver. Tach -> raw RPM -> ten-point RPM correction -> S5 report. The two paths stay separate; no fabricated tach response to match an expected drive demand.

## Material-handling drive reservations

This is a **six-stepper-channel custom replacement option**, not a finding about the stock hardware. Each connection passes through the selected driver's required logic interface; a 3.3 V-only input must not receive a 5 V Mega signal directly.

| Bay | STEP pin | DIR pin | Driver symbol |
|---|---|---|---|
| A / 0 | D24 | D25 | DRV_F0 |
| B / 1 | D26 | D27 | DRV_F1 |
| C / 2 | D28 | D29 | DRV_F2 |
| D / 3 | D30 | D31 | DRV_F3 |
| E / 4 | D32 | D33 | DRV_F4 |
| F / 5 | D34 | D35 | DRV_F5 |

```text
U_MCU.D36 -> DRIVER_LOGIC_IF.FEED_ENABLE -> DRV_F0..5.ENABLE [R]
DRV_Fn.motor_outputs -> M_FEED_n.coils [R: actual motor/coil pairs TBD]
ACTUATOR_V -> each driver's protected power input [R]
```

Driver enable polarity, disabled-state bias, separate versus common enable, current limiting, supply rating, fault routing, microstep/serial configuration and motor type remain to be chosen. Keep drivers disabled on reset using the selected driver's specified bias. No motor or solenoid load connects directly to a Mega output. STEP pulse timing should use a deterministic motion scheduler; reserve Timer1 provisionally for motion and Timer3 for fan PWM. A GPIO expander is not a drop-in source for time-critical STEP pulses.

Power returns belong to the power stage. Join ACTUATOR_RETURN to LOCAL_GND only as required by the reviewed driver interface; an isolated interface may keep them separate. The CSV intentionally does not bridge that unresolved boundary. Expansion-board and NFC power/ground connectors also remain part-selection-dependent; their signal reservations do not establish a complete powered circuit.

### Rewinder / optional selector

```text
U_MCU.D9  -> DRV_RW_INTERFACE.PWM_OR_STEP [R]
U_MCU.D37 -> DRV_RW_INTERFACE.DIRECTION [R]
U_MCU.D38 -> DRV_RW_INTERFACE.ENABLE [R]
U_MCU.D39 -> ACTUATOR_PERMISSION_INTERFACE [R: optional common inhibit]
DRV_RW_INTERFACE -> actual rewinder power stage/motor [R]
```

D9 is reserved; it is not yet a statement that the stock rewinder is a DC motor or that default PWM frequency is suitable. A changed mechanism may need a stepper driver, DC H-bridge, clutch or passive spool buffer instead. Solenoid selector modules need physical selection/clearance feedback before advancing new filament.

## Slow I/O / expansion reservations

| Expansion symbol | Proposed node/function | Status |
|---|---|---|
| U_GPIO_IN.IN0..11 | Up to two filament detection inputs per bay | R; logical events known, actual physical counts/types TBD |
| U_GPIO_IN.IN12 | Door switch | R |
| U_GPIO_IN.IN13..15 | Selector/homing/driver status inputs | R; may require more channels |
| U_GPIO_OUT.OUT0..7 | Generic selector/clutch/DC-coil power-stage control inputs | R; no stock coil assignment claimed |
| U_GPIO_OUT.OUT8..15 | Additional optional auxiliary controls | R |
| U_LED.CH0..11 | Bay white/blue channels | R; logical channel mapping source-confirmed |
| U_LED.CH15 | Frame lighting | R; current/voltage and LED driver TBD |
| U_GPIO_IN.IRQ / U_GPIO_OUT.IRQ | Interface -> D3, optional interrupt | R; combine only if outputs support compatible open-drain wiring |

Inputs need interface conditioning for their actual sensor voltage and output type. Contact/compatible open-collector sensors may use pull-ups, but do not place a 24 V proximity-sensor output directly on the expander. Keep driver faults and physical travel limits available to the fault logic; allocate additional I/O if the chosen mechanics need it.

For a **DC coil using a low-side MOSFET stage**, conceptual nodes are:

```text
ACTUATOR_V -> DC_COIL.PLUS
DC_COIL.MINUS -> Q_COIL.DRAIN
Q_COIL.SOURCE -> POWER_RETURN
U_GPIO_OUT.OUTn -> gate interface / R_GATE -> Q_COIL.GATE
Q_COIL.GATE -> R_GATE_OFF -> Q_COIL.SOURCE
DC_COIL -> rated flyback/clamp network -> appropriate supply/return
```

This is not a universal valve/motor circuit. Select voltage/current ratings, gate drive, suppression and release time with the actual coil. A simple diode can change release time; actuator timing matters for selectors. Bipolar/latching coils or reversible motors may need another topology. GPIO expanders and LED outputs are not power switches.

## Reserved functional blocks with no pin assignments

- Left/right decoupler or buffer feedback: conditioned analog or digital interface TBD. No gain/offset values establish sensor voltage or pinout. Reserve A0/A1 only as possible conditioned analog inputs, not as verified stock connections.
- NFC reader and antenna selection: keep Mega SPI D50/D51/D52 available if the selected reader uses SPI; D53 may be its chip select. Actual reader voltage/reset/antenna mux connections are unknown.
- Dryer fan, heater and valve/regeneration subsystem: treat as separate optional power/control modules. No heater or mains wiring is defined here. Heater implementation needs actual sensor/protection/power-stage evidence before mapping an enable output.
- External ambient probe: optional extra multiplexed SHT45 on channel 5, if needed to supply genuine ambient temperature.
- UMB chain-control and device-bootstrap interfaces: fully unresolved; leave connector pins unassigned.

## Review / next evidence

The definite design decisions are the signal groups and four-plus-one probe arrangement. Mega pin assignments, resistor values, driver topology and component choices are provisional. Electrical domains marked R/H must not be silently converted into direct wires.

Next steps: board photographs; actual fan label; UMB transceiver identification and connector continuity; one feeder/selector hardware choice; motor/coil voltage/current data; target Arduino pin/timer and memory review; then a bench wiring schematic with real parts and connector orientations. Firmware has no output changes in this revision.

References checked for this draft:

- Mega pin functions: https://docs.arduino.cc/resources/pinouts/A000067-full-pinout.pdf
- Noctua PWM/tach specification: https://cdn.noctua.at/media/Noctua_PWM_specifications_white_paper.pdf
- Adafruit SHT45 breakout power/level shifting: https://learn.adafruit.com/adafruit-sht40-temperature-humidity-sensor/pinouts
- TCA9548A breakout power/reset/channels: https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout/pinouts
