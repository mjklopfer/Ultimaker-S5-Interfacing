# UMB replacement-controller draft

Offline research and original Arduino/C++ code; not validated S5-compatible hardware.
The printer remains host. An accessory peripheral may expose Air Manager, Material
Station, both or neither using two boot-time jumper inputs. Transport, outputs and
writes start disabled. Unsupported stock fields return unavailable, not fake healthy
values. No original accessory firmware or proprietary source snapshots are included.

See DESIGN.md, PROTOCOL.md, CONFIGURATION.md, HARDWARE_INVENTORY.md and TODO.md.
CONCEPTUAL_CONNECTIONS.md and connection_nodes.csv are proposed nets, not a stock
connector schematic. The catalog lists 95 source-observed register names; it is
not an exhaustive live accessory inventory. ObservedCatalog.h is checked in; the
private-source catalog extractor is intentionally excluded.

The design includes four chamber SHT45 probes and one material-compartment probe
through a TCA9548A, tachometer feedback, ten-point interpolated duty/RPM mappings,
and optional follow/trim/local temperature control. Defaults do not drive hardware.
Mega 2560 is provisional; a Mini-class board is constrained for the combined role.

Run `python tools/run_tests.py` here with a native g++ C++11 compiler on PATH.
These are native protocol/model tests and stub Arduino syntax checks, not a real
AVR build, memory/timer validation, motor test or printer-connected acceptance test.
Electrical standard, UMB bootstrap, monitor delimiter, physical fan drive, material
actuators, scaling and actual accessory compatibility remain unresolved.
