# ADR — Gateway history store, network views and the Slurm view

**Status:** Accepted for implementation (operator, 2026-10-22)  
**Decision owner:** operator  
**Date:** 2026-10-22  
**Relationship:** extends [`2026-10-22-status-ui-javascript-and-charts.md`](2026-10-22-status-ui-javascript-and-charts.md)
and [`2026-10-22-status-envelope-cpu-node-and-gateway-session.md`](2026-10-22-status-envelope-cpu-node-and-gateway-session.md).
**Supersedes** the 2026-09-17 working decision that gateway telemetry stays in files rather than a database, for the
optional history store below only.

## Operator statement (2026-10-22)

Page shape collapsed as in the legacy console; per-user usage is shown (the username, or when none exists a masked
email of the form `ab***@*****.*`); status data comes from recorders on the proxy path, with no active probe of an
external node; an external node has its own page; history is kept until deleted and rolled up so it does not grow
without bound; a database is acceptable for the gateway; every network and model map is visible on the gateway page;
whatever the Go gateway persists is persisted by the Rust gateway when the feature is enabled, and the feature is
optional so several gateways do not duplicate data; the Go gateway is going away, so admin functions and optional
identity connectors (Cognito, OAuth) follow; the Slurm view is wanted, and a gateway on a cluster may call `squeue`
and the like for the nodes and jobs it spawned; scaling activity is communicated upstream between gateways and
visualised per gateway. For the local deployment the history home is the zapp gateway; other sites choose their own.

## Decisions

1. **History store (optional, off by default).** A `history:` section of the gateway YAML (no environment
   variables). The database connection comes from a secret file, never inline. One gateway is the **history home**;
   other gateways stream facts to it over the existing gateway link. Every fact carries `(gateway id, sequence)` and
   writes are idempotent, so a retry or a second enabled gateway never duplicates a row.
2. **What is stored (content-free, always).** Per-request facts (model, node, GPU, Slurm job, outcomes, timings,
   token counts); usage rollups by model, day, user and key; model-intelligence observations and incidents; GPU-memory
   and placement snapshots and the residency timeline; topology snapshots; model availability transitions;
   external-node counters; Slurm job lifecycle; scaling intent and outcome. Prompts, responses and any request body
   are never stored by this feature.
3. **Retention is forever until deleted, with rollups.** Raw rows are kept for a configurable raw window
   (default 30 days, `history.raw_days`), then rolled up (minute, hour, day, month) and the raw rows are dropped;
   rollups are kept until an operator deletes them. Tables are partitioned by month. The gateway page shows the store
   size and growth. Deletion is an explicit admin action (CLI or admin API) by time range, model, user or all, with a
   confirmation and an audit row; the read-only status pages never delete.
4. **Identity in the store.** The store holds a display label chosen at write time: the username when the identity
   provider supplies one (Cognito supplies one), otherwise the masked email. Raw emails are not written to the status
   database. A local login without a username shows the masked email.
5. **Three data planes.** Live status (`iw.status/1`), history (`GET /api/status/history`, served from the store), and
   typed maps and tables (topology, model map, rankings, histograms) as siblings of the envelope. The metric envelope
   stays small and generic.
6. **External node.** A standalone page per gateway listing its providers: declared models, link state and breaker,
   and request, error and latency figures recorded on the proxy path. No active probe, no credential, no peer poller.
   Health is "no traffic yet" or "last seen", never "healthy" from configuration alone.
7. **Slurm view (optional).** A page of nodes and jobs the gateway spawned: job id, partition, state, time left,
   preemption and requeue history, and pool desired versus pending versus ready. The gateway reads Slurm with
   `squeue` and `sacct` no more often than once a minute (the UC Davis rules in the `ucd-hpc` skill apply). A node
   also reports its own job id and walltime. Scaling intent (desired, pending, ready, waiting for nodes) is reported to
   the parent gateway and shown per gateway.
8. **Identity connectors and admin.** The Go gateway's administration (aliases, keys, usage administration,
   provisioning, approvals) and sign-in move to Rust in later phases, with optional generic OIDC/OAuth connectors
   (Cognito among them) configured in YAML; credentials only by file reference. Until each admin page exists in Rust,
   Go stays authoritative for it.
9. **Order of work.** (1) relay richness and the external node page from live data; (2) the history store with usage
   by model, day and user; (3) topology and model maps; (4) reliability and residency; (5) the Slurm view and upstream
   scaling signals; (6) admin and identity connectors.

## Does not authorize

Storing prompt or response content; provider API calls or credentials; exposure beyond loopback without the
authentication work of decision 8; removal of the Go gateway before parity of decision 8; a deployment of any of this.
`OPEN_GATES.md` stays as written until each piece is proven.

## Owed

The schema and its migration tests; a measured storage growth figure under real traffic; the Cognito claim mapping;
the scaling-signal wire format; independent review.
