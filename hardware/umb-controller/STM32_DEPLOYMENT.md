# Two-controller STM32 development plan

## Selected architecture and suggested boards

Use **two physical STM32 controllers**, one fixed accessory role per controller.
They may eventually share a carrier PCB; they remain separate discovery,
firmware, reset and recovery domains. This supersedes the single-controller/two-jumper
proposal. A jumper on each new controller enables its fixed role; it does not
change the chip identity or make one MCU represent both accessories.

| Controller | Provisional development board | Reason |
|---|---|---|
| Air Manager | [NUCLEO-F072RB](https://www.st.com/en/evaluation-tools/nucleo-f072rb.html) | STM32F072RB, 128 KiB flash and 16 KiB SRAM; family corresponds to observed chip ID 0x0448; ST-LINK and accessible headers |
| Material Station | [NUCLEO-F303ZE](https://www.st.com/en/evaluation-tools/nucleo-f303ze.html) | STM32F303ZE with larger package/I/O access for drivers and feedback; family corresponds to observed chip ID 0x0446; ST-LINK and accessible headers |

These are **suggested bench boards, not demonstrated S5 replacements**. Product
pages and MCU families were checked against ST references. Physical chip ID,
bootloader version, ROM UART/pin availability and complete host startup must be
confirmed on the purchased board/revision before printer attachment.

The STM32F303ZE has 512 KiB physical flash according to ST; the captured S5 MISP
configuration uses a 384 KiB firmware region ending at 0x08060000. Do not silently
replace that region with the whole physical flash or assume the remainder is
available. The reason for that host boundary remains unresolved.

The [upstream STM32 device table](https://github.com/stm32duino/stm32flash/blob/main/dev_table.c)
also associates these families with 0x448 and 0x446. It is an identification
reference, not proof of the exact S5 bootloader implementation. The host profile
and chain-control details are recorded in
[accessory startup and health](../ACCESSORY_DISCOVERY_AND_HEALTH.md).

## Division of responsibility

| Air controller | Material controller |
|---|---|
| Four chamber SHT45 probes through TCA9548A channels 0..3 | One material-compartment SHT45 on its own local I2C bus |
| Fan PWM driver, tach input, airflow conversion and both calibration tables | Feeders/selectors/solenoids, arrival/exit/buffer feedback and rewinder |
| Optional local chamber temperature loop | Door, decouplers, optional NFC, LEDs and drying backend |
| Air Manager registers, advancing heartbeat and truthful fan/filter status | MISP registers, bay state transitions, calibration and truthful dryer/drive status |
| Independent UMB front end/reset/boot handling | Independent UMB front end/reset/boot handling |

This revises the previous single five-channel sensor-bus proposal: there are
still five probes, but the controllers own separate buses. Each firmware retains
the portable five-slot environment model. Air populates slots 0..3; Material
populates slot 4. Unsampled slots remain invalid. Sharing readings later would
need an explicit private controller link and stale-data/fault policy; it is not
implemented and must not be improvised as a second UMB master.

## Draft code layout and default behavior

- `examples/AirManagerBench/AirManagerBench.ino`: compile-time Air Manager role.
- `examples/MaterialStationBench/MaterialStationBench.ino`: compile-time MISP role.
- `src/Stm32BenchApp.h`: shared disabled operational bench entry point.
- `src/Stm32BenchConfig.h`: compile-time architecture/pin/configuration gates.
- `src/ShtSampler.h`: injected STM32 TwoWire bus, four mux probes or one direct probe.
- Portable protocol/control code stays shared; its multi-address router tests are
  fixture tests, not the selected one-IC architecture.

Library draft version is 0.2.0 and its Arduino architecture is `stm32`. Both
sketches start with no configured pins, no enabled role, UART transport off,
sensor sampling off, stock writes disabled, and no actuator outputs. The old
combined-role sketch is removed. Selecting both compile-time roles is an
error. Non-STM32 sketch builds and enabling peripherals without a reviewed board
configuration are also rejected.

## Board-specific build configuration

Use ST's [STM32duino core API](https://github.com/stm32duino/Arduino_Core_STM32/wiki/API)
or a later deliberate HAL/Cube port. Arduino framework selection does not
implement the S5 bootstrap. No specific core/toolchain version or real target
compile has been validated for these new sketches yet.

After checking the exact Nucleo schematic, ROM boot UART and alternate functions,
provide these macros through build flags or before the application header in the
role sketch. No real pin values are supplied as defaults:

| Macro | Meaning |
|---|---|
| `UMB_BOARD_CONFIGURED=1` | Explicitly acknowledges a reviewed per-board pin map |
| `UMB_ROLE_ENABLE_PIN` | Active-low role enable input; use uint32 STM32duino pin identifier |
| `UMB_ENABLE_TRANSPORT=1` | Isolated operational UART bench testing only; does not enable bootstrap |
| `UMB_UART_RX_PIN`, `UMB_UART_TX_PIN` | Pins belonging to the same appropriate USART; confirm ROM bootloader access separately |
| `UMB_ENABLE_SENSORS=1` | Enable role-local sampler after wiring review |
| `UMB_I2C_SDA_PIN`, `UMB_I2C_SCL_PIN` | Pins of one valid I2C peripheral with reviewed 3.3 V pullups |

The application constructs explicit `HardwareSerial(RX, TX)` and `TwoWire(SDA,
SCL)` objects using STM32duino APIs. It does not rely on a board's default
`Serial1`, debug UART or Wire pin map. ST-LINK SWD/NRST access must remain usable;
debug/VCP routing, BOOT configuration and oscillator pins must not conflict with
application pins. Reserve an appropriate timer channel for approximately 25 kHz
fan PWM and a separate input capture/interrupt for tach; those drivers are still
unimplemented. Do not assume a particular TIM number from the superseded pin plan.

Each isolated fixture uses manual address zero only. Never connect both fixture
images as addressed accessories on a real bus: negotiated chain addressing and
startup are not implemented. Genuine UMB discovery must eventually assign each
device its own address based on physical chain order. That order is not fixed by
the role sketches.

## Electrical and firmware integration gates

Use **3.3 V MCU-side logic**. Do not carry over 5 V GPIO, tach pullups or ADC
ranges. Confirm every STM32 pin's tolerance; do not treat all inputs as 5 V
tolerant. The fan may need a separate 5 V-compatible PWM interface, while its
open-collector tach should be conditioned for 3.3 V input. The 24 V motor rail
never connects to MCU logic. Board power inputs and USB backfeed protection need
their own reviewed design; a board's regulated 5 V input is not its MCU VDD.

The native UMB bootloader interface is STM32-based, but a Nucleo board alone does
not implement the observed BREAK/reset/chain circuit or accessory application.
The S5 host can erase/program stock firmware when its check differs. Therefore
two matching MCU families remove the dual-identity problem but do not resolve
custom-firmware ownership. Resolve that before printer connection; returning a
fabricated version or comparison block is not an implemented update strategy.

The exact startup helper, application-entry/trampoline contract, chain gating,
electrical transport, device update/recovery policy and real register behavior
remain required for **each controller individually**. Shared carrier construction
and the number of chips do not remove those requirements.

## Validation and next work

The local runner tests portable core behavior and reference packets, then syntax
checks both role sketches with stub APIs in disabled/configured modes. It also
checks rejection of unsupported architecture, unconfigured UART and simultaneous
roles. These checks do not validate STM32 headers/linker, bootloader, UART parity,
timers, interrupt behavior or physical outputs.

Next: review exact board schematics/pin mux, build both with a real STM32 core,
inspect flash/RAM/linker output, validate the saved startup helper against actual ROM behavior, capture genuine
accessory boot and chain traffic, and settle firmware update ownership. Then
bring up one isolated controller with inhibited outputs before adding the second.
