# Native physical-work lifetime counterexamples

Feature/task scope: `IW-RT-001` / `B-T01`, and `IW-CAP-001`, `IW-BP-001` /
`P1-T12`. Baseline runs 9918 and 9921 are **RED**. Candidate run 9923 proves one bounded
private physical-retirement control; broader candidate and deployed/native
production qualification remain **owed**.

These private CPU qualification observations occurred November 11 Pacific /
November 12 UTC. This change independently reread the original `evidence.jsonl`
and `artifact-provenance.json` receipts over the existing verified normal-user
SSH route, extracted only the allowlisted metadata below, and hashed the exact
original byte snapshots. It did not rerun inference or mutate a runtime.
The originals remain in the operator-private receipt sets identified in
[red-receipts.json](red-receipts.json). No request/state/question text, answers,
authentication data, private error bodies or network addresses are included.

## Pinned baseline

Both receipts identify Core source
`e79730300fe59670f44ce86babf85a7956454be0`, binary SHA256
`4071d0e1f12f452cb76aa196513cc319c936cdb0cfa646b25d432104e0a311ed`.
The Go binary SHA256 is
`be624fa23f6d58c48d8455304d4da995a99b38380f098d569eae7bfd416141b5`;
the runtime image SHA256 is
`d425cc857105686acdc47760f29884ae2579000f2272f6d2a60f5a8d34843d28`.
The observed native policy fingerprint is
`4e7c3e4f54df4f530f9df35a32baa845e3067f57bcd4075e69dede12632ab0e5`.
The contract's unchanged Laya0.4.8 package/checkpoint pins remain the source of
input-envelope policy, not proof of cancellation or runtime serviceability.

## Run 9918: deadline and delayed same-incarnation recovery

At `2026-11-12T00:41:02.363057+00:00`, the harness-labelled maximum-shape
single-state decision returned HTTP503 after **180.062 s**, code
`system_one.native_pool_unavailable`. The receipt records a 180 s configured
worker budget and state size 50,000 characters. The private harness used the
existing legal question/state boundary; no raw input is published here.
A following normal-route decision returned HTTP200 after **98.919 s**.
The receipt explicitly records the same pool and registration generation.

This is a timeout/recovery counterexample, not by itself proof of which forward
pass occupied the backend throughout the interval. It does not qualify the
maximum envelope, establish an SLA, or justify extending a request deadline.
The original error was also not classified as a named worker/route timeout.

## Run 9921: fresh zero report while work remained unacknowledged

This was a controlled private failure probe with a **15 s** worker budget,
not a production timeout-profile change. The caller returned HTTP503 after
**15.154 s**. At `2026-11-12T01:51:29.074110+00:00`, the original harness recorded
`RED_unacknowledged_work_reported_free`: worker-reported units **0** and child
holds **0**, with source age **20 ms**, while the tracked old process still
consumed CPU (**322 raw clock ticks** in the observation interval). The process
anchor was PID `1932813`, start ticks `312458291`.

CPU activity corroborates remaining work; it is not a completion receipt or a
throughput measurement. No conversion from clock ticks to time/utilization is
claimed. The decisive failure is treating caller/transport termination as enough
to publish physical work as free without an authoritative completion or checked
owned-process exit. A healthy probe cannot supply that missing receipt.

## Defect and required proof

The prior specification said a batch reserved its units "until
completion/cancellation", without distinguishing a caller reservation from a
physical work permit. Following that text literally could reproduce the observed
zero counter. Spec48 now requires queued/active ownership independent of caller
lifetime, exact-incarnation checked retirement, and retained debt plus quarantine
when execution is unconfirmed. Ambiguous post-write failure cannot replay
inference on another connection or runtime.

The new contract checks prove only that this vocabulary, the unchanged wire
members, state-unit cost and clipped routing formula remain consistent. They
cannot prove a backend stopped. Broader candidate batch/disconnect cancellation, failed termination, no-replay,
old-incarnation isolation, healthy siblings across target placements, full
workload, RAM and soak results remain **owed**; the bounded case below has a
separate, narrower proof scope.


## Run 9923: bounded private physical-retirement control

**Proven only for this private 15 s timeout probe.** The original receipt set
[bounded-green-receipt.json](bounded-green-receipt.json) was independently reread
and sanitized by the same method; its source is Core
`6f28cb9ce7971d596f0aba3eb47777bf472984bf`, binary SHA256
`d1cea9fa441bd67bedf31fb0ec1660f00f9d299e045f8854f07c41f6091ff9bb`.
The Go binary is unchanged from the RED baseline. The candidate runtime image
SHA256 is `76c17a10ff57310eb2f1a41d836d3543ec4db5ca4664cd616a88579a508cebf2`.

The caller returned HTTP503 after **15.104 s**. The owned old process, PID
`1945774` / start ticks `312641944`, exited at **20.689 s**. The private worker
log contains a confirmed SIGKILL/signal9 exit receipt; only those marker facts
and the original log digest are retained, never its raw messages. The harness
did not accept a fresh free-capacity claim while that old work lacked a receipt.
A replacement process, PID `1946069` / start ticks `312648441`, loaded and became
actually ready; a new accepted observation reported concurrency **16**. A real
normal-route request returned HTTP200 after **0.556 s**, recorded at
`2026-11-12T02:22:44.682242+00:00`.

This RED-to-GREEN pair establishes the bounded private timeout-to-checked-exit
control against the earlier zero-counter failure. It does not establish all
batch/disconnect/shared-pool cases, the production 180 s profile's maximum-shape
performance, RAM, sustained load, unaffected production siblings or a production
rollout. Those proofs remain **owed**. A legal input envelope is not an SLA.
