# InferWeave Model Intelligence & UI Cohesion — Master Implementation Specification
Version: 1.0 | 2026-10-12 | Implementation target: Codex multi-agent

## 0. Scope and absolute constraints

Repositories (verify actual remotes during bootstrap):
- `metabolomics-us/inferweave-gateway` — existing web UI and gateway-facing administration adapter
- `inferweave/inferweave` — authoritative inference metrics, model registry, routing and optimization domain logic
- `inferweave/inferweave-spec` — specification storage if accessible / conventional to this project

**Do not replace the existing UI.** All pictures are *conceptual* references, not proof of actual existing screens, colors, layout, or navigation. The existing application is the source of truth for tokens, components, URLs, role permissions, interaction patterns, technology stack, and retained behavior. Do not blindly copy mockup branding or color values. Do not rename routes without explicit compatibility bridges. Existing UI flows must keep working. Add new details within relevant existing screens and introduce only genuinely necessary navigation.

Before any code: inventory current pages, route map, providers/state, design tokens, component library, chart implementation, existing statistics, access controls, responsive behavior, dark/light themes, test suite, API contracts. Screenshot current app in both themes (running locally with non-sensitive sample fixture), record baseline. Record conflicts between mockups and actual UI; defer to current UI. If repo/API inaccessible, stop claims about current source and use environment's authorized checkout, never invent source structure. Use one cohesive system of shared components; no parallel frontend or duplicate domain services.

### Non-goals
No replacement app, no hard-coded mock numbers in production, no unsolicited upstream resource commands, no massive migration, no model auto-switching without opt-in policies, no indiscriminate raw prompt logging, no duplicative metrics computed by the UI, no speculative cost presented as measured.

## 1. Product objectives and information architecture

Questions answered: reliability, availability, preemption, speed, safe request/user concurrency, input/output/cache usage, effective cost, capability by task, intelligence by version, historical changes and task-matched alternatives. All views have global time range, models, gateway/tenant scope, provenance, filters, unit tooltips, loading/empty/error states, and meaningful export if existing patterns permit.

Placement principle, *adjust after UI inventory*:
- Existing overview: fleet health cards and mini charts including logical tokens and exclusive token composition.
- Existing models list: sortable availability/success/TTFT/speed/safe-concurrency and comparison action.
- Existing model detail: reliability, speed/capacity, token economics, capability history, incidents and profile selection, without losing existing settings.
- Existing usage/cost page: stacked daily exclusive token buckets, logical vs billed vs physical work, workload attribution, cost per completed task, baselines.
- Existing nodes/GPUs: per GPU VRAM components, deployed models, KV/cache, Slurm events, preemption recovery and headroom.
- Existing routing/provisioning: recommendation candidates, shadow evaluation, safe opt-in rollout.
- Existing logs/events: linked incident timeline, cause and impact.
- Comparison route only if existing affordances cannot accommodate comparison. No duplicated charts or menus.

Breakpoints: desktop, tablet, mobile; keyboard accessibility, screenreader names, WCAG contrast; theme parity; timezone-aware time scales; consistent decimal precision, statuses and units; responsive tables with scroll/column priority; skeleton loading.

## 2. Metric semantics (must be implemented and tested)

### 2.1 Identity and aggregation
Dimension keys: `logical_request_id`, `attempt_id`, `trace_id`, `tenant_id`, `user_id` (hashed/privacy-scoped), `mission_id`, `gateway_id`, `worker_id`, `node_id`, `gpu_id`, `slurm_job_id`, `model_id`, `model_version`, `quantization`, `runtime_family`, `profile_id`, `hardware_class`, `region`, `time`. Label cardinality limits; never place unique IDs in Prometheus metric labels. Every aggregate must specify cohort, numerator/denominator, coverage, units, source/measurement status and time window.

