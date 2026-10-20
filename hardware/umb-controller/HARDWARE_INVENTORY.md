# Material Station: sensors, actuators and functions

The original unit is UltiMaker's Material Station (`misp` in firmware). User shorthand AMS here is not a claim of Bambu AMS protocol compatibility. Evidence is the installed Linux consumer source, not a stock PCB schematic or disassembled accessory.

| Subsystem | Confirmed function / evidence | Physical details still needed |
|---|---|---|
| Six bays A-F | `MISP_BAYS=6`; `prefeeder_0..5` command/state registers | Number/type of motors, gears, selectors and clutches per bay |
| Filament detection | State events distinguish FilamentDetect1/2 and Undetect1/2; load/pullback/EOF transitions | Sensor technology, exact location, wiring and whether any signals are virtual/shared |
| Prefeeding | LOAD, UNLOAD, EJECT, PARK, EXPECT_RETRACT, LOAD_TO_PRINTHEAD; FOLLOWING and idle states | Motor feedback, direction/power/step interface, speed/force/length limits |
| Decouplers left/right | state, distance_max, gain, offset_bits, offset_dis_one/two; decoupler controller motors_under_control | Actual displacement/tension sensor type, range, analog/digital interface and mechanical function |
| Flow/EOF coordination | FlowSensorEndOfFilament event and printer-side procedures | Which measurements originate in S5 vs station; notification timing |
| Rewinder | STATE, PREV, TRANSITION_EVENT, current_prefeeder; rewinder_motor.output and enabled | Motor count/type, driver, engagement mechanism, polarity and feedback |
| Routing to extruder 1/2 | Per-slot filament_direction; left/right decoupler/controller names | Selector topology, actuation and interlocks; ability to feed both printer paths |
| NFC/material identity | tags_visible, command, four sector_data words; bay selection and page read/write | Reader IC, antenna mux/circuit, bus, six antenna connections and geometry |
| Bay indicators | White and blue channels per bay; LED indices 0..11 | LED driver part and current/voltage; `led_driver/led_pwm_output` literal name validation |
| Frame light | Index 15, brightness 0..1 | Driver/cable and power requirements; indices 12..14 are not assumed available |
| Door | door_sensor.door_opened.0 | Switch type/polarity/debounce and fault semantics |
| Material temperature/RH | dehumidifier.current_temperature/current_humidity; C and percent RH in consumer | Existing probe type/location; replacement fifth SHT45 can measure the compartment but needs cross-check |
| Dryer fan | DHUM_NORMAL_FAN_ON/OFF and fan self-test/verify states | Fan supply, PWM/tach and airflow arrangement |
| Dryer heat/regeneration | PREHEAT, REGENERATE, COOL_DOWN, heater self-test/verify states | Heater type/power, temperature sensing, thermal protection and control loop |
| Dryer valves/position | VALVES_TO_REGEN/DEHUM; valve coil/switch/end-switch self-tests | Number of valves/solenoids/motors/endstops, drive current, travel and energized state |
| Dryer faults | hw_error bitmap, dehumidifier_state, high RH warnings | Exact bit meanings and accessory internal protections |


- `/usr/share/misp_service/service/mispService.py`: constants near lines 39-47, rewinder/decoupler monitoring near 145-161, dehumidifier states near 378 onward.
- `/usr/share/misp_service/service/mispSlot.py`: RequestSlotState, SlotState and TRANSITIONS_REASONS enums; command write near 433.
- `/usr/share/misp_service/nfc/mispNfcDevice.py`: NFC command packing, data words and readiness callback.
- `/usr/share/misp_service/led/mispLedManager.py` and mispSlotLedManager.py: light indices and brightness.

The live configuration service returned an empty `misp` map during this investigation. No configuration-derived extra actuator endpoints were added. The host supports a feature-flagged configuration-to-register path, so the catalog may need to expand when a real station/configuration is available.

## Proposed replacement interfaces

The software backend should accept logical `requestSlotAction(bay, action)` and expose verified slot state/direction/event, while delegating to interchangeable hardware modules:

- `FeederDrive`: controlled advance/retract/stop with distance/speed and timeout.
- `RouteSelector`: select confirmed output 1/2, verify home/selection, reject occupied junction conflicts.
- `FilamentSense`: per-route/prefeeder arrival/departure, jam and clearance confirmation.
- `SpoolReturn`: take up retract slack without overpowering the filament path.
- `DecouplerOrBuffer`: measured compliance/tension for handoff and following.
- `IndicatorDriver`: bay white/blue and frame brightness.
- `MaterialIdentity`: NFC reader or an explicitly validated manual-material workflow.
- `StorageEnvironment`: temperature/RH, door, and dehumidifier controls only if hardware is fitted and implemented.

These are design interfaces, not claims that the stock unit uses this exact motor/solenoid layout. Missing heater/valve/NFC or decoupler behavior must be handled explicitly; do not emulate healthy machinery that is absent. The current draft rejects actuator commands until a real backend exists.
