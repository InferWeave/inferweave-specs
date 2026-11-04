# 10 — Next.js Dashboard, Portal and Public Proxy

All web surfaces use **Next.js + TypeScript** and shared generated InferWeave API types,
subject to the narrow existing embedded site-gateway exceptions in D-002. Spec 58
defines model-intelligence integration into that existing UI; it does not create a
second frontend.

## Public/read-only dashboard

Routes may include:
- `/`
- `/capacity`
- `/models`
- `/gpus`
- `/nodes`
- `/benchmarks`
- `/contributions`
- `/status`
- `/docs`
- `/about`
- `/connect`
- optional `/play`
- later `/economics`

Show useful ready capacity first.

Capacity views read waiting work from the structure that orders admission
(`04_CAPACITY_ADMISSION_SEATS.md`), never from a separate collector that observes only
executing requests.

A per-resource capacity view shows context occupied, the sessions holding it, context
remaining, and how many further clients fit at common context sizes before requests begin to
queue.

## Machine-checked presentation policy

Presentation requirements are enforced by a policy the build checks, not by review.

A policy file maps each route to the rendering variants it must be proven under, at minimum:

- `default` and `narrow` viewport;
- `forced-colors`;
- `reduced-motion`;
- `wired` against live contract data, or `fixture` where a live surface does not yet exist;
- `unsupported`, the state shown when a required capability is absent.

The policy also names the single token source every surface draws colour, spacing and type
from, and a denylist of superseded components that must not reappear.

Accessibility and theming stated only in prose are not enforced, and regress silently at the
first route added under deadline. A route absent from the policy fails the check rather than
defaulting to unconstrained.

## GPU explorer

For each privacy-safe GPU/service view display appropriate public-safe fields:
- GPU model/architecture/VRAM;
- region band;
- active deployment/model;
- context envelope;
- TTFT/prefill/decode/aggregate benchmark ranges;
- utilization/power/temperature bands;
- reliability/qualification band;
- contribution totals/accepted work aggregates;
- exact benchmark fingerprint details that do not reveal secrets/private addresses.

Operators with authorization can view deeper telemetry, settings and historical charts.

## Global benchmark explorer

Filter/compare:
- GPU;
- model/revision;
- runtime/backend/version;
- quantization/precision/KV precision;
- context;
- concurrency;
- batching/attention/speculative settings;
- workload class;
- cache hit/miss;
- power/thermal envelope;
- software/container fingerprint.

Never display ambiguous cross-model universal TPS rankings without dimensions.

### Public task inspection navigation

The authoritative data for a public review is the current Rust-exported snapshot
whose manifest hashes have been verified by the server. A known task is a
canonical `family/task` key present in its `tasks`, `suite_tasks` or
`task_prompts` collections; the split is on the first slash. A known observation
is an exact `observation_id` in the snapshot's validated `configurations`
collection. Community submissions and model names/timestamps do not stand in for
that observation identity.

The existing application-profile identifiers are `balanced`, `coding`, `logic`,
`science` and `tool-use`. A missing profile uses the existing `balanced` default;
an explicitly supplied empty or other value is invalid. Validity is against this
profile vocabulary, not a claim that an observation has measurements for every
profile: a valid but unmeasured profile must retain the model view's explicit
"Not measured" state, never substitute another profile's score.

Required public behavior (IW-UI-002 / P2-T18 UI E2E):

1. A configuration or comparison task-result row links to its existing public task
   page only when that exact canonical task key is known. Otherwise the recorded
   task name remains plain text; no definition or prompt is invented.
2. A contextual return is available only for a known task and a nonempty known
   observation. Each of `task`, `observation`, `compare` and `profile` occurs at
   most once. If `compare` is present it is nonempty, known and distinct from the
   first observation. Repeated keys are ambiguous even when their values agree.
3. Valid context preserves the exact observation and profile; a comparison also
   preserves the second observation. The return opens that configuration or the
   same comparison pair. Browser Back restores the preceding inspection state.
4. Unknown observations, duplicate identities/keys, invalid profiles and empty or
   unknown comparison references omit the contextual return link. The known
   public task page and its ordinary Back-to-Benchmarks link remain usable. No
   alternative configuration or profile is selected for that return.
5. A nonempty requested task key absent from the snapshot shows the catalogue with
   the generic status "The selected task is not available in this snapshot."
   The unknown key is not echoed; no task detail, prompt or contextual return is
   invented. A known task without published prompt content keeps its existing
   absent-prompt disclosure.

These links carry public review context, never content-read authority. The
required tests cover both valid roundtrips and the invalid/ambiguous cases above;
private prompt history remains governed separately below and by spec22.

## Authenticated portal

Authentication for authenticated portal surfaces follows decision
`2026-10-25-bench-cognito-auth.md`: Cognito is the single identity authority for
local User Pool users and Google federation. The application maps verified
`(issuer, sub)` identities to local roles and never treats an email address or
browser-provided identity header as authority.

The browser uses Authorization Code + PKCE through Cognito Managed Login. Raw
prompts, generated outputs, traces and artifacts require reviewer/admin grants;
aggregate benchmark views remain content-free. New users start as viewers and
must receive elevated roles through an audited application action. The security
qualification and production deployment gates remain separate and blocked until
the decision's proof obligations pass.

- API keys;
- usage;
- prompt/session/request history where authorized;
- saved routing policies;
- provider contribution history;
- node/GPU telemetry and benchmark history;
- CI/build/Pi-review history;
- operator policy/routing/queue views.

## Prompt history

Authorized users can inspect prompt/session history for records that reached a
durable sink. The UI must disclose gaps reported by recorder loss metrics and
must not imply complete history. Access control comes from the prompt ledger and
every privileged content read is audited.

## Node administration

Hosted dashboard is not the authoritative node secret/config/install/update surface. Local node administration remains authoritative unless a later ADR defines secure remote management.

## Live updates

Use server components/static rendering for stable catalog pages and SSE/WebSocket or efficient polling for live capacity/telemetry. Browser update strategy must not force inference traffic through Next.js or gateway servers.


## Ephemeral-resource views

Authorized cluster views show:
- stable host/GPU identity;
- currently connected worker/allocation;
- reservation time remaining;
- historical allocations;
- cumulative serving/benchmark contribution;
- performance history;
- runtime/model history;
- temperature/power/health trends;
- current gateway-assigned desired deployment;
- cached artifacts;
- reconnect/rediscovery events.

A returned known node should visibly continue the same resource history rather than appearing as an unrelated new GPU.
