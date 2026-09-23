# Actionable backpressure and load-diagnostic reporting design

Date: 2026-09-23  
Feature: `IW-BP-001`  
Canonical task: `P1-T19`

## Outcome

Every public inference `429` or `503` response tells a human what happened and
tells a client what to do without inviting an unbounded retry loop. The Go site
gateway, Rust gateway/relay, and the installed Pi engineering runtime interpret
one additive contract. The model-wide load diagnostic renders the same reason
and action data in a self-contained HTML report and correlates failures with
observed scaling and model-rebalancing events.

This design extends, but does not replace, the canonical `503` infrastructure
versus `429` caller-policy split in `specs/06_BACKPRESSURE_RETURN_TO_SENDER.md`.

## Operational evidence

The production diagnostic that motivated this design observed both failure
classes:

- one caller accumulated 86 requests behind a one-seat model, with the oldest
  waiter above 228 seconds;
- after a model queue cap was installed, a 24-request burst produced seven
  immediate `429` responses with `Retry-After: 8` instead of recreating that
  queue;
- one advertised model accepted a direct request at the Go gateway but returned
  no response headers before a two-minute client deadline.

Existing components expose only parts of the recovery decision. The Go
gateway's admission errors have a reason and delay but no action or replay
safety. Several Go `503` paths are plain text. The Rust gateway has canonical
reason and retry fields but inconsistent OpenAI adaptation. The Rust HTTP relay
creates local `429` and `503` bodies without `Retry-After` or condition codes.

The installed default Pi integration is
`berlinguyinca/pi-engineering-runtime`. Its interactive stream wrapper defaults
to an unlimited attempt count, its OpenAI parser does not unwrap nested
`error`, and its structured transport can clamp a server minimum delay
downward. These are bounded-backpressure defects, not presentation issues.

## Repositories and ownership

| Repository | Responsibility |
| --- | --- |
| `InferWeave/inferweave-specs` | Canonical status, field, action, and conformance contract |
| `InferWeave/inferweave` | Native envelope, OpenAI adaptation, Rust gateway/relay, schema and conformance fixtures |
| `metabolomics-us/inferweave-gateway` | Conformant Go site-gateway responses, proxy preservation, load-test HTML/timeline |
| `berlinguyinca/pi-engineering-runtime` | Default Pi parsing, cooldown scope, bounded retry and replay-safety enforcement |

The Pi package is installed as an extension around the upstream Pi coding-agent
CLI. Both the interactive stream wrapper and the structured admission transport
are contract consumers.

## Error envelope

OpenAI-compatible inference errors retain the standard outer `error` member.
All new fields are additive. Existing `type`, `code`, `reason`, counters, model
intent, scope, and request identifiers remain valid.

```json
{
  "error": {
    "message": "The model queue is full. Wait at least 8 seconds, add jitter, and do not send parallel retries.",
    "type": "inferweave_backpressure",
    "code": "model_queue_full",
    "reason": "model_queue_full",
    "retryable": true,
    "replay_safe": true,
    "request_state": "queued",
    "action": "backoff",
    "action_code": "IW-ACT-BACKOFF",
    "retry_after_ms": 8000,
    "scope": "model",
    "request_id": "req-opaque"
  }
}
```

### Field semantics

- `message`: safe, useful prose describing the immediate condition and primary
  action. It contains no credential, prompt text, output, or private endpoint.
- `code`: stable condition code. Existing frozen InferWeave reason codes remain
  authoritative; an adapter does not invent a synonym.
- `reason`: retained for compatibility where already published. When both are
  present they describe the same condition.
- `retryable`: a future request may succeed after the stated action.
- `replay_safe`: the same logical request can be repeated automatically. This
  is false when upstream acceptance is possible or unknown.
- `request_state`: `not_started`, `queued`, `dispatched`, `streaming`, or
  `unknown`.
- `action`: readable primary action name.
- `action_code`: frozen machine action code from the table below.
- `retry_after_ms`: minimum delay before another eligible attempt. It matches
  the `Retry-After` header after converting whole seconds to milliseconds.
