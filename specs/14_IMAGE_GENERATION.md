# 14 — Distributed Image Generation and Visual Artifacts

Image generation is a first-class capability but not required to bootstrap text inference.

## Deployment unit

Schedule a complete immutable pipeline: weights, text encoder, decoder/VAE, adapters, workflow, runtime/container, policy/license and hardware compatibility.

Initial execution adapter may use constrained ComfyUI templates. Public clients never submit arbitrary ComfyUI graphs.

## APIs

- compatible image endpoints where semantics match;
- native async job API for advanced generation/editing;
- resumable ordered job events;
- cancellation;
- artifact access grants.

### OpenAI parameter binding

The public `POST /v1/images/generations` surface (specs/02) is bound to a named,
server-side template through a declared mapping — see
`contracts/image-template-binding.example.json`. Only the template name and its
bound inputs are accepted; clients never supply a workflow graph.

Standard OpenAI fields (`prompt`, `n`, `size`, `response_format`) map directly to
template inputs. Generation controls that have no OpenAI equivalent
(`negative_prompt`, `steps`, `seed`, `guidance`, sampler/shift) are supplied only
through the optional `inferweave` request object or documented `X-InferWeave-*`
headers, so stock SDKs continue to work unchanged. Every artifact records the
resolved seed and settings for reproducibility.

An image deployment is declared as an immutable pipeline manifest — see
`contracts/deployment-manifest.image.example.yaml` (`modality: image`).

## Data plane

Large inputs/outputs normally bypass the central gateway through scoped object/direct/relay transfers. Gateway remains authoritative for auth, reservation, policy and job state.

## Artifacts

Every output has checksum, deployment provenance, ownership/access policy, retention deadline and reproducibility metadata such as seed/settings.

## Annotated technical images

Do not rely on diffusion-generated text/arrows. Use:
generation → grounding/detection/segmentation → deterministic label/arrow renderer → vision QA.

Exact caller label text is preserved. Low grounding confidence fails rather than drawing a misleading annotation.

## Resource safety

Reserve VRAM/RAM/scratch/thermal/bandwidth before execution. Oversized requests fail before host instability. Worker crash leads to bounded retry/terminal error without duplicate accounting.

## Admission probe (model-aware)

A gateway admits an image worker **by observed serving** (spec 42 C4): the
admission probe is a real `POST /v1/images/generations` against the worker,
never a self-report or a health endpoint. The probe MUST be **model-aware**, so
its cost scales with what the model can do cheaply and a large model can still
be admitted:

- The probe request body is the smallest standard generation:
  `{"model": <registered model>, "prompt": "<short fixed text>",
  "size": "512x512"}` plus the advisory step count through the optional
  `inferweave` request object (spec 02): `"inferweave": {"steps": 4}`.
- A conformant image worker **MUST honor `size`** (clamping to its model's
  smallest supported size when 512 falls below it) — every probe is therefore
  bounded by the worker's cheapest generation, whatever the model is.
- A conformant image worker **SHOULD honor `inferweave.steps`** as an upper
  bound on its default step count. A worker that ignores it still passes the
  probe; it just pays its full cost, which is what the probe budget is for.
- The probe has a **budget**. The identity step (`GET /v1/models`) always runs
  at the default budget (30 s): a slow model list is a sick endpoint, not a
  big model. The liveness step (the generation) takes a **model-aware
  budget**: the default is the floor, and a registering worker MAY declare
  `probe_budget_secs` in its registration (how long its small probe
  generation takes on this hardware). The gateway raises sub-default values
  to the default and clamps at a ceiling (300 s), so a genuinely slow model
  (e.g. a 20 B+ diffusion model whose 512²/4-step probe still outlasts 30 s)
  is admitted while a wedged endpoint can never hold admission open
  indefinitely. The budget bounds the observation; it is never a substitute
  for it — the probe is always a real generation, and a worker that cannot
  complete one within its budget is refused (422), not admitted unverified.
- The gateway rewrites the forwarded `model` to the worker's upstream name
  exactly as for routed traffic (spec 42 C3); the probe uses the name the
  worker actually serves, as established by the identity step.

## Workbench/AutoSpec

Workbench displays actual deployment/policy/license/progress/artifacts. AutoSpec may request visual artifacts and route independent vision QA as a separate workflow.

## Sync/async decision and artifact provenance

`/v1/images/generations` may answer synchronously only when the request fits a
bounded budget (small resolution, few steps, short queue wait). Otherwise the
client is directed to the native durable job API (spec 15): submit → ordered
resumable events → artifact access grant, with cancellation. The decision rule
and job shape are shown in `contracts/image-job.example.json`.

Every produced image is recorded as an artifact carrying checksum, deployment
provenance (deployment id, backend, workflow template, pipeline fingerprint),
reproducibility metadata (resolved seed + settings), ownership/access policy and
a retention deadline — see `contracts/image-artifact.example.json`. Bulk bytes
move over scoped direct/relay transfers (spec 08); the gateway stays
authoritative for job state, provenance and access grants.