### 2.2 Request outcomes
Separate: transport success, inference-attempt success, logical-request success after retry/fallback, task-success from downstream feedback, and model-serving availability. Define denominator per metric and exclude client cancellations only when policy is explicit and chart tooltip states exclusions. Error taxonomy: preempted, Slurm reclaimed, insufficient multi-GPU world-size, OOM, runtime crash, timeout, rejection, queue expiry, model unload, network error, client cancelled, output invalid, failed task, other, unknown. Preserve attempt-level cause chains; do not count multiple retries as distinct users.

### 2.3 Availability and preemption
Observe modeled state (available/healthy, loading, queued, recovering, preempted, failing, administratively disabled, unknown). Distinguish `replica_up`, `model_advertised_available`, `serviceable_within_SLO`, `logical_request_served`. Availability denominators include eligible requested time with explicitly documented maintenance exclusions; no traffic means unknown demand, not automatic success. Link worker/Slurm lifecycle to affected logical requests and failovers. Record preemption rate per replica-hour / GPU-hour and requests interrupted; recoveries and registration transitions.

### 2.4 Token accounting (canonical exclusive categories)
At request attempt boundary, record `input_total`, `input_uncached`, `input_cache_read`, `input_cache_write` (when separately measurable), `output_visible`, `output_reasoning` (if reported and included in total), `output_total`, `cache_source`, `tokenizer_id`, `reported_or_estimated`, `provider_billed_input/output/cache_*`, `usage_coverage`, and `raw_provider_usage` retained appropriately. Never sum nested totals with subsets. `cache_write` may be a subset of input total depending on engine contract: normalize to **exclusive** buckets for display only when upstream semantics justify that decomposition; otherwise show separate overlap annotation/unknown. Derive `logical_input = input_uncached + input_cache_read + exclusive_cache_write + unknown_input` only when mutually exclusive. Report attempt-level compute tokens separately from logical request-level, because retries may duplicate physical usage. Cache hit ratio denominator must be explicit; zero-data should be N/A. If old samples lack breakdown, show **unknown**; do not fabricate/cache-backfill from total count. Normalize runtime adapters (OpenAI-compatible and other runtime families) through capability-aware telemetry contracts; respect unsupported statuses.

### 2.5 Speed and concurrency
Measure queue wait, scheduler time, TTFT, per-request inter-token latency, decode output tokens/s, prefill throughput when measurable, end-to-end latency, completed requests/min, aggregate decode throughput, request-level decode throughput; p50/p95/p99 plus counts and CI where appropriate. Separate concurrency of connections, in-flight logical requests, attempts, decode sequences, slots, sessions, agents, and distinct active user IDs. Estimate **safe sustainable request concurrency** for model+profile+hardware+workload bin based on historical SLO-compliant bins with min sample count; confidence/coverage/last-observed date. Avoid pretending observed requests equals active humans. Estimate user-equivalent capacity only when a defined workload mix and requests/user relationship are available; show scenario confidence. Compare equivalent prompt length, cached percentage, output length, batch size and latency targets. Report saturation curves, queueing and preemption impact. Historical data should not imply ability to extrapolate beyond observed load; display unmeasured territory.

### 2.6 Cost and normalization
Self-hosted actual: GPU reservation/active/slice accounting, GPU-seconds, shared-model attribution allocation policy, amortized compute/power if configured, storage and transfer if relevant; unconfigured dollars = unknown, not $0. External price: versioned provider/region rate-card separate uncached input/output/cache-read/cache-write, reasoning/billing distinctions, date effective, sensitivity to context tiers. Avoid double-counting shared GPU occupancy. Show cost/1M input vs output vs cache read/write, and **cost per successful task** with retries, plus cost per 1M logical tokens only with token mix breakdown. Cost simulations marked as estimated with intervals. Normalize task, quality threshold, latency SLO, workload shape and hardware for fair comparisons.

