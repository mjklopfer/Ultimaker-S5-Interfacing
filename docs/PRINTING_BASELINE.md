# Observed Nylon printing baseline

A user reported improved build-surface adhesion during a small extruder-2 print
on an S5 R1. A read-only local job query associated the observation with the tuned
file at approximately 40% progress. This is a mid-print observation, not a
completed-part, repeatability or general material-profile validation result.

| Setting | Observed baseline |
|---|---|
| Core / material | Extruder 2, AA 0.25, black Nylon |
| Main / outer wall speed | 63 / 18 mm/s |
| Inner wall / top-bottom speed | 27 / 27 mm/s |
| First-layer / travel speed | 9 / 135 mm/s |
| Speed adjustment | Saved speeds scaled to 90% of the preceding profile |
| General flow | 115%, with subordinate values scaled while preserving profile ratios |
| Skin flow | 109.25% |
| Initial outer / inner wall flow | 126.5% / 109.25% |
| Nozzle / bed target | 230 / 40 degrees C |
| Layer / initial layer height | 0.1 / 0.2 mm |
| Infill / adhesion setting | 40% / brim |

The reduced speeds and increased flow are already in the sliced configuration;
they are not instructions to apply additional printer multipliers. The job query
did not expose live speed/flow overrides. Surface preparation, adhesive, drying
and ambient conditions were not recorded. Completion, warping, dimensions,
function and cooled-part removal remain follow-up observations.

An external MCP connector probe returned HTTP 429 during the observation, while
a direct local read-only HTTP query succeeded. That does not establish the
printer or Cura as the source of throttling. See the investigation task in
[known issues](KNOWN_ISSUES.md). No write or print interruption was performed.
