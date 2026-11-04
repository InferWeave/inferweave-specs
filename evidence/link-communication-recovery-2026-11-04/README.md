# Link communication recovery — 2026-11-04

## Scope

Feature IDs: `IW-DP-001`, `IW-DP-002`; tasks `P1-T03`, `P1-T18`; specs 8,
47, and 59.

This evidence covers two communication defects: restoring a DNS-broken data route
from control-only evidence, and reporting every linked-stream failure as shared
connection loss. It does not qualify production rollout.

## DNS recovery defect

The Rust gateway withdrew a node after its endpoint failed DNS resolution before
dispatch, then restored the same unchanged route on the node's next heartbeat.
The heartbeat proved control liveness but supplied no evidence that the endpoint
resolved. Requests could therefore select and withdraw the same broken route
repeatedly.

The implementation now retains a distinct endpoint-unresolvable withdrawal across
heartbeats. A fresh registration clears it under the existing new-incarnation
policy. An accepted authenticated held Link clears only that DNS reason because it
provides another data path; an invalid credential clears nothing, and leaving,
released, and distrusted reasons remain authoritative. Real HTTP registration,
chat, heartbeat, and Link-upgrade tests reproduced the old restoration and cover
all three recovery boundaries.

Review additionally exposed a stale-result race: Link acceptance or registration
could finish before a pending DNS failure was applied. The repaired router
captures the existing registration incarnation or controller snapshot version
before dialing, then atomically checks it and current held-Link state when
withdrawing. Three reverse-order regressions fail without this guard; all seven
DNS tests pass with it. Heartbeats do not rotate the marker. The complete selected
gateway routing/Link suite passes 129 tests.

## Stream attribution defect

The Go edge treated every non-EOF `Stream.Next` error as a Link cut. Credit-window
overrun, sequence violation, and per-stream idle timeout could therefore produce
“Connection lost” while the shared socket remained healthy. Legacy socket EOF
before End could also appear as clean completion.

The implementation retains typed local causes and maps only a shared-socket cause
to connection-loss wording. Operator diagnostics use the bounded labels
`link_credit_exceeded`, `link_sequence_error`, `link_stream_idle_timeout`, and
`link_connection_lost`; unknown causes remain `upstream_transport_failure`. Raw
errors are not labels or public content. The public `upstream_transport_error`
code, retry metadata, request-state and replay-safety fields remain unchanged.
EOF before End is incomplete in both legacy and HTTP modes.

## Proof boundary

The implementation tests are deterministic local evidence. They prove recovery
state transitions, bad-credential refusal, stronger-withdrawal retention,
stream-local failure classification, shared-socket classification, and incomplete
legacy EOF handling. They do not prove deployed mixed-version behavior, sustained
traffic, post-repair DNS propagation, production diagnostic retention, or an
improved error rate. Those remain **owed**.

The focused specification check passes:

```text
python3 -m unittest discover -s tests/smoke -p 'test_link_http_json.py'
```

After integrating onto current main (`f32bfe0`), 14 focused smoke tests pass.
`git diff --check` and the repository-wide
`python3 scripts/validate_specs.py --self-test` also pass: 106 features, 172
canonical tasks, a valid DAG, and all 12 registry/7 file mutation guards reject
their known-bad inputs. Task cards, canonical task data, the implementation
sequence, bundle inventory and checksums are synchronized. This replaces the
initial older-base schema-resolution validation gap; production qualification
remains owed.