### 2.7 Capabilities and intelligence
Versioned evaluation suites per task family: coding, tool use, agent completion, reasoning, math, summarization, embedding, rerank, speech recognition/TTS, vision, prediction. Record suite version, dataset provenance, score direction, sample count/CI, latency, resource profile, tokenizer/model revision. Do not invent a global 'intelligence' score; offer per-task normalized measures plus transparent composite weighting if explicitly configured. Protect evaluation sets from leakage when possible. Publish score timeseries with deployments/config changes; benchmark vs production quality separate.

## 3. Recommendations and routing safety
Recommendation candidate engine in `inferweave/inferweave`, not frontend. Build Pareto selection with task constraints: required tools/context/modality/output schema/quality policy, observed success, p95 TTFT/latency, hardware fit/VRAM/KV, concurrency, confidence and availability under preemption. Present expected saving and uncertainty, evidence window and sample size, alternative availability on *current owned hardware*. Use profile-specific quantization and placement. Never conflate a published benchmark with verified local runtime performance.

Workflow: discovery -> eligibility -> offline benchmark -> shadow run/replay where privacy-safe -> canary under limits -> opt-in promotion -> rollback. Default recommendation only, no automatic upstream resource commandeering. Downstream advertises resources voluntarily; policy authority remains downstream. Feed existing rebalancer and routing interfaces, not new competing ones. Preserve currently defined gateway control boundary.

## 4. Backend APIs and lifecycle
Reuse current OpenAPI/client types/transport. Add versioned endpoints only after discovering existing conventions, for model telemetry summary, timeseries query, incidents/preemptions, token economics, capacity curve, evaluations, comparative candidates, cost reports. Allow pagination and time-bucket granularity, `coverage`, `metric_definition_version`, aggregation dimension, `as_of`, unit, error reasons. Use server-side aggregation/rollups; configurable retention (e.g. raw 7-30d, 5m 90d, daily long-term, subject to policy); object artifacts/evaluations to RustFS when supported, not a new silo. Reuse existing telemetry/event system. Backfill only where data is actually present, mark missing unknown.

Domain owners: InferWeave = metrics, cost/capability/capacity, routing recommendations and policies; metabolomics UI = presentation, filters, permissions and authorized API mutations. Avoid duplicating calculations across gateways or UI. Use existing authn/authz, tenant isolation, audit logs and data retention; sensitive request content never needed for core metrics.

## 5. Cohesive design system
Strictly derive existing colors, typography, spacings, radii, shadows, icon set, grid breakpoints, badges, chart palette, tab treatments, tables and sidebar from checked-out UI. Extract tokens into shared variables only when not already centralized; migrate duplicate styling incrementally. Use semantic variables: surface / surface-muted / text / text-muted / border / positive / caution / critical / informative / chart 1..N; ensure light/dark contrast and color-blind-safe legend/text distinction. Reuse existing charts/components; if charts lack required features, extend once in shared library. Screenshot references are *information hierarchy* examples only; do not install an unrelated dashboard template. Preserve keyboard focus, tooltips, table sorting, feature flags, saved UI preferences where present.

Cleanup goals after audit: repeated KPI cards, duplicated filters/toolbars, inconsistent formats, oversized navigation, redundant charts, stray style literals, dense control arrangements, mobile overflow and confusing error status names. Refactor only with behavior-preserving tests. Explicit forbidden actions: deleting old screens merely to fit concepts, renaming product or sidebar, introducing second theme switch, changing admin workflows, replacing state management for style alone, assuming mock model names/values are real.

## 6. Visual references / wireframes
`reference/01_visual_reference_board.png` contains 10 concept panels (dashboard, models, details, usage, comparison, GPU, routing, events, mobile, light theme). `reference/02...11*.png` are separate crops for accessibility of review. `wireframes/*.svg` contain **editable annotated wireframes** with module positions and content hierarchy. Apply existing UI design language after screenshots/audit, not the example colors. Mark all fixture values as DEMO and never include them in live production aggregates.

