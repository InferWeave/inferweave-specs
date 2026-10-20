# Carry normalized telemetry through a private authenticated HTTP boundary

Status: additive contract within the operator-approved observability scope;
independent review required before integration. Runtime and deployment proof owed.

The normalized event/rollup/failure contracts define internal data but no HTTP
carrier. An implementation otherwise has to invent producer authorization,
pre-buffer size limits, durable acknowledgements and read consistency. The Rust
HTTP parser currently has a generic 16 MiB body limit and a first-value header map;
reusing those defaults without route-specific checks would violate the 64 KiB
normalized-event bound and make duplicate credentials ambiguous. This is a
specification gap identified from source inspection, not a production incident.

Add one single-event POST and two operator-only GETs under
`/iw/v1/observability/`, defined by `contracts/private-observability.json` and
`openapi/private-observability.{yaml,md}`. Reuse current registered gateway-node
credentials for external producers and existing admin credentials for reads.
Source identity, retained authorized epochs and lineage derive from server state;
claims in a normalized event cannot grant authority. Local publishers use an
internal trusted path. Durable outboxes retain identities until durable ACK;
independent capture/loss accounting is required for complete coverage.

Read envelopes carry validated internal diagnostics or atomic exact
parent/failure bundles with bounded snapshot pagination, query health and explicit
unavailable companions. They do not change frozen v1 data objects. Reject batch
ingestion initially: a single 64 KiB event avoids introducing another buffering,
partial-acceptance or retry contract. Reject a public serializer or caller-supplied
cohort/coverage inputs. Reject inferring complete coverage from accepted rows.

All routes default disabled. Production collection additionally depends on the
paired rollup generator and persistent sealing/watermark fence, not merely event
storage. Existing Rust global authority, Go own-edge scope, 7/90-day new-family
retention and unchanged legacy 730/365-day retention remain binding. No new
production target, public release, retention migration or deployment gate opens.

Traceability: IW-OBS-001/IW-TEL-001/IW-BENCH-002, P1-T20/P2-T03,
AC-PRIVATEOBS-01..06; offline executable contract checks prove only their local
assertions. Runtime parser, auth-race, database durability, outbox restart,
snapshot concurrency and independent coverage tests remain owed in OPEN_GATES.
