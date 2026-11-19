# Recording outcomes v1

The frozen data is [recording-outcomes-v1.json](../../contracts/recording-outcomes-v1.json),
for IW-PROMPT-001/spec22. These are bounded recorder metrics and sink outcomes;
they are not inference errors, execution authority or durable acknowledgements.
The contract is vendored/pinned by implementations and reconciled by tests,
never fetched at runtime. Changes require a reviewed version/decision update.

## Known-loss reasons

`iw_recording_losses_total{reason="..."}` counts an event exactly once when it
is known not committed through this recorder. It includes producer rejection
before enqueue and never-dispatched queued casualties. Previously uncertain
in-flight work is classified separately, even after a later permanent refusal.

| Reason | Meaning |
| --- | --- |
| `full` | Count-bounded queue rejected newest event. |
| `byte_budget` | Shared encoded-byte reservation could not fit newest event. |
| `oversize` | One event exceeded the configured event bound. |
| `closed` | Producer channel closed, or a never-dispatched queued event was abandoned. |
| `encoding` | Encoding/sealing failed before any sink dispatch. |
| `entropy_unavailable` | Prepared one-use entropy was unavailable. |
| `contention` | Nonblocking producer lock/reservation contention refused the event. |
| `discard` | Explicit discard policy or orderly abandonment before dispatch. |
| `disk_budget` | File space could not be proven within the configured policy before dispatch. |
| `missing_parent` | A supported dependent event has no committed parent. |
| `unsupported` | Configured sink does not implement the event, including PG response capture. |
| `invalid` | Event failed the sink's static structural/identity validation. |
| `conflict` | Existing semantic receipt or unproven legacy natural row conflicts. |

## Unknown-outcome reasons

`iw_recording_sink_outcome_unknown_total{reason="..."}` counts terminal events
whose sink commit cannot be determined. These are neither known losses nor
acknowledged commits; do not add them to either counter. Actual crash loss is
also unknown, independently of the configured retained-buffer upper bound.

| Reason | Meaning |
| --- | --- |
| `worker_termination` | Sink worker terminated with a dispatched event unacknowledged. |
| `shutdown` | Shutdown abandoned work with an unresolved dispatch. |
| `invalid_sink_result` | Sink returned an invalid per-event outcome shape after dispatch. |
| `refusal_after_uncertain_retry` | A later permanent refusal cannot resolve a prior uncertain write. |

## Health states

`iw_recording_health` describes recorder progress; ordinary serving health remains independent.
Successful later acknowledgement may restore healthy state without resetting
historical counters. Per-process counters reset on process restart; historical
absence is never a claim of zero lifetime loss.

| State | Meaning |
| --- | --- |
| `healthy` | No current retained retry or newer failure after the last successful progress. |
| `delayed` | A retained batch is awaiting bounded retry without newer dropping state. |
| `dropping` | Explicit discard or newer known/unknown recording failure is observed. |

## Sink results

| Result | Meaning |
| --- | --- |
| `committed` | Sink acknowledged the exact semantic event or its identical prior receipt. |
| `permanent_loss` | Current attempt cannot commit; earlier uncertain writes still require unknown classification. |
| `unresolved` | Retry only this event, preserving identity, ciphertext and byte reservation. |

## Resource policy

The JSON defaults are operator-selected policy, not hardware measurements.
All numeric limits are finite positive integers, except `disk_max_bytes` and
`disk_scan_limit`: they default to `null` (unset), meaning no disk budget, and
are positive integers only when an operator sets them. A set budget counts only
the sink's own `recording-*.jsonl` files; zero is still invalid. Queued count may be lowered
from 8192 and batch count from 128, but neither may be raised. Reject count
limits above these ceilings (including platform-sized maximum integers) before
allocating channels or starting workers. Configured crash-loss count bounds
are queue plus batch, never above 8320; this is not actual known crash loss. Require event bytes ≤ batch
bytes ≤ total shared encoded bytes, and initial retry delay ≤ maximum delay.
Zero or inconsistent limits are a static configuration error, even in discard
mode. One reservation remains held through queued, in-flight, retained and
retry ownership and is released exactly once at terminal classification.
The defaults bound encoded retained recording data, not total process RSS or
request/response buffers. No acknowledged durable record is auto-deleted.

The entropy reservoir is independent of a lowered event-queue capacity:8191
queued prepared objects plus at most one preparing/sending object,8192 total.
Each holds64 raw entropy bytes; these are software limits, not total RSS claims.
The `entropy_prepared` snapshot count includes that pending-send object and is
not a readiness or immediate-pop guarantee. Serial N-offer fixtures must use a
controlled barrier for at least N+1 preparations, never infer readiness from a
single prepared object or arbitrary sleep. Discard creates no entropy refiller.
