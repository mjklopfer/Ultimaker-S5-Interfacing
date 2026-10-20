# Public release sanitization

This public repository was assembled from an explicit source-file allowlist in
a new Git repository. It does not inherit the development workspace's history.
Commit author identity is a neutral project identity; publication under the
repository owner's account is deliberate.

Included: original bridge/plugin/tests, structural API interface inventories,
original controller code/design, general device mapping notes and public source
links. Interface examples/vendor prose were removed from schemas. A configured
printer origin is required; job metadata uses a generic owner label.

Excluded: credentials and credential stores, workstation/server paths and names,
network addresses and wireless identifiers, serial/MAC/device IDs, real job UUIDs,
delivery/account records, print projects, binary archives/images, service dumps,
raw inventories/logs, proprietary implementation source and historical commits.
Public hardware notes retain reusable model identifiers, generic operating-system
device paths and register/pin mappings; these are technical interfaces rather
than identifiers of a particular printer.

The release gate uses a reusable privacy pattern checker, a separate private
identifier comparison, a redacting secret scanner, file allowlisting, and a scan
of the freshly created Git history. The private identifier list is not shipped.
Known test fixtures use loopback and dummy secrets only. Reports publish aggregate
results, never matched secret values or private paths. Scan success is a bounded
review result, not a claim that future contributions cannot introduce sensitive data.
