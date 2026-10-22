# Private gateway attempt metrics

IW-OBS-001 / IW-TEL-001: `GET /internal/requests/metrics` exposes process-local
observations of terminal **admitted execution attempts**, not logical requests,
users, task correctness or complete fleet traffic. It requires the existing
`secrets.metrics_token_file` as a Bearer credential. No token configured returns 404;
missing/wrong credentials return 401; authenticated non-GET returns 405. The
public `/iw/metrics` remains unchanged. This does not enable the default-off
private warehouse carrier or any public/cohort projection.

The measurement seam is `Gateway::record_intelligence_completion`, before its
bounded best-effort persistence recorder. The accumulator does no storage or
network I/O. A failed/unsupported ledger cannot suppress these observations.
Only paths reaching that seam count: early authentication/admission refusals,
remote/direct-node requests not observed by this gateway, and crash-lost terminal
observations are excluded. Each retry observed locally is another attempt.
Counters reset with the Gateway instance; scrape the start-time gauge. Scrapes
are observations, not durable replay or exactly-once warehouse history.

| Metric | Semantics |
| --- | --- |
| `inferweave_gateway_attempts_total{model,outcome}` | Local terminal attempt transport outcomes. `completed` is not proof of inference success. |
| `inferweave_gateway_attempt_duration_seconds` | True cumulative histogram of monotonic dispatch-to-terminal time, excluding queue wait; model dimension. |
| `inferweave_gateway_attempt_invalid_duration_total{model}` | Invalid/nonfinite/negative durations excluded from histogram. |
| `inferweave_gateway_attempt_reported_tokens_total{model,direction}` | Provider-reported total input or output tokens only. Totals/subsets are never added together. Absent until a reported observation exists; reported zero is zero. |
| `inferweave_gateway_attempt_usage_observations_total{model,direction,basis}` | Coverage counts: `reported`, `estimated`, `missing`, `unsupported`, `invalid`. Absent/invalid raw usage stays missing at the capture boundary. |
| `inferweave_gateway_attempt_overflow_total` | Attempts aggregated under `__overflow__` after model attribution bounds. |
| `inferweave_gateway_attempt_metrics_info{metric_definition_version}` | Frozen metric semantics version (`1`). |
| `inferweave_gateway_attempt_metrics_start_time_seconds` | Accumulator creation Unix time; explains counter resets. |

Outcome vocabulary is `completed`, `node_error`, `stream_error`,
`client_disconnected`, `client_cancelled`, `node_unreachable`, `upstream_rejected`,
`other`. Unrecognized source outcomes map to `other`; arbitrary strings never
become labels. Original source facts retain their original vocabulary. No
inference-success ratio is derived from transport success.

The `model` label is the canonical model selected by this gateway after its
local alias resolution, not the requested alias or a claim about deeper peers.

The initial policy admits at most 64 model label values of at most 256 UTF-8
bytes, plus one overflow group; these are explicit operational bounds, not
measured envelopes. A reserved `__overflow__`, empty or oversized model goes to
overflow. First-observed model membership remains fixed until restart. No request,
prompt, principal, session, node, worker, GPU, endpoint or credential identifiers
are labels. Prometheus escaping preserves valid model strings safely. Outcomes
are eight fixed values, directions two, basis five. All counters saturate rather
than wrap. Histograms use second boundaries 0.1, 1, 5, 15, 60, 180, 600, 1800
and +Inf, shared by every model; no latency percentile is fabricated from an
average. Missing duration contributes only to invalid-duration coverage.

The schema is additive and deliberately not the retired Go metrics vocabulary.
Do not relabel it as `iw_model_requests_total` or compare its attempt denominator
to historical logical-request rates. Never sum observations from multiple
forwarding hops as distinct user requests.

Deploy only via the existing reviewed green-main binary artifact pipeline
(`.woodpecker/rust.yaml`, `scripts/woodpecker-node-release.sh`, hash/commit-verified
`deploy/hive/iw-node-pull-deploy` and canary/gateway-cycle workflow). Once the
running release actually serves the endpoint, add a separate private scrape with
existing authoritative Rust service discovery and token file. Remote-write
allowlisting must explicitly include `inferweave_gateway_attempt.*`. Do not
replace the existing autoscale or public scheduler/trust scrape. No release or
production activation is proven by this source change.

Normative bounded vocabulary: `contracts/private-attempt-metrics.json`.
Runtime proof, independent review and production activation remain owed.
