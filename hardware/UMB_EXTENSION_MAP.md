# UMB device families and extension map

Reference: captured S5 R1 host firmware 9.0.3.0. This is an interface map, not a
live attached-device inventory or a promise that arbitrary accessories work.

## Recognized configuration families

| Configuration entry | Meaning established by captures | Limits |
|---|---|---|
| `airmanager` | Air Manager family; service `airmanager@{id}.service`; chip profile 0x0448 | Host profile; physical replacement acceptance untested |
| `airmanager-r2` | Another Air Manager type routed to the same service | Separate MCU config file was listed; its contents and exact revision differences remain unreviewed |
| `misp` | Material Station family; service `misp@{id}.service`; chip profile 0x0446 | Host profile; physical replacement acceptance untested |
| `umbus.debug` | Debug mapping file listed; generic debug implementation captured | Exact mapping contents unreviewed; not evidence of another commercial accessory |

No additional shipping accessory family was found in this saved configuration
listing. This is bounded to the captured installation, not the entire UltiMaker
product line. The MCU/device/service configuration is how Linux recognizes and
launches a type; operational register names alone do not create a supported role.

## Generic UMB operational contract

| Command | Payload/function | Extension use |
|---|---|---|
| 0x00 | First/next register index; empty initial request, previous index on subsequent requests; returned 0x0000 ends traversal | Discover new fields without hardcoded indices |
| 0x01 | Register name for discovered index | Name original fields in a separate namespace |
| 0x02 | Read register by index | Telemetry, identity, health and configuration readback |
| 0x03 | Write ASCII value; length, NUL-terminated value and index layout | Requests accepted by a real backend; permissions/types still need definition |
| 0x10 | Enable register monitoring | Subscribe to changes |
| 0x11 | Disable register monitoring | Remove subscription |
| 0x1F | Poll monitored updates | Gather changed values; wire delimiter remains unresolved |

These are operational commands, not startup enumeration commands. The packet
structure is independent of whether the register represents a fan, probe or
feeder. It does not supply a standard universal temperature/motor/accessory
class. Naming, units, data validity, command completion and fault semantics must
be designed and consumed explicitly. A writable D-Bus property is not proof that
every accessory register accepts writes.

## Linux-side endpoint structure

| Layer | Source-observed endpoint | Purpose |
|---|---|---|
| Bus | System D-Bus `nl.ultimaker.UMBus1`, root `/nl/ultimaker/UMBus1` | Publishes discovered devices |
| Device | `/nl/ultimaker/UMBus1/{device}`, interface `nl.ultimaker.UMBus1.device` | `id`, `type`, `service` properties |
| Device methods | `getAllRegisters`, `startMonitoringAllRegisters`, `stopMonitoringAllRegisters` | Register snapshot and subscription control |
| Device signal | `PropertyValueChanged` | Register change notifications |
| Register | `nl.ultimaker.UMBus1.register` with `name`, `value`, `monitor` | Generic register interface; dots in names map to path separators |
| Air service | `nl.ultimaker.airmanager1` | Airflow, fan/filter/temperature and heartbeat consumer |
| Material service | `nl.ultimaker.MISP1` | Material/bay/dryer/door/NFC consumer |
| Developer TCP service | Port formula `42000 + device descriptor` in the inspected implementation | Initial register name/value pairs, monitored updates, `name=value` writes |

The debug implementation binds all IPv4 interfaces when launched. That is a
source-observed bind rule, not a claim that a listener is enabled or reachable on
any printer. It is separate from SSH and MCP authentication/confirmation. Do not
enable it as a default deployment path. Connecting also enables monitoring, so
it is not a completely side-effect-free snapshot. No debug connection or write
was performed for this review. The service loader supports developer-only gates;
the complete debug mapping and its particular gate remain to inspect.

## Hypothetical original accessories

| Proposed function | Register approach | Additional host work |
|---|---|---|
| Chamber probe array | Existing draft `custom.chamberTemperature.0..3`, `custom.chamberHumidity.0..3` | Logger/UI/API consumer; define probe locations and invalid/stale semantics |
| Material environment | Existing draft `custom.materialTemperature.0`, `custom.materialHumidity.0` | Consume the Material controller's local sample; remote slots remain invalid |
| Probe freshness | Existing draft `custom.sensorValid.0..4`, `custom.sensorAgeMs.0..4` | Respect validity/age; no fabricated default measurements |
| Filter pressure / airflow / VOC probes | New original register names and explicit units | Sensors, calibration, backend and application consumer; not stock-supported fields |
| Lighting / cabinet interlocks | New request/state/fault fields | External drivers and deliberate host policy; no new automatic safety enforcement is implied |
| Original dryer / selector / feeder module | Command plus asynchronous state/fault feedback | Hardware state machines and new Linux integration, or proven compatible stock semantics |

Only the first three rows have register names modeled by the current draft.
The remaining rows are concepts, not discovered stock registers or implemented
MCP endpoints. An environmental sensor does not implement stock drying behavior.

## New device versus extending a known role

Adding fields to an already recognized replacement role can reuse dynamic
register discovery, but a host service still has to consume them. A completely
new accessory type additionally needs a settled identity/firmware/startup contract
and device-to-service configuration. New HTTP/MCP tools or touchscreen views do
not appear automatically. Keep experiments off the operating printer until the
native startup and update behavior are understood.

The generic debug and fake-device hooks are useful subjects for isolated Linux
development; they are not demonstrated stock deployment bypasses. This project
uses two STM32 controllers with fixed Air and Material roles. Other accessory
roles and host modifications are separate research work.

See [startup and health](ACCESSORY_DISCOVERY_AND_HEALTH.md),
[stock register catalog](umb-controller/endpoint_catalog.json), and
[STM32 development plan](umb-controller/STM32_DEPLOYMENT.md).