- `scope`: at least `request`, `model`, `caller`, or `global`, allowing Pi to
  avoid freezing unrelated models for a model-local queue.
- `request_id`: local correlation ID when available. A relay does not replace
  it with a private upstream identifier.

The native InferWeave envelope adds equivalent optional fields rather than
changing the frozen reason-code vocabulary. Schema publication and reconciliation
tests are required by invariant 41.

## Action vocabulary

| Action code | Action | Client meaning |
| --- | --- | --- |
| `IW-ACT-BACKOFF` | `backoff` | Wait at least the declared delay, add jitter, then reconsider |
| `IW-ACT-REDUCE-CONCURRENCY` | `reduce_concurrency` | Stop parallel fan-out and lower caller concurrency before reconsidering |
| `IW-ACT-RETRY-ALTERNATE` | `retry_alternate` | Try another eligible route or deployment within the same finite budget |
| `IW-ACT-FIX-REQUEST` | `fix_request` | Change invalid syntax, parameters, endpoint, or model identity |
| `IW-ACT-AUTHENTICATE` | `authenticate` | Supply or refresh valid credentials |
| `IW-ACT-REQUEST-ACCESS` | `request_access` | Obtain permission or quota; repeated requests do not help |
| `IW-ACT-RESOLVE-CONFLICT` | `resolve_conflict` | Reconcile the idempotency/session conflict before resubmission |
| `IW-ACT-REDUCE-INPUT` | `reduce_input` | Reduce prompt/context/output reservation to the published ceiling |
| `IW-ACT-DO-NOT-RETRY` | `do_not_retry` | Surface the terminal error without automatic replay |

Action codes are frozen data, published documentation, and reconciled by a test.
Adding a code requires the same decision discipline as adding a reason code.

## HTTP status matrix

| Status | InferWeave meaning | Default action | Automatic replay |
| --- | --- | --- | --- |
| `400` | Malformed request or unsupported parameter | `IW-ACT-FIX-REQUEST` | No |
| `401` | Missing, invalid, or expired credential | `IW-ACT-AUTHENTICATE` | No |
| `403` | Authenticated but forbidden or hard quota | `IW-ACT-REQUEST-ACCESS` | No |
| `404` | Model or endpoint does not exist | `IW-ACT-FIX-REQUEST` | No |
| `408` | Server did not receive the complete request in time | `IW-ACT-BACKOFF` | Only when `replay_safe=true` |
| `409` | Native preview constraint or idempotency/session conflict | `IW-ACT-RESOLVE-CONFLICT` | No |
| `413` | Context or request exceeds a published hard ceiling | `IW-ACT-REDUCE-INPUT` | No |
| `422` | Valid JSON with invalid inference semantics | `IW-ACT-FIX-REQUEST` | No |
| `429` | Caller, queue, rate, or FairShare restriction | Back off and/or reduce concurrency | Only when explicitly safe |
| `500` | Unexpected implementation failure | Back off and alert operators | Only when explicitly safe |
| `502` | Selected upstream produced an invalid response | `IW-ACT-RETRY-ALTERNATE` | Only when explicitly safe |
| `503` | Model/capacity unavailable, warming, draining, or temporarily unhealthy | Back off or try an eligible alternate | Only when explicitly safe |
| `504` | Selected upstream exceeded its deadline | `IW-ACT-RETRY-ALTERNATE` | Only when explicitly safe |

An unknown model is `404`; a known model with no usable capacity is `503`.
`413` never becomes a capacity retry. Nonstandard public status `499` and
unrelated exotic status codes are not introduced.

## Delay and retry rules

1. `Retry-After` is the minimum server-requested delay. A body delay cannot
   shorten it. If legacy fields disagree, a client uses the larger value.
2. A client may add positive jitter. It never subtracts jitter.
3. A local per-attempt delay ceiling does not clamp a server minimum downward.
   If the minimum exceeds the remaining elapsed-time budget, the client stops
   instead of retrying early.
4. Retry requires all of:
   - `retryable=true`;
   - `replay_safe=true`;
   - no response token or other committed output;
   - a permitted action code;
   - remaining attempt, candidate, and elapsed-time budgets.
