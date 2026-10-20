# Two-controller STM32 UMB draft

Offline research and original STM32duino/C++ code; not validated S5-compatible hardware.
Use two STM32 controllers, each with one fixed role: Air Manager or Material
Station. Each has its own active-low enable jumper. Stock discovery of these
roles is not implemented. Transport, outputs and
writes start disabled. Unsupported stock fields return unavailable, not fake healthy
values. No original accessory firmware or proprietary source snapshots are included.

See DESIGN.md, PROTOCOL.md, CONFIGURATION.md, HARDWARE_INVENTORY.md and TODO.md.
CONCEPTUAL_CONNECTIONS.md and connection_nodes.csv are proposed nets, not a stock
connector schematic. The catalog lists 95 source-observed register names; it is
not an exhaustive live accessory inventory. ObservedCatalog.h is checked in; the
private-source catalog extractor is intentionally excluded.

The Air controller has four chamber SHT45 probes through a TCA9548A; the Material
controller has one compartment probe on its separate bus. Tachometer feedback,
ten-point interpolated duty/RPM mappings,
and optional follow/trim/local temperature control. Defaults do not drive hardware.
STM32 is required because the observed stock host expects an STM32 bootloader
interface and distinct chip-ID/memory profiles for each accessory. Suggested bench
boards are NUCLEO-F072RB and NUCLEO-F303ZE. Matching families alone do not solve
startup or custom-firmware ownership. See [STM32 deployment](STM32_DEPLOYMENT.md)
and [startup/health requirements](../ACCESSORY_DISCOVERY_AND_HEALTH.md).

Run `python tools/run_tests.py` here with a native g++ C++11 compiler on PATH.
These are native protocol/model tests and stub Arduino syntax checks, not a real
STM32 build, memory/timer validation, motor test or printer-connected acceptance test.
Electrical standard, UMB bootstrap, monitor delimiter, physical fan drive, material
actuators, scaling and actual accessory compatibility remain unresolved.
