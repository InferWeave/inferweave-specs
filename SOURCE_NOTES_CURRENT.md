# Current External Implementation Notes — 2026-09-03

These notes inform implementation choices but do not replace InferWeave requirements.

## MCP

The current MCP 2026-07-28 specification moved to a stateless protocol core, supports header-based routing, cache metadata on list/resources responses, authorization hardening, and a formal extensions model. InferWeave's remote MCP service should target the current stable specification at implementation time and avoid relying on in-memory client sessions.

Official sources:
- Model Context Protocol 2026-07-28 release notes.
- MCP TypeScript SDK v2 documentation.

## Container GPU discovery

Docker Compose supports explicit GPU device reservations and GPU device IDs. InferWeave init must probe the host/runtime instead of assuming all GPUs should be exposed to a container.

Official source:
- Docker Compose GPU support documentation.

These details can evolve; the bootstrap CLI should detect runtime capabilities at installation time.


## Watchdog preservation

Earlier tuning specifications required automatic rollback on GPU reset/illegal-memory faults, OOM below admitted envelope, restart loops, correctness/SLO failures and profile drift, while preserving the previous image/model mounts/environment/cache namespace until rollback succeeds. Production qualification required soak without GPU reset/restart loop plus successful rollback. These are now canonicalized in `specs/36_GPU_WATCHDOG_RESCUE.md`.

## Deployment substrate

Current Docker Compose supports explicit GPU device reservations. Current Apptainer documentation supports NVIDIA (`--nv`) and AMD ROCm (`--rocm`) GPU container execution. InferWeave standardizes persistent deployment on Docker/Compose and Slurm workers on Apptainer.
