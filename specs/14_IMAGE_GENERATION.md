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