5. `request_state=streaming`, `dispatched`, or `unknown` is not automatically
   replayed without an idempotency guarantee that covers inference execution.
6. Retry loops have finite configured attempt and elapsed-time defaults. An
   unset limit never means infinity.
7. Model-scoped backpressure cools that model. Caller/global policy can cool a
   wider scope. A model queue does not freeze unrelated models.
8. A relay preserves upstream guidance but does not replay an ambiguous or
   partially streamed inference request.

## Gateway behavior

### Rust gateway and relay

- Adapt native errors into the additive OpenAI envelope without changing their
  canonical reason.
- Supply explanation, action, replay safety, request state, and matching delay
  on local admission failures.
- Preserve safe upstream `Retry-After` and structured fields across relay
  boundaries.
- Add the contract to locally generated relay queue-full, concurrency, timeout,
  connection-budget, and memory-budget responses.
- Do not convert an error after HTTP 200 or committed stream output into a new
  HTTP response. Emit a terminal stream failure and mark replay unsafe.

### Go site gateway

- Extend structured admission errors additively.
- Replace plain-text no-worker, busy-worker, failed-link-dispatch, and generic
  inference `503` responses with the same envelope.
- Normalize upstream `429`/`503` only when required fields are absent; preserve
  a more specific upstream condition and never leak its private request ID or
  endpoint.
- Preserve the existing warmup trigger: an infrastructure no-worker `503` is
  not mislabeled as overload merely to make headers uniform.
- Keep non-inference readiness and administrative failures outside this change.

## Pi default-client behavior

`berlinguyinca/pi-engineering-runtime` changes both retry paths:

- unwrap `error`, `detail`, and nested `detail.error` envelopes;
- accept both legacy `inference_admission` and new
  `inferweave_backpressure` types;
- read condition code, action code, scope, retryability, replay safety, request
  state, body delay, and `Retry-After`;
- use the larger valid delay and treat it as a minimum;
- remove the interactive stream wrapper's unlimited-attempt default;
- enforce finite attempts and total elapsed time on both paths;
- never retry after output reaches the sink;
- never automatically replay `dispatched`, `streaming`, or `unknown` requests;
- apply model-local cooldowns without pausing unrelated models;
- retain legacy parsing for gateways that have not deployed the additive
  fields.

Pi surfaces the server explanation and stable code when it stops. It does not
replace the final error with a generic “retry exhausted” message.

## Load diagnostic artifacts

Every `iw-loadtest` run additionally writes:

- `report.html`: self-contained HTML and CSS with no remote assets;
- `timeline.jsonl`: sanitized periodic telemetry samples and derived events.

Both are mode `0600`, atomically published, and included in overwrite
protection. The existing JSON, JSONL, and Markdown artifacts remain canonical
machine evidence.

### HTML contents

- executive totals: requests, success/failure counts and rates, models and
  lanes;
- failure breakdown by HTTP status, condition code, action code, and scope;
- model and lane tables with TTFT, wall latency, output tokens/second, sample
  count, and success rate;
- reliability, TTFT, latency, throughput, node, and ordered worker-path
  rankings;
- explicit “not ranked” treatment for zero-success or insufficient-sample
  groups rather than treating missing measurements as zero;
- sortable/filterable accessible tables and CSS performance bars;
- scaling/rebalancing timeline correlated with request start, completion,
  failure, queue depth, and latency changes;
- telemetry gaps rendered as unknown intervals, never as stable zero change.

## Scaling and rebalancing timeline

During the run, the diagnostic samples sanitized stats, dashboard, and topology
surfaces every five seconds by default. The interval is configurable and the
sampler has bounded response sizes and timeouts. Sampling failure records a gap
but does not fail or retry a logical inference request.

The five-second initial default is a visibility and safety policy choice, not a
measured optimum. Implementation must benchmark endpoint and sampler overhead
and record that evidence before treating the interval as tuned.

Reported gateway/scheduler events retain their source. Consecutive snapshots
can additionally derive:

