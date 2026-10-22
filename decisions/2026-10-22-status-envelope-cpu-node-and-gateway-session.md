# ADR — Status envelope, CPU nodes and the gateway status session

**Status:** Proposed (implementation exists as draft pull requests; the operator has not reviewed it)  
**Decision owner:** operator  
**Date:** 2026-10-22  
**Relationship:** records choices the implementation of
[`2026-10-22-status-ui-javascript-and-charts.md`](2026-10-22-status-ui-javascript-and-charts.md) had to make
and the spec did not settle. It approves nothing for production.

## Decisions proposed

1. **`iw.status/1` envelope.** One typed envelope per component (GPU node, CPU node, relay, gateway,
   external node), served at `GET /api/status` and `GET /api/status/stream`. A figure with no source is
   unknown and carries the reason; unknown is never served as `0`. Metric names are the closed vocabulary in
   the implementation contract.
2. **CPU nodes.** A node whose adverts are all `cpu` may register without a GPU. It states system memory
   (`system_memory_bytes`) instead of VRAM and negotiates the capability `iw.host-telemetry/1`; only then may
   its telemetry report omit the GPU read and carry host facts. GPU nodes' wire bytes are unchanged
   (golden fixtures). A gateway refuses a GPU-less report without the capability. An old gateway refuses a
   CPU node (found by reading the code, not by testing).
3. **Gateway browser sign-in.** The gateway's status API keeps its admin-secret header rule. Because a
   browser cannot send that header, `POST /api/status/session` exchanges the admin secret once for an
   in-memory, HttpOnly, SameSite=Strict session (8 h, capped, rate-limited) that opens the status API only.
   This is the one POST in an otherwise read-only surface; it writes only that in-memory table. The secret
   is never stored in the browser.
4. **External nodes.** Configured providers appear as `external_node` envelopes from an optional YAML list
   with no credential field (unknown fields are refused). They show declared models only; health,
   requests, errors and latency are unknown because nothing calls a provider.
5. **Mount points.** Node `/` (legacy page at `/details`), gateway `/`, relay `/status` (the relay console
   owns `/`). All serve the shared shell and `/assets/<name>`.

## Does not authorize

Production deployment of any role UI, exposure beyond loopback, provider API calls or credentials, spend or
balance display, removal of any Go behaviour, a CI browser step.

## Owed

Operator review of this record; independent review (gate BLOCKED); engine pid plumbing for RSS; a decision
on retiring legacy Go pages per `PARITY-MATRIX.md`.
