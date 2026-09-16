# Implementation Report — Dynamic Context Capability and Request-Scoped Admission

Date: 2026-09-14 · Branch: `feat/dynamic-context-capabilities` (all four repos)

This report closes the bundle in `00-overview-and-architecture.md`. Where the
bundle says "the implementation shall", this report says what was implemented,
where, what was measured, and what the independent review found.

## 1. The original problem, and exactly where the fixed behaviour lived

The reported defect — *every Pi session permanently occupies a context slot,
`caller_concurrency` is refused at low real concurrency, a 1M deployment is
advertised as 262144, and 260K is a magic number* — was four compounding
full-window reservations, not one bug:

| # | Where | What it did |
|---|-------|-------------|
| 1 | `inferweave-impl/crates/iw-core/src/capacity.rs` | An inference **seat reserved the deployment's full `context_tokens` for its whole life** (acquired on seat creation, released on seat removal). 5 active seats on a 262K model reserved 1,310,720 tokens against a 1,048,576 pool — the seat model was *descriptive* by spec 04 and *capacity* by code. |
| 2 | `inferweave-impl/crates/iw-core/src/autospec_pi.rs` | Every Pi session was mapped to `WorkloadClass::C256` and **pinned for the session's life**, so `caller_concurrency` counted sessions, and 5 idle Pi sessions exhausted the caller budget. |
| 3 | `autospec-inferweave/linux-turing-dual/scripts/admission.py` + `gateway.py` | `tier_tokens()` reserved a **share of the model's window** per request (small 32,768 / large 65,536), held for the request's whole life in a `Pool` lease; `POOL_SIZES` was a hardcoded table, not runtime observation. |
| 4 | `~/.pi/agent/qwen-nodes.json` | Advertised **262144 for every model id**, because the operator had written the reservation ceiling into the client config. |

So a 4K prompt and a 250K prompt cost the same, idle sessions looked like busy
callers, and the advertised window was a ceiling someone had once used for
admission.

## 2. What the new architecture is

Three layers, each with one job:

**Capability (what can be promised).** A model's context is *discovered from the
runtime*, never from a model-name table. `llama.cpp` reports `n_ctx`/
`system_prompt_tokens` and `--ctx-size`; vLLM reports `max_model_len`; a generic
endpoint may report `context_window` / `x_context_window` / an
`inferweave.context` extension. Per alias, the catalog computes:

- `guaranteed_routable_tokens` — the **smallest** observed usable backend unless
  context-aware routing is enforced, because that is the largest window the alias
  can promise a request will be routed to;
- `max_routable_tokens` — the largest observed usable backend;
- `max_output_tokens`, `heterogeneous`, `capability_generation` (a content hash,
  reused as `ETag`), `capability_source` (provenance: which deployment and which
  field), and freshness (`fresh` / `stale` / `expired` / `unknown`).

Stale data is served only if it **cannot expand** the advertised context;
expiring never silently widens a promise. `ETag` = capability generation, so a
client's `If-None-Match` is a 304 until the guarantee actually changes.

**Routing (where it goes).** Context feasibility is a **hard filter before any
scoring** — before affinity, locality, latency, or load. The Rust `route()` and
the Python scheduler both record an `insufficient-context` exclusion per
candidate, which is what makes `no_context_capable_backend` distinguishable from
`backend_saturated` (retryable) and `context_capacity` (structural). Affinity is
a preference *among* placements that passed every hard gate, and a session that
grows beyond its pinned backend is **migrated** rather than refused.

**Admission (what it costs).** A request reserves

```
ceil(prompt_tokens + output_budget + safety_margin)
rounded up to the reservation quantum
```

for as long as it is queued or actively inferring. It is **not** a model window
and **not** a seat. On the server the prompt token count is authoritative
(tokenized after rendering); the client's count is only an estimate and is
corrected on arrival.

The five things the spec required to be separated are distinct objects with
distinct limits:

| Concern | Object | Limit | Held |
|---------|--------|-------|------|
| Caller request concurrency | `caller_inflight` | `max_inflight_per_caller` (32) | request queued or running |
| Caller queue | `caller_queued` | `max_queued_per_caller` (12) | while queued |
| Request context capacity | per-deployment reserved tokens | `deployment_capacity` (from the runtime, not the request) | request queued or running |
| Session affinity | `(tenant, session) → deployment` | none (metadata) | until changed or idle-expired |
| KV / prefix retention | `(tenant, session, deployment) → tokens` | soft, TTL-bound, evictable under pressure | TTL or eviction |

