# Actionable Backpressure and Load Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship one safe, actionable inference-error contract across InferWeave servers and the default Pi client, plus a self-contained load-test report that measures failures, performance, routing, scaling, and model movement.

**Architecture:** The specs repository owns the frozen action vocabulary and hostile/valid fixtures. Rust and Go servers add compatible guidance without changing existing reason semantics; Pi centralizes envelope parsing and replay eligibility; `iw-loadtest` records sanitized samples and renders deterministic JSONL/HTML evidence. Server rollout precedes reliance on the new client fields, and legacy envelopes remain accepted throughout.

**Tech Stack:** Markdown/JSON/Python validation, Rust/Serde/Axum, Go `net/http` and `html/template`, TypeScript/Node test runner, GitHub pull requests, systemd deployment.

**Spec:** `docs/specs/backpressure-actions-load-report/00-design.md`

## Global Constraints

- Preserve the canonical distinction: infrastructure/capacity is `503`; caller/rate/FairShare policy is `429`.
- Existing InferWeave reason codes and Go `type=inference_admission` remain compatible and unchanged.
- `Retry-After` is a minimum; body guidance cannot shorten it and clients add only positive jitter.
- Automatic replay requires `retryable=true`, `replay_safe=true`, an eligible request state/action, no committed output, and remaining finite attempt and elapsed budgets.
- Never replay `dispatched`, `streaming`, or `unknown` inference requests without an idempotency guarantee.
- Unknown model is `404`; known model without usable capacity is `503`; hard request/context ceiling is `413` on public inference.
- No key, authorization header, prompt/output, private endpoint, or stable private infrastructure identity enters reports or public errors.
- Every artifact is atomically published at mode `0600`; every load run is finite and bounded.
- Do not label snapshot differences as causal; distinguish `reported`, `inferred`, `inventory_change`, and telemetry gaps.
- No new external dependency is required.

## Review Focus

- A nested `detail.error` envelope with explicit false replay flags must never be retried; Task 4 adds this case to both Pi retry paths.
- Conflicting header/body delays must use the larger value, and a delay beyond the remaining budget must stop rather than sleep early; Task 4 tests both.
- Go no-worker `503` must retain the absence of the overload marker so warmup still triggers; Task 3 locks this with the existing gateway integration test.
- Upstream error enrichment must not leak upstream request IDs or rewrite a response after streaming begins; Tasks 2 and 3 add privacy/commit-boundary tests.
- A topology identity change without stable resource continuity must be `inventory_change`, not `rebalance`; Task 5 adds hostile snapshot fixtures.

---

### Task 1: Publish the canonical contract and shared vectors

**Files:**
- Modify: `specs/06_BACKPRESSURE_RETURN_TO_SENDER.md`
- Modify: `contracts/error.example.json`
- Modify: `contracts/feature-registry.json`
- Modify: `contracts/canonical-task-graph.json`
- Modify: `tasks/phase-1/P1-T19.md`
- Modify: `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`
- Modify: `OPEN_GATES.md`
- Create: `contracts/backpressure-action-codes.json`
- Create: `contracts/backpressure-conformance-v1.json`
- Modify: `scripts/validate_specs.py`
- Test: `scripts/test_validate_specs.py`

**Interfaces:**
- Consumes: the field and status definitions in `docs/specs/backpressure-actions-load-report/00-design.md`.
- Produces: `backpressure-action-codes.json` with the nine frozen `IW-ACT-*` values and `backpressure-conformance-v1.json` with `name`, `status`, `headers`, `body`, `expected`, and `legacy` cases.

- [ ] **Step 1: Write failing validator tests for vocabulary and vector drift**