- scale up: worker, GPU, or slot count increases;
- scale down: worker, GPU, or slot count decreases;
- model rebalance: a stable opaque worker/GPU assignment moves between model
  deployments;
- registration or withdrawal;
- desired/live/pending capacity change;
- scaling allowed, refused, or blocked by a named guardrail.

Derived events are labeled `inferred`; emitted scheduler/gateway events are
labeled `reported`. A changing inventory without a stable identity is labeled
`inventory_change`, not falsely called a rebalance. The report never claims a
causal relationship merely because a scale event and latency change are close
in time.

## Rankings

Rankings always display sample count and lane. They are deterministic and use:

- reliability: success rate descending, then failures ascending;
- TTFT and latency: successful samples only, lower percentile first;
- throughput: successful samples only, higher output tokens/second first;
- backpressure: failure rate and time spent waiting, higher first;
- scaling response: reported or inferred event-to-healthy-capacity time when
  both endpoints are observed; otherwise unranked.

Ties use model ID then lane. Rankings across materially different context depth
are visibly separated, preserving invariant 42.

## Security and compatibility

- No API key, Authorization header, prompt/output body, private endpoint, or
  stable private identity enters an error, timeline, or HTML report.
- JSON and HTML escaping is mandatory; report data is not executable script.
- Existing clients continue to receive compatible status, outer OpenAI shape,
  reason, and delay fields.
- Existing reason codes remain frozen. The new action-code vocabulary is
  additive and machine-reconciled.
- `Retry-After` and body delay are generated from one value to prevent drift.

## Verification design

### Contract and conformance

- one cross-language fixture per status/action/replay combination;
- Rust protocol schema, Rust gateway, Go gateway, and Pi parser consume the
  same hostile and valid vectors;
- field removal, code drift, delay mismatch, or new undocumented action fails;
- legacy envelopes remain accepted.

### Server tests

- every inference `429`/`503` branch returns explanation, stable condition and
  action codes, retry/replay booleans, request state, scope, and matching delay;
- upstream preservation and local enrichment never expose private metadata;
- no-worker still triggers warmup;
- a failure after committed output is never advertised replay-safe.

### Pi tests

- nested OpenAI errors are parsed;
- header/body disagreement uses the longer wait;
- a server minimum above the remaining budget stops rather than retries early;
- attempt and elapsed budgets terminate both retry implementations;
- model scope does not pause unrelated models;
- no output, unknown-state, partial-output, and idempotent cases exercise the
  replay gate;
- terminal errors retain the server message and codes.

### Report tests

- HTML escaping and absence of remote resources;
- deterministic rankings, ties, missing samples, and failure rates;
- artifact permissions, atomic publication, and overwrite refusal;
- reported versus inferred scaling events;
- stable-identity rebalance versus unknown inventory change;
- telemetry gaps and snapshot-size/time bounds;
- secret and private-endpoint fixtures never appear in HTML or timeline.

## Rollout and implementation order

1. Update `IW-BP-001`, canonical schemas, action-code frozen data, task evidence,
   and conformance vectors in the specs repository.
2. Implement protocol and adapters in `InferWeave/inferweave`; keep fields
   additive and land Rust conformance tests first.
3. Implement the conformant Go site-gateway responses and proxy preservation.
4. Implement both Pi retry consumers, finite budgets, and scope-aware cooldown.
5. Implement timeline sampling and HTML generation in `iw-loadtest`.
6. Run cross-language fixtures, focused suites, full repository suites, secret
   scans, and independent reviews.
7. Deploy servers before relying on new client actions; deploy Pi with legacy
   fallback; then generate a production example HTML report.

Each repository receives its own reviewable PR. Production deployment remains
governed by that repository's gates and rollback procedure.

## Out of scope

- automatic replay after committed output;
- exactly-once inference without a separate idempotency design;
- changing readiness, admin, database, or WebSocket control-plane errors;
- claiming production approval for the clean-slate InferWeave monorepo while
  its production gate remains blocked;
- inventing hardware rebalance events without stable resource identity;
- causal claims from temporal correlation alone.