## 7. Implementation workstreams, delegation and token efficiency
Coordinator (Codex) owns scope, architecture, dependency graph, issue/PR sequencing, acceptance and final integration. Parallel subagents with isolated worktrees and no overlapping file ownership:
A. Repo/UI audit + design-system inventory + current screenshot baseline. Small/cheap fast model suited to code reading and inventory; no writes except report.
B. Telemetry domain contracts and adapter semantic audits. Stronger reasoning/coding model for metric correctness; add tests; own inferweave core telemetry modules only.
C. Preemption and capacity estimator with SLO definitions. Strong reasoning model (high complexity), own scheduler/analytics slice only.
D. Token economics and cost engine. Strong model for accounting invariants, moderate coding model for implementation/tests, own backend economics modules only.
E. Capability registry, evaluation schemas, recommendation safety. Strong reasoning model, own evaluation/optimizer slice only.
F. Frontend components/style unification. Fast economical coding model for repetitive UI work after audit, own shared UI components only.
G. Page integrations/chart views. Fast/moderate coding model, own targeted page components, serial or partition by route to avoid conflict.
H. Test/review/security/performance. Reviewer model with high reasoning for accounting/availability invariants and security; separate verification branch, do not rewrite teammates' files indiscriminately.

Prefer available low-cost capable models for routine reading, tests, docs, UI scaffolding; strong models for tricky failure taxonomy, measurement, economics, cross-repo architecture and review. Codex session orchestrator dynamically chooses *from available models using capabilities and cost*, never invent model IDs or blindly require an unavailable model; do not hard-code model branding. Route tasks according to cost/quality/availability, avoid repeated large context; agents get concise scoped briefs, exact interfaces/files, desired tests and acceptance criteria. Share one canonical plan/decision log/artifact manifest rather than repeated repo scans. Prefer incremental diff context, shared generated schemas, selective test execution and bounded retries. Parallelism bounded by repository hot files, machine capacity and provider quota. Monitor agent progress; timeouts and escalations, not indefinite stuck builds. At most one agent changes shared API schema at a time; explicit interface freezes, integration gates and cherry-pick sequence. Do not grant destructive actions beyond project's permissions.

## 8. Phased acceptance and gates
P0 AUDIT: obtain access to real repo, architecture map, route map, design token inventory, current light/dark screenshots and test baseline. Propose actual integration locations and gap inventory. If unavailable, do not claim done.
P1 DATA: telemetry/event/token semantics and aggregation verified with fixtures for cache nested totals, retry/fallback, multi-GPU preemption, sparse/unknown data, cancellation and agent tasks.
P2 UI FOUNDATION: shared design-system consolidation plus reusable chart components; every existing workflow keeps working.
P3 EXISTING-PAGE INTEGRATION: overview/models/details/usage/nodes/events in place, with working time range/filters/accessible tables and real data.
P4 ADVANCED: task capability, fair cost comparisons, measured capacity and safe recommendations; optional integration.
P5 VERIFY: cross-browser desktop/mobile, light/dark screenshot diffs against actual baseline; no missing controls/route regressions; security/tenant scope; performance budgets; source benchmarks; validate all equations and test coverage. Document migration/rollback and expose feature flags for risky features.

Exit acceptance: old routes and core actions functional; cohesive actual theme; every chart has metric definition and source/coverage; the 100M example can be decomposed when data exists or explicitly unknown when not; request-level success distinct from attempt failures; preemption linked to GPU/worker and logical requests; safe concurrency labeled with confidence and workload/SLO; speed reports meaningful units and percentiles; comparisons use equal workload and token composition; recommended alternative never silently promoted; no duplicate ownership or frontend business logic; all tests and screenshot reviews pass.

## 9. Deliverables
Implementation commits/PRs per workstream, updated product docs, API schemas, migrations, tests, live-design screenshots in both themes, user-visible data definitions, sample data fixtures, changelog, and final audit mapping each requirement to code/tests/screenshots. Store master spec in repo specification convention if available. No silent partial completion.