The **hard request lease** is the only one that consumes admission capacity. It
is released on every terminal path via an RAII guard (Rust `AdmissionGuard`,
Python `finally`), release is **idempotent** with double-releases counted as a
metric, and a **reaper** recovers any lease that outlived its deadline — a
crashed or disconnected request cannot permanently leak a permit.

**Rollback is a mode, not a restore.** `fixed` / `shadow` / `weighted`. In
`fixed` the operator chooses the legacy reservation; in `shadow` the legacy
decision is enforced and the weighted decision is recorded beside it for
divergence measurement; `weighted` enforces the new arithmetic. All three keep
discovery, reasons, and metrics live. The rollback reservation **must not** be
262144 or 260000 (validated), and the conservative floor everywhere is **128,000**
— no generic 260K fallback exists in any layer.

## 3. The Pi integration

Implemented through Pi's **supported provider and extension surface only** —
no fork, no patch to Pi core.

- `registerProvider()` with a `refreshModels()` callback; the callback fetches
  `/v1/models` plus the per-model capability document and maps
  `guaranteed_routable_tokens` → Pi `contextWindow` and `max_output_tokens` →
  Pi `maxTokens`.
- A **shared process-local discovery cache**: TTL, ETag/`If-None-Match`,
  single-flight refresh, timeout, `AbortSignal`, stale-if-error, and a
  diagnostics `inspect()`. No subagent hammers `/v1/models`; a refresh failure
  returns the last known list, and the last known good capability is used while
  fresh.
- Precedence exactly as specified: `guaranteed_routable_tokens` →
  `context_window` → `max_model_len` → local override → fresh last-known-good →
  conservative 128K. `260000` and `262144` are rejected as fallbacks.
- A local override above the gateway's guarantee is refused unless
  `allowUnsafeOverride` is set, and produces a warning either way.
- **Model switch**: `planModelSwitch()` returns `none` / `compact` / `reject`.
  A switch to a smaller window triggers Pi's **native** `ctx.compact()` before
  the next dispatch (no competing summarizer); an impossible switch is refused
  before the request is sent. Pi's own overflow recovery is untouched.
- **Status bar**: a context segment inside the existing harness footer
  (no competing footer), dropping before model/throughput on narrow terminals:
  `acme/qwen3.8-27b │ ctx 143k/262k 55% │ ⚡ 31.0 t/s`.
- `/iw-context [model]` shows resolved window, basis, generation, source,
  freshness, heterogeneity, cache age, last error, and session usage.

## 4. Observability

Added **to the existing dashboards and metrics**, not beside them:

- **Node dashboard** (`autospec-inferweave/linux-turing-dual/web/index.html`):
  a Context tab — admission mode in force, live hard request leases, reserved
  context against published capacity, per-caller in-flight and queued, lease
  hygiene (orphan reclaims, **double releases flagged as the bug alarm they
  are**), refusals grouped by their own reason, and the published capability
  table (advertised vs max routable, output cap, freshness with age, provenance,
  generation). It renders `/api/context` and does not recompute anything.
- **Gateway endpoints**: `/api/context`, `/v1/models` (OpenAI shape +
  capability extension + `ETag`/304), and `/v1/models/{model}/capabilities`
  (capability document, `ETag`/304, 404 when unknown).
- **Rust** (`context_admission.rs` `AdmissionMetrics`): admitted, rejections by
  reason, double releases, orphan reclaims, caller records pruned, inflight
  requests, reserved tokens, and per-deployment capacity — the source an
  exporter reads.
- **Client** (`/iw-context` + `inspect()`): the Pi-side view of the same
  numbers.

No raw prompt contents or sensitive context are logged; only token counts and
ids.

## 5. Tests that were actually run, with results