```python
def test_backpressure_actions_match_vectors(tmp_path):
    repo = copy_repo(tmp_path)
    actions = json.loads((repo / "contracts/backpressure-action-codes.json").read_text())
    vectors = json.loads((repo / "contracts/backpressure-conformance-v1.json").read_text())
    assert {v["expected"]["action_code"] for v in vectors["cases"] if v["expected"].get("action_code")} <= set(actions["values"])

def test_undocumented_action_fails_validation(tmp_path):
    repo = copy_repo(tmp_path)
    mutate_vector_action(repo, "IW-ACT-NOT-DOCUMENTED")
    assert validate(repo).returncode != 0
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run: `python3 -m unittest scripts.test_validate_specs -v`

Expected: failure because the frozen action data, conformance vectors, and validator checks do not exist.

- [ ] **Step 3: Add the frozen action data and exhaustive vectors**

Use this exact vocabulary:

```json
{
  "name": "backpressure_action_code",
  "values": [
    "IW-ACT-BACKOFF",
    "IW-ACT-REDUCE-CONCURRENCY",
    "IW-ACT-RETRY-ALTERNATE",
    "IW-ACT-FIX-REQUEST",
    "IW-ACT-AUTHENTICATE",
    "IW-ACT-REQUEST-ACCESS",
    "IW-ACT-RESOLVE-CONFLICT",
    "IW-ACT-REDUCE-INPUT",
    "IW-ACT-DO-NOT-RETRY"
  ]
}
```

Vectors must cover statuses `400,401,403,404,408,409,413,422,429,500,502,503,504`, legacy `inference_admission`, nested `error`/`detail.error`, conflicting delays, explicit false booleans, every request state, unknown actions, and hostile strings requiring escaping.

- [ ] **Step 4: Extend the canonical prose, task evidence, and validator**

The validator must reject duplicate/unknown action codes, mismatched `code`/`reason`, retryable vectors without bounded guidance, replay-safe vectors in unsafe states, and task/feature text that omits the shared contract files.

- [ ] **Step 5: Run full spec validation**

Run: `python3 -m unittest scripts.test_validate_specs -v && python3 scripts/validate_specs.py`

Expected: all validator tests pass and the repository reports a valid feature/task DAG.

- [ ] **Step 6: Commit**

Commit only Task 1 files with a Lore-protocol message explaining why action codes are frozen separately from reason codes.

---

### Task 2: Implement Rust protocol, gateway, and relay guidance

**Files:**
- Modify: `crates/iw-protocol/src/error.rs`
- Modify: `schemas/json-schema/error_envelope.json`
- Modify: `crates/iw-core/data/vocabularies.json`
- Modify: `docs/specs/shared-vocabularies.md`
- Modify: `docs/specs/protocol.md`
- Modify: `crates/iw-gateway/src/server.rs`
- Modify: `crates/iw-gateway/src/adaptive.rs`
- Modify: `crates/iw-gateway/src/http.rs`
- Modify: `crates/iw-relay-http/src/proxy.rs`
- Modify: `conformance/vectors/error_envelope.json`
- Modify: `conformance/MANIFEST.json`
- Modify: `conformance/MANIFEST.sha256`
- Test: `crates/iw-protocol/src/error.rs`
- Test: `crates/iw-gateway/tests/adaptive.rs`
- Test: `crates/iw-gateway/tests/gateway_e2e.rs`
- Test: `crates/iw-gateway/tests/join_adaptive_e2e.rs`
- Test: `crates/iw-relay-http/tests/integration.rs`
- Test: `crates/iw-relay-http/tests/chaos.rs`
- Test: `crates/conformance/tests/conformance.rs`

**Interfaces:**
- Consumes: Task 1 action values and conformance semantics.
- Produces: `ActionCode`, `RequestState`, and optional `message`, `action`, `actionCode`, `replaySafe`, `requestState`, and `scope` fields on native envelopes; OpenAI adapters expose equivalent snake-case fields.

- [ ] **Step 1: Add failing protocol/schema reconciliation tests**

```rust
#[test]
fn actionable_capacity_error_round_trips() {
    let mut env = full_envelope();
    env.action_code = Some(ActionCode::Backoff);
    env.replay_safe = Some(true);
    env.request_state = Some(RequestState::Queued);
    env.scope = Some("model".into());
    let parsed = parse_error_envelope(&serde_json::to_string(&env).unwrap()).unwrap();
    assert_eq!(parsed.action_code, Some(ActionCode::Backoff));
    assert_eq!(parsed.request_state, Some(RequestState::Queued));
}
```

Also make the frozen-data reconciliation test fail when an enum value is absent from `vocabularies.json` or the published table.

- [ ] **Step 2: Confirm protocol tests fail for missing types/fields**

Run: `cargo test -p iw-protocol && cargo test -p iw-core registry::`

Expected: compile/test failure naming `ActionCode`, `RequestState`, or missing schema properties.

- [ ] **Step 3: Add optional native fields and regenerate schemas**

Implement closed Serde enums for the nine actions and five states, retain the current `ErrorEnvelope::new` signature for callers, initialize new fields to `None`, and add a builder/helper for complete inference guidance. Run `cargo run -p schema-gen -- --generate`; never hand-edit generated bindings after generation.

- [ ] **Step 4: Add failing adaptive/public inference tests**

Assert the nested OpenAI error body includes:

```json
{"error":{"type":"inferweave_backpressure","code":"capacity_unavailable","reason":"capacity_unavailable","retryable":true,"replay_safe":true,"request_state":"queued","action":"backoff","action_code":"IW-ACT-BACKOFF","retry_after_ms":1000,"scope":"model"}}
```

Add separate assertions for hard input ceiling `413`, stale/capacity `503`, policy `429`, and the post-commit no-replay boundary.

- [ ] **Step 5: Implement one Rust guidance mapping and use it in native/OpenAI adapters**

Create a pure mapping from status/reason/request state to prose/action/retry/replay/scope. Adaptive queue refusals are queued/not-started and replayable; an upstream-dispatched failure is not. Generate header and body delay from the same millisecond value using ceiling whole seconds.

- [ ] **Step 6: Add failing relay-local and upstream-preservation tests**

Test queue full, client concurrency, queue timeout, connection/memory budget, upstream structured `429/503`, upstream request-ID removal, Retry-After preservation, and ambiguous generation non-replay.

- [ ] **Step 7: Implement relay guidance without replaying requests**

Replace the local two-field `json_error` call sites with a typed helper. Preserve safe upstream fields and headers; enrich only missing public fields; exclude readiness/control-plane errors and never buffer/rewrite a committed event stream.

- [ ] **Step 8: Run focused and full Rust verification**

Run:

```bash
cargo test -p iw-protocol
cargo test -p iw-core registry::
cargo test -p iw-core backpressure::
cargo test -p iw-gateway --test adaptive
cargo test -p iw-gateway --test gateway_e2e
cargo test -p iw-gateway --test join_adaptive_e2e
cargo test -p iw-relay-http --test integration
cargo test -p iw-relay-http --test chaos
cargo test -p iw-conformance
cargo run -p schema-gen -- --check
cargo test --workspace
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
```

- [ ] **Step 9: Commit**

Commit Task 2 as one reviewable Rust contract/adapters unit with the focused/full evidence in Lore trailers.

---

### Task 3: Make Go site-gateway inference errors actionable

**Files:**
- Create: `internal/proxy/inference_error.go`
- Create: `internal/proxy/inference_error_test.go`
- Modify: `internal/proxy/proxy.go`
- Modify: `internal/proxy/admission_extensions_test.go`
- Modify: `internal/proxy/request_id_test.go`
- Modify: `internal/proxy/traffic_test.go`
- Modify: `cmd/gateway/admission.go`
- Modify: `cmd/gateway/admission_error_policy_test.go`
- Modify: `cmd/gateway/gateway_test.go`
- Modify: `cmd/gateway/performance_integration_test.go`
- Modify: `docs/Pi-admission-integration.md`

**Interfaces:**
- Consumes: Task 1 field/action definitions while retaining `type=inference_admission` on legacy admission errors.
- Produces: `InferenceError`/`WriteInferenceError` for local failures and `NormalizeInferenceError(status, headers, body, localRequestID)` for bounded upstream `429/503` enrichment.

- [ ] **Step 1: Write table-driven failing tests for local inference errors**

```go
func TestInferenceErrorsAreActionable(t *testing.T) {
    tests := []struct{ name string; status int; code, action string; replay bool }{
        {"queue full", 429, "model_queue_full", "IW-ACT-BACKOFF", true},
        {"no worker", 503, "capacity_unavailable", "IW-ACT-RETRY-ALTERNATE", true},
        {"dispatch uncertain", 503, "route_dispatch_failed", "IW-ACT-DO-NOT-RETRY", false},
    }
    // Marshal the real writer response and assert status, matching delay,
    // stable fields, safe prose, and no private metadata.
}
```

- [ ] **Step 2: Confirm RED**

Run: `go test ./internal/proxy ./cmd/gateway -run 'InferenceError|AdmissionError|ColdModel|Busy'`

Expected: failures because generic 503s are plain text and admission fields are incomplete.

- [ ] **Step 3: Implement the local error helper and admission extension**

Use additive snake-case JSON fields. Keep no-worker free of `X-InferWeave-Overload`; keep busy/queue-full overload marking. Use one delay value for body/header. Failed link dispatch is `request_state=unknown`, `replay_safe=false`.

- [ ] **Step 4: Add failing upstream normalization/privacy tests**

Cover missing fields, complete upstream body preservation, malformed/oversized/non-JSON bodies, conflicting request IDs, content-length rewrite, streaming commitment, and private endpoint/authorization strings.

- [ ] **Step 5: Implement bounded pre-commit normalization**

Normalize only inference `429/503` responses before stream commitment. Preserve a more specific upstream reason/action, replace upstream correlation identity with the local ID, bound JSON parsing, and pass unparseable responses safely without inventing replay safety.

- [ ] **Step 6: Verify warmup and proxy behavior**

Run:

```bash
go test ./internal/proxy ./cmd/gateway
go test -race ./internal/proxy ./cmd/gateway
go vet ./...
go test ./...
make fmt-check
```

Expected: cold model still triggers exactly one warmup, busy does not warm, and all suites pass.

- [ ] **Step 7: Commit**

Commit Task 3 with a directive preserving the no-worker/overload distinction.

---

### Task 4: Make the default Pi client parse and obey the contract safely

**Files:**
- Modify: `src/inference/admissionContract.ts`
- Modify: `src/inference/retryDelay.ts`
- Modify: `src/inference/admissionConfig.ts`
- Modify: `src/inference/admissionTransport.ts`
- Modify: `src/gateway/signals.ts`
- Modify: `src/gateway/config.ts`
- Modify: `src/gateway/AdmissionController.ts`
- Modify: `src/gateway/streamRetry.ts`
- Modify: `src/gateway/installStreamRetry.ts`
- Modify: `extensions/index.ts`
- Modify: `docs/specs/pi-engineering-harness-inferweave-admission-retry-spec/01-admission-error-contract.md`
- Modify: `docs/specs/pi-engineering-harness-inferweave-admission-retry-spec/02-retry-state-machine.md`
- Modify: `docs/inference-admission-retry.md`
- Test: `test/unit/inference-admission-contract.test.ts`
- Test: `test/unit/inference-admission-delay.test.ts`
- Test: `test/unit/inference-admission-transport.test.ts`
- Test: `test/unit/gateway-admission.test.ts`
- Test: `test/unit/gateway-stream-retry.test.ts`
- Test: `test/unit/gateway-stream-retry-install.test.ts`
- Test: `test/integration/admission-inferweave.test.ts`
- Test: `test/integration/gateway-stream-retry-registry.test.ts`

**Interfaces:**
- Consumes: legacy and new nested envelopes plus response headers.
- Produces: one normalized guidance shape shared by both retry paths:

```ts
interface InferenceGuidance {
  status?: number;
  message?: string;
  type?: string;
  code?: string;
  reason?: string;
  action?: string;
  actionCode?: string;
  retryable?: boolean;
  replaySafe?: boolean;
  requestState?: "not_started" | "queued" | "dispatched" | "streaming" | "unknown";
  scope?: "request" | "model" | "caller" | "global" | string;
  retryAfterMs?: number;
}
```

- [ ] **Step 1: Add failing parser/eligibility tests**

Test top-level, `error`, `detail`, and `detail.error`; both error types; explicit false flags; unknown action; all request states; legacy bodies; and terminal message/code preservation. A safe retry test must require `queued|not_started`, `IW-ACT-BACKOFF|IW-ACT-REDUCE-CONCURRENCY|IW-ACT-RETRY-ALTERNATE`, and explicit true flags for the new contract.

- [ ] **Step 2: Confirm parser tests fail**

Run: `node --test test/unit/inference-admission-contract.test.ts test/unit/gateway-admission.test.ts`

Expected: new nested fields/types are missing or ignored.

- [ ] **Step 3: Implement shared parsing and replay eligibility**

Unwrap nested envelopes once, preserve legacy heuristics only when new fields are absent, and have both transports call the same pure replay predicate. Explicit false always wins over status/text inference.

- [ ] **Step 4: Add failing delay and finite-budget tests**

```ts
assert.equal(resolveRetryDelay({ headers: { "retry-after": "8" }, body: { retry_after_ms: 1000 }, ...base }).serverDelayMs, 8000);
assert.equal(decideWait({ serverMinimumMs: 8000, remainingMs: 7000 }).action, "stop");
```

Also prove the interactive wrapper terminates at finite default attempts and elapsed time, and both paths preserve the final server error.

- [ ] **Step 5: Implement maximum server hint and non-shortening budgets**

Choose the largest valid header/body hint. Never clamp that minimum down in `retryDelay`, `AdmissionController`, or `admissionTransport`; stop when it cannot fit. Add finite interactive defaults and an injectable monotonic clock. Keep positive jitter bounded by the remaining budget or stop.

- [ ] **Step 6: Add failing scope and partial-output tests**

Prove explicit `scope=model` does not pause another model, caller/global scopes retain their wider cooldown, and any forwarded event or withheld response with unsafe state prevents replay.

- [ ] **Step 7: Implement scope-aware cooldown and thread configuration**

Key model cooldown by provider/model identity. Thread finite attempt/elapsed defaults through `installStreamRetry` and extension wiring. Preserve existing legacy behavior when scope is absent.

- [ ] **Step 8: Update local Pi specifications and run verification**

Run:

```bash
node --test 'test/unit/inference-admission*.test.ts' 'test/unit/gateway*.test.ts' test/integration/extension-gateway-wiring.test.ts test/integration/gateway-stream-retry-registry.test.ts test/integration/admission-inferweave.test.ts
npm run typecheck
npm run lint
npm test
npm run test:e2e
```

- [ ] **Step 9: Commit**

Commit Task 4 as a dedicated Pi PR unit; document finite defaults and legacy fallback.

---

### Task 5: Generate the HTML report and scaling/rebalancing timeline

**Files:**
- Modify: `internal/loadtest/types.go`
- Modify: `internal/loadtest/client.go`
- Modify: `internal/loadtest/pi.go`
- Modify: `internal/loadtest/summary.go`
- Modify: `internal/loadtest/report.go`
- Create: `internal/loadtest/telemetry.go`
- Create: `internal/loadtest/telemetry_test.go`
- Create: `internal/loadtest/html.go`
- Create: `internal/loadtest/html_test.go`
- Modify: `internal/loadtest/loadtest_test.go`
- Modify: `cmd/iw-loadtest/main.go`
- Modify: `cmd/iw-loadtest/main_test.go`
- Modify: `docs/qa/2026-09-22-llm-load-diagnostics.md`

**Interfaces:**
- Consumes: structured failure fields from Task 3 and bounded sanitized `/iw/v1/stats`, `/iw/v1/dashboard`, `/iw/v1/topology` samples.
- Produces: `timeline.jsonl`, `report.html`, enriched `requests.jsonl`/`summary.json`, and deterministic rankings.

- [ ] **Step 1: Add failing artifact and privacy tests**

Assert `report.html` and `timeline.jsonl` are reserved, mode `0600`, atomically published, refuse overwrite, contain no remote asset URLs/scripts, and omit fixture keys, prompts, output, endpoint addresses, bearer text, node/job IDs, and raw private resource IDs.

- [ ] **Step 2: Confirm RED**

Run: `go test ./internal/loadtest ./cmd/iw-loadtest -run 'HTML|Timeline|Artifact|Redaction'`

Expected: missing artifacts/types/renderers.

- [ ] **Step 3: Implement bounded sanitized sampling**

Add `TelemetryInterval`, `TelemetryTimeout`, and `TelemetryMaxBytes` to `Config`. A sampler covers all lanes, records timestamp/source/status/sanitized counts/opaque run-local identities, records gaps without failing inference, and stops cleanly on cancellation. Default interval is five seconds but is described as an initial policy, not a tuned optimum.

- [ ] **Step 4: Add failing event-inference tests**

Use consecutive fixtures to prove scale up/down, stable-identity model rebalance, registration/withdrawal, desired/live/pending changes, reported scheduler guardrails, unknown identity as `inventory_change`, and failed sampling as a gap.

- [ ] **Step 5: Implement event derivation and structured error capture**

Store source=`reported|inferred`, confidence/evidence references, and never causal language. Parse error `code`, `action_code`, `scope`, retry/replay/state, and safe message for both direct and Pi lanes.

- [ ] **Step 6: Add failing summary/ranking/HTML tests**

Cover success/failure rates, status/condition/action/scope breakdowns, sample counts, deterministic ties, zero-success unranked groups, context-depth separation, node and ordered worker-path metrics, HTML escaping, filtering/sorting hooks, and timeline correlation.

- [ ] **Step 7: Implement deterministic self-contained rendering**

Use `html/template` and inline CSS plus minimal inline JavaScript sourced only from escaped JSON data. Render executive cards, failure tables, model/lane performance, reliability/TTFT/latency/tokens-per-second rankings, route rankings, and timeline. Missing evidence renders `unknown`/`not ranked`, never numeric zero.

- [ ] **Step 8: Add sampler benchmark and run full Go verification**

Run:

```bash
go test ./internal/loadtest ./cmd/iw-loadtest
go test -race ./internal/loadtest ./cmd/iw-loadtest
go test ./internal/loadtest -run '^$' -bench 'Telemetry|Sampler' -benchmem
go vet ./...
go test ./...
make fmt-check
```

Record benchmark hardware, sample payload sizes, allocations, and elapsed time in the QA document; do not call the interval tuned without evidence.

- [ ] **Step 9: Commit**

Commit Task 5 separately from Task 3 so report behavior can be reviewed independently.

---

### Task 6: Cross-repository conformance, review, rollout, and production evidence

**Files:**
- Modify only files required by material review findings.
- Generate outside git: one new private `iw-loadtest` artifact directory.
- Update: `docs/qa/2026-09-22-llm-load-diagnostics.md` with links/aggregate evidence but no credentials or private identities.

**Interfaces:**
- Consumes: Tasks 1–5, the existing dedicated load-test key file, and each repository's deployment gates.
- Produces: reviewed PRs, server-first rollout, updated local Pi extension, and one sanitized production HTML report.

- [ ] **Step 1: Run all cross-language vectors**

Run the specs validator, Rust conformance/self-tests, Go fixture consumer tests, and Pi fixture consumer tests against the same canonical vector content. Any semantic mismatch blocks rollout.

- [ ] **Step 2: Run independent reviews and fix material findings**

Review each repository diff separately for contract compliance, replay safety, privacy, stream commitment, boundedness, and test adequacy. Re-run affected focused and full suites after fixes.

- [ ] **Step 3: Push branches and open one PR per repository**

PR descriptions must link the design, summarize the additive contract, list exact verification, identify rollout order, and declare any remaining test/deployment gaps. Do not push directly to `main`.

- [ ] **Step 4: Merge/deploy servers before client reliance**

Merge only green, reviewed changes under each repository policy. Deploy the Go gateway with its existing rollback procedure; treat the Rust repository production gate honestly and do not claim it deployed if the gate remains closed.

- [ ] **Step 5: Merge and install the Pi client with legacy fallback**

Update the installed `berlinguyinca/pi-engineering-runtime` extension from its merged revision, verify package loading, and run a bounded real Pi request before enabling reliance on explicit new fields.

- [ ] **Step 6: Run bounded production diagnostics**

Use the dedicated mode-0600 key and a fresh output directory. Start with smoke, then steady; require explicit stress acknowledgement. Run all catalog models in direct and Pi lanes, collect five-second initial-policy samples, and stop on the tool's finite limits.

- [ ] **Step 7: Verify the generated evidence**

Check artifact permissions, secret scan, model/lane totals, failure rates, error/action breakdowns, tokens/s, host/worker-path rankings, gaps, and scale/rebalance classifications. Compare with the earlier baseline without claiming causation.

- [ ] **Step 8: Publish the final diagnostic summary**

Report what works, what fails, deployment revisions, rollback points, remaining risks, and exact paths to the private HTML/JSON artifacts. Never include the API key or private infrastructure identifiers.
