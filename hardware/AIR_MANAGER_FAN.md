# Air Manager fan identification: likely family, unconfirmed exact model

## Evidence and confidence

The manufacturer's [S5 Air Manager fan replacement manual](https://um-support-files.ultimaker.com/manuals/repair-calibration/S-series/Repair-manual-Air-Manager-fan2.pdf),
pages 3-4, shows a Noctua fan with brown corner pads, a four-wire cable and an
IP67 marking. The frame and rear guide-vane layout appear consistent with the
120 mm NF-F12 industrialPPC family. **This family identification is an inference
from photographs, not a readable complete model label or a manufacturer BOM.**
The exact speed variant, voltage/current label and OEM customization remain
unconfirmed. The illustrated batch marking is not a model number; no unit or
batch identifiers are reproduced here.

The [S5 Air Manager user manual](https://um-support-files.ultimaker.com/manuals/user-manual/S5-Air-Manager/Ultimaker%20S5%20Air%20Manager%20-%20User%20manual%20ENv2.2.pdf),
specifications section, explicitly gives the accessory UMB power/data connection
as 24 VDC. This establishes the accessory's nominal supply, **not individual UMB
contacts or the voltage delivered by its PCB to the fan**.

## Catalog candidates, not confirmed stock equivalents

Noctua currently lists the following relevant retail variants. The current `SP`
suffix is not established for the older fan in the UltiMaker manual; do not assume
the current retail product and the installed OEM fan are electrically identical.

| Specification | [NF-F12 industrialPPC-24V-2000 SP IP67 PWM](https://www.noctua.at/en/products/nf-f12-industrialppc-24v-2000-sp-ip67-pwm/specifications) | [NF-F12 industrialPPC-24V-3000 SP IP67 PWM](https://www.noctua.at/en/products/nf-f12-industrialppc-24v-3000-sp-ip67-pwm/specifications) |
|---|---|---|
| Dimensions without pads | 120 x 120 x 25 mm | 120 x 120 x 25 mm |
| Mounting-hole spacing | 105 x 105 mm | 105 x 105 mm |
| Rated supply | 24 V | 24 V |
| Maximum nominal speed | 2000 RPM | 3000 RPM |
| Maximum catalog input current | 0.07 A | 0.18 A |
| Maximum catalog input power | 1.68 W | 4.32 W |
| Interface | Four-pin PWM + tach | Four-pin PWM + tach |

These catalog values are comparison data, not measured stock fan ratings or a
basis for final fuse/driver sizing. The published free-air flow must not be
equated to flow through the assembled Air Manager filter/housing.

## Control and tach reference

The [Noctua PWM white paper](https://cdn.noctua.at/media/Noctua_PWM_specifications_white_paper.pdf)
specifies a 25 kHz PWM target (21-28 kHz acceptable), separate from motor supply.
Tach output is open collector, two pulses per revolution, with a 2 mA sink-current
limit for 24 V fans. PWM maximum is 5.25 V; do not apply the motor rail to PWM.
Noctua recommends CMOS-type PWM drive and does not recommend open-collector PWM
drive. Tach conditioning to STM32 3.3 V and PWM driver behavior need circuit review.

The candidate retail pin assignments are black ground, yellow supply, green RPM
and blue PWM. These are **fan connector reference assignments**, not the UMB
connector pinout or proof of the OEM harness/header orientation. Verify continuity
before using a connector drawing as a wiring plan.

## Remaining identification work

Read the complete fan hub label: model string, rated voltage/current and any OEM
suffix. Measure frame dimensions and connector orientation. Verify fan-header
supply and control/tach behavior on the actual PCB using a planned bench test.
Retain the two retail variants as candidates until that evidence exists; do not
silently select a 2000/3000 RPM rating in firmware or claim a drop-in replacement.

The current STM32 node plan remains symbolic. No wiring, firmware changes or live
fan tests were performed for this identification review.
