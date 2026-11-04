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

Published task results in configuration details and comparisons link to an existing
public task page using its canonical `family/task` identity. A task inspection
preserves the known observation, application profile and, for comparisons, both
observations; its return link restores that context. Unknown or duplicate
observation references, ambiguous repeated context keys, explicitly invalid
profiles and empty comparison references do not produce a contextual return link;
they never substitute a different configuration or profile. Tasks absent
from the published catalogue remain plain recorded results rather than invented
public definitions. A requested task absent from the snapshot is disclosed
explicitly without echoing the unknown identifier or inventing its prompt.
These links carry public review context, never content-read authority.

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