| Suite | Result |
|-------|--------|
| `inferweave-impl` `cargo test -p iw-core --lib` | **253 passed, 0 failed** |
| `inferweave-impl` `cargo test -p iw-core --test dynamic_context_capabilities` | **11 passed, 0 failed** |
| `inferweave-impl` `cargo test --workspace --offline` | green |
| `inferweave-impl` `cargo clippy -p iw-core --all-targets` | 0 warnings |
| `inferweave-impl` `cargo fmt --all --check` | clean |
| `inferweave-impl` `cargo run -p schema-gen -- --check` | no drift |
| `pi-engineering-runtime` `npx tsc --noEmit` | clean |
| `pi-engineering-runtime` `npx biome check src test extensions` | clean |
| `pi-engineering-runtime` `npm test` | **477 pass, 1 skipped, 0 fail** |
| `autospec-inferweave` `linux-turing-dual` + repo `pytest` | **727 passed, 1 failed (pre-existing, fails identically on the clean branch)** |
| `autospec-inferweave` `linux-qwen38` `pytest` | 12 passed |
| `autospec-inferweave` structural suites (turing, qwen38, leak guards) | all pass |

New tests written for this work: **89** — 11 Rust integration, 42 Python
(28 capability + 14 endpoints/routing), 36 TypeScript (capability 10, client 10,
provider 6, status 10).

The specific cases the spec required, and where they are:

- **32K / 64K / 128K / 262K / 1M matrix** — Rust `dynamic_context_capabilities.rs`
  and Python `test_unit_context_capabilities.py`.
- **Capability response matrix** (`context_window` only, `max_model_len` only,
  both, neither, invalid fields, conflicting fields, stale data, safe/unsafe
  override) — both languages.
- **Pi provider refresh and fallback** — `context-client.test.ts`,
  `context-provider.test.ts`.
- **Model switching `1M → 128K` and `128K → 1M`** — `context-capability.test.ts`
  (`planModelSwitch`) and Rust routing tests.
- **Heterogeneous routing** — Rust `route()` (180K never reaches a 128K backend;
  700K only to a 1M backend) and Python `test_unit_context_endpoints.py`
  (the full matrix, plus "a warm 128K affinity does not capture a 200K request").
- **Concurrent small and large requests** — Rust `concurrent_small_and_large_requests_stay_inside_capacity`.
- **Idle-session regression (≈100 sessions, ≈5 active)** — Rust
  `idle_sessions_do_not_consume_caller_permits` and Python
  `test_one_hundred_sessions_five_active`: hard permits track the 5 active, not
  the 100 sessions.
- **Leak soak** — Rust `leak_soak_ends_with_zero_orphan_reservations` and Python
  `test_leak_soak`: request / cancel / disconnect / upstream failure / routing
  failure / retry / completion, ending with **0 orphan reservations** and
  `hard permits == actual active`.
- **Double-release** — counted, asserted, and asserted idempotent in both
  languages.
- **Rollback is not "restore permanent 260K"** — `test_rollback_mode_is_a_mode_not_a_restore`
  and the fixed-reservation validation that rejects 262144/260000.

## 6. Benchmark, before / after

`linux-turing-dual/scripts/context_admission_bench.py`, a **deterministic
discrete-event capacity-accounting simulation** (not a GPU benchmark): 100
logical sessions, 12 concurrent, 600 s, output budget 2048, the required mix
(70% ≤32K, 20% 32–128K, 8% 128–256K, 2% >256K), strict FIFO head-only admission,
identical workload and seed for both arms. Machine-readable results in
`linux-turing-dual/docs/bench-context-admission-*.json`.

**Homogeneous, 4 × 262,144-token backends, model window 262,144:**

| Metric | Legacy (full-window) | Weighted | 
|--------|----------------------|----------|
| Acceptance rate | 16.4% (44/283) | **95.5% (211/223)** |
| Context refusals | 224 | 5 |
| Caller-concurrency 429s | 0 | 0 |
| Peak accepted concurrency | 4 | 28 |
| Mean TTFT / p95 TTFT | 32.4s / 47.4s | 14.9s / 35.9s |
| Mean queue / p95 queue | 26.3s / 29.9s | 9.4s / 25.2s |
| Throughput | 2,830 tok/s | **12,286 tok/s (4.3×)** |
| Mean reserved, a ≤32K request | 262,144 | **24,626** |
| Mean reserved, a 32–128K request | 262,144 | 92,017 |
| Overflow incidents | 0 | 0 |

A 4K-class request reserved **262,144** tokens under the old behaviour and
**24,626** under the new one — the spec's "20K consumes substantially less than
250K" is the whole point, and it is measured.

**Heterogeneous, 131,072 + 262,144 + 1,048,576-token backends, model window
1,048,576:**

