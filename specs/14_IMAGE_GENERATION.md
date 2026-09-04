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
