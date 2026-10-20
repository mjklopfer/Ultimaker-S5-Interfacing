# Security and privacy

Run on a trusted workstation. The Cura listener is loopback/token protected;
the Node server is stdio-only. Do not expose the plugin port directly. The printer
origin must be supplied explicitly and cannot contain embedded credentials.

Keep generated connection files, OS credential stores, job/model files, logs,
device images and local client configuration outside version control. Generic
reads can return identifying printer/network data at runtime; redact them before
sharing. Diagnostic endpoint responses and client exception text can contain
local paths even though this repository contains none of the original paths.

Never paste a password, pairing key, bearer token or private SSH key into an
issue or chat. Use OS credential storage. The generic read tool is not a redactor
for arbitrary live printer responses. Pairing secret keys are suppressed by the
transport; caller/client logging still needs appropriate controls.

Human authorization belongs to the MCP client/operator. The bridge enforces
request/state-bound short-lived tokens and staging/busy guards, but does not
independently prove human approval. Do not automate away confirmation or print
busy-state checks. Run destructive/intrusive tests against mocks first.

For a vulnerability, use the repository platform's private security reporting
facility if available. Do not post operational credentials in a public report.
If a secret is exposed, revoke/rotate it before discussing non-secret diagnostics.

Before contributing, run the privacy scanner and a secret scanner on both files
and Git history. Use new dummy fixtures. Do not attach private deployment bundles
or real device snapshots to pull requests.