| Metric | Legacy | Weighted |
|--------|--------|----------|
| Acceptance rate | 3.9% (11/296) | **100% (214/214)** |
| Context refusals | 270 | 0 |
| Peak accepted concurrency | 1 | 32 |
| Mean queue / p95 TTFT | 26.1s / 47.4s | 2.2s / 25.3s |
| Throughput | 709 tok/s | **15,097 tok/s (21×)** |
| Capacity utilization | 72.7% | 100% |
| Capacity amplification avoided | — | **0.73** (legacy reserved 73% more) |

Under the old behaviour a heterogeneous fleet served essentially one concurrent
request, because every request — including a 4K one — reserved the **1M** window
of the largest backend. The weighted arm uses the fleet at full utilization
because each request reserves what it occupies.

The >256K class is accepted 0/8 in the homogeneous arm: with a 262,144-token
model window, a >256K prompt plus a 2048-token output **exceeds the model's
guaranteed context**, so those are correctly refused as
`model_context_exceeded` (413) rather than admitted and then killed by the
backend. That is the intended failure, not a gap.

## 7. Independent review findings and fixes

A focused adversarial pass over the four repos — leaked permits, double release,
race conditions, cancellation races, arithmetic overflow, unsafe capability
expansion, stale metadata, incorrect heterogeneous routing, model switches,
tenant/session isolation, KV cache isolation, backwards compatibility, error
paths. Four real defects found, all fixed and regression-tested:

1. **Self-blocking weighted mode.** The weighted hook sized the per-deployment
   ledger from the *request's own predicted peak*, so the ledger's capacity was
   the size of the request trying to enter it — `weighted` mode refused
   essentially everything. Fixed to size the ledger from the **deployment's
   context** (observed runtime value, or a configured capacity), not the request.
   `fix(context): size the weighted ledger from the deployment, not the request`.
2. **Promoted queue entries invisible to the caller limit.** A request that was
   queued, then promoted to running, was decremented from the queue and
   incremented to in-flight, but the promotion path did not update the caller's
   in-flight count, so a caller could exceed `max_inflight` while looking idle.
   Fixed; the queue and in-flight dimensions now both move on promotion.
   `fix(context): count a promoted queue entry as the active work it became`.
3. **Shared refresh cancelled by one caller.** The Pi shared capability client
   created its in-flight refresh with the **first caller's** `AbortSignal`; when
   that one caller cancelled, the fetch aborted and every other caller waiting on
   the same refresh lost it. Fixed by counting waiters: a refresh is aborted only
   when its **last** waiter leaves. `fix(context): a cancelled caller must not
   cancel the refresh others are waiting on`.
4. **Unbounded caller map in the Rust ledger.** Per-caller accounting records were
   created on first sight of a caller-supplied id and never dropped, so any fleet
   with rotating or anonymous callers grew a map for the life of the process,
   with no capacity symptom to point at. Fixed: emptied records are pruned by the
   reaper (and via `prune_idle_callers()`), counted as
   `inferweave_admission_caller_records_pruned_total`.
   `fix(context): prune emptied caller records so the ledger cannot grow forever`.

Also addressed during review: a `now: undefined` optional-dependency defaulting
bug in the Pi client; a provider stampede (one capability request per listed
model) bounded by `INFERWEAVE_MAX_CAPABILITY_LOOKUPS`; an override-parser that
accepted only one of the two documented spellings; the nginx gap for
`/api/context` and the installer gap for `context_capabilities.py`, **both caught
by this repo's own structural guards rather than by a reviewer**; and tenant
isolation of affinity and KV state (keyed `(tenant, session)` and
`(tenant, session, deployment)` respectively).

## 8. Rollout, flags, and configuration

**InferWeave node** (`autospec-inferweave/linux-turing-dual`, env):

| Variable | Default | Meaning |
|----------|---------|---------|
| `QT_CONTEXT_ADMISSION_MODE` | `shadow` | `fixed` (legacy reservation enforced) / `shadow` (legacy enforced, weighted recorded) / `weighted` (weighted enforced) |
| `QT_CONTEXT_FIXED_RESERVATION` | 32,768 | Legacy-mode reservation. **Rejects 262,144 and 260,000.** |
| `QT_CAPABILITY_STALE_SECS` / `QT_CAPABILITY_EXPIRE_SECS` | 300 / 3600 | Freshness windows. Stale data never expands a promise. |
| `QT_CONTEXT_AWARE_ROUTING` | `1` | Advertise the largest backend because placement filters on context; `0` advertises the smallest. |
| `QT_ALLOW_UNSAFE_CONTEXT_OVERRIDE` | `0` | Permit a local window above the guarantee. |
| `QT_CONTEXT_MAX_INFLIGHT` / `QT_CONTEXT_MAX_QUEUED` | 32 / 12 | Per-caller concurrency and queue limits. |

