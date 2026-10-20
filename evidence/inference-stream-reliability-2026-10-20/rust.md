# Serving timeout implementation and canary

Implementation pin: `InferWeave/inferweave` revision
`70553036ae44fd7c570252ec8ccab19eb6440df4`.
The ordinary production Hive gateway was not replaced by this work.

## What is implemented

- Independent inference inactivity and execution policy (defaults 180/1800 s),
  validated positive whole-second environment settings, idle <= execution <=
  86400 s. Heartbeat freshness remains unchanged.
- Useful-output progress from content, reasoning and tool/function deltas,
  bounded incremental/multiline SSE parsing, and prefill allowance retained for
  metadata-only output. Execution remains independently bounded.
- Shared watcher wired into raw HTTP, legacy Link, HTTP Link and upstream Link.
  Raw HTTP request writing/header acquisition and bounded nonstream reads also
  observe the configured deadline. Dialing is separately bounded and clamped to
  the supplied ceiling; synchronous OS DNS resolution remains a limitation.
- Explicit `inference_idle_timeout` / `inference_request_timeout` error events
  and failed accounting. Gateway-owned HTTP chunk framing allows safe terminal
  timeout events while retaining detectable transport truncation.
- Admin-only, no-store `/iw/v1/inference/streams` and internal alias. Effective
  local settings, process-start timestamp, active/started attempts, finite
  path/phase/reason counters, fixed noncumulative timeout-elapsed buckets and 64
  bounded recent failures. Internal request and incoming correlation IDs remain
  distinct. `failure_coverage` explicitly limits these counters to local
  inference-deadline cutoffs, not every backend failure.

## Local evidence and limits

Observed RED before fixes: metadata followed by a delayed answer expired under
the short original idle policy; reasoning/tool-name progress was unrecognized;
trickled headers escaped cancellation. Those controls now pass regression tests.

Executed raw HTTP regressions include:

- `stream_metadata_preserves_prefill_allowance`
- `inference_timeout_inside_upstream_chunk_preserves_error_and_downstream_framing`
- `inference_truncated_backend_chunk_stays_a_transport_failure`
- `inference_decoding_preserves_complete_bodies_for_all_http_framings`
- `inference_steady_output_cannot_extend_execution_deadline`
- endpoint authentication, absent-admin refusal, pre-header and nonstream
  deadline accounting/cleanup in `tests/inference_streams_http.rs`
- meaningful-output/multiline parsing in `src/capture.rs` and
  `src/intelligence_usage.rs`
- virtual-time shared-watcher phase/deadline/bounded-statistics checks in
  `src/inference_stream.rs`
- `iw-core` upstream trickled-header and slow-writer cancellation tests.

`cargo fmt --all -- --check` and strict
`cargo clippy -p iw-gateway -p iw-core --lib --bins -- -D warnings` passed.
The complete library run used a dedicated local PostgreSQL cluster, rather than
silently skipping storage-dependent tests. Full integration results are recorded
below when the run is complete.

**Proof boundary:** real-socket timeout injection covers raw HTTP and the gateway
pre-header/nonstream pipeline. The shared watcher is tested for all four finite
path labels, and existing Link compatibility suites are exercised. There is no
new timed end-to-end failure-injection test proving every Link method. Do not
upgrade that remaining wire proof to proven merely from shared helper coverage.

## Binary-level canaries

The default synthetic smoke passed locally with the debug candidate: prefill
35.038 s, idle cutoff 1.051 s, execution cutoff 3.018 s, cancellation and
authenticated statistics, with zero active streams afterward. These are
synthetic elapsed times, not GPU throughput or a measured production envelope.

The pinned musl release artifact then passed the same smoke in Hive CPU job
`24958748` on `hive-as-11-2-38`, state COMPLETED, exit 0:0. Artifact identity,
resource declarations, exact results, logs and staging directory are in
[`rust-canary.json`](rust-canary.json). The 35.032 s metadata-only pause crosses
the former 30 s cutoff. Both short-policy timeout cases preserved distinct
causes; cancellation released the active stream. Credentials and outboxes were
generated privately by the harness and removed with its isolated processes.

No production traffic was sent to the canary. The temporary synthetic job has
finished. Production rollout/recovery and a comparable-traffic measurement remain
owed; a passing synthetic canary does not establish fleet recovery.

## Final verification result

The combined default `iw-gateway` run passed **2,879 distinct tests**, using the
full run, continuation and focused retries. `iw-core` upstream tests passed 8/8;
`iw-cli` LinkEngine tests passed 36/36. Strict core/gateway library/binary Clippy,
workspace formatting and diff checks passed. A dedicated native PostgreSQL16
cluster supported storage-dependent checks and was stopped/removed afterward.
No production databases or existing local databases were used.

Two test-run corrections remain visible in the record:

1. `link_http_startup` initially exhausted its existing 15-second readiness wait.
   Both tests passed on an unchanged exact retry (2/2, 4.49 s); the initial
   failure is retained rather than attributed to a proven cause.
2. `soak::a_silent_upstream_releases_its_seat_within_the_idle_bound` had set a
   two-second heartbeat TTL to obtain a two-second inference timeout. Test-only
   follow-up `de12bb70` uses the independent inference constructor and a
   30-second heartbeat, retaining its <10-second completion and released-seat
   assertions and adding the explicit timeout-code/no-DONE checks. All six soak
   checks passed, including its separately enabled PostgreSQL restart case.
   Product code and staged binaries remain exactly revision `70553036`.

**Additional limits:** three live GPU cases were not run. Two optional persistence
checks failed when explicitly enabled: an immediate fact query returned no row,
then repeated deterministic-request execution encountered duplicate attempt
accounting. Their baseline status was not established. Neither production
persistence code nor those assertions was changed to make them pass. These
failures are not part of the passing default suite and remain unresolved, not
proven unrelated to the change. Local logs are retained under
`/tmp/iw-stream-reliability-*.log`.

The CLI transport test build reported four unused-Result warnings in unchanged
`runtime_observation_report.rs`; the strict changed-core/gateway Clippy check is
clean. No claim of a warning-free complete CLI crate is made.