**Pi** (env, all optional): `INFERWEAVE_BASE_URL`, `INFERWEAVE_ENABLED`,
`INFERWEAVE_PROVIDER`, `INFERWEAVE_API_KEY`, `INFERWEAVE_TTL_SECONDS`,
`INFERWEAVE_STALE_SECONDS`, `INFERWEAVE_TIMEOUT_MS`,
`INFERWEAVE_MAX_CAPABILITY_LOOKUPS`, `INFERWEAVE_MODEL_CONTEXT`
(`model:window[,model:window]`), `PI_STATUS_BAR_SHOW_CONTEXT`.

**Staged rollout**, per the spec: baseline instrumentation (already live) →
capability discovery (live) → **shadow** (default; nothing enforced) → canary
enforcement (`weighted` on one node) → general enforcement → KV/affinity tuning.
Rollback at every stage is a mode switch, and discovery, reasons, and metrics
survive the rollback.

## 9. Migrations performed

- `~/.pi/agent/qwen-nodes.json` is the operator's static config; the Pi
  extension now **discovers** context from the gateway and uses that file only as
  a local override, so the 262144-in-every-model entry is superseded in place
  rather than requiring a separate migration. No client was forked.
- No schema or API breaking change: `/v1/models` keeps its OpenAI shape with an
  additive `inferweave` extension and standard capability fields;
  `/v1/models/{model}/capabilities` and `/api/context` are new; the Rust
  OpenAPI schema was extended and bindings regenerated with no drift.
- No existing behaviour removed: the legacy seat pool and legacy tier
  reservation are still present and still enforced in `fixed` mode.

## 10. Review findings and remaining limitations (honest list)

- **The benchmark is capacity accounting, not GPU measurement.** It proves the
  admission arithmetic and its fairness; it does not measure TTFT under real
  prefill, KV cache hit rates, or OOM. Real-fleet validation (shadow mode on one
  node, comparing recorded weighted decisions against enforced fixed decisions
  for a day) is the next step before canary enforcement.
- **The authoritative prompt token count is the server's**, computed after
  rendering; the client estimate is a floor. If a deployment cannot report a
  token count, admission falls back to the estimate plus the margin, which is
  conservative but not exact.
- **`weighted` mode enforces on the gateway's own ledger**, which is per-node.
  A fleet-wide admission decision still requires the InferWeave control plane to
  aggregate node ledgers; `iw-core`'s `ContextAdmission` is the unit that does
  that, but the cross-node aggregation service is out of scope for this change
  and is where `caller_records_pruned` and the reaper become visible fleet-wide.
- **The Pi `contextWindow` is set from the gateway at model-registration time.**
  A model whose guarantee *shrinks* while a Pi session is open is caught by the
  model-switch guard on the next switch and by Pi's own overflow recovery, but
  not proactively mid-session; that is a known, bounded gap.
- **One pre-existing Python test fails on the clean branch too**
  (`test_every_advertised_model_is_claimed_by_a_server`) — it is not caused by
  this work and fails identically before and after.

## 11. Where the code is

| Repo | Branch | What |
|------|--------|------|
| `inferweave-impl` | `feat/dynamic-context-capabilities` | `model_capabilities.rs`, `context_routing.rs`, `context_admission.rs`, `lib.rs`, OpenAPI schema + regenerated bindings, `tests/dynamic_context_capabilities.rs`, architecture doc, CHANGELOG |
| `pi-engineering-runtime` | `feat/dynamic-context-capabilities` | `src/context/{capability,client,provider,usage}.ts`, `src/status/*`, `extensions/index.ts`, tests, `docs/usage.md`, evidence report |
| `autospec-inferweave` | `feat/dynamic-context-capabilities` | `linux-turing-dual/scripts/context_capabilities.py`, `gateway.py` wiring, `context_admission_bench.py`, tests, nginx + installer, dashboard Context tab, docs + benchmark JSON |
| `inferweave-specs` | `spec/dynamic-context-capabilities` | this bundle + `docs/specs/README.md` + CHANGELOG entry |

Four ledger entries record the root-cause finding, the review findings, and the
no-260K-fallback decision.
