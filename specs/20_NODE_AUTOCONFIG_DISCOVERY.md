# 20 — Node Self-Discovery and Auto-Configuration

The node agent should minimize manual provider setup without making unsafe guesses authoritative.

## Discover

On first run and on demand, discover:
- CPU, RAM, NUMA;
- GPU vendor/model/count/VRAM/topology/interconnect;
- driver/runtime availability (ROCm/CUDA/Vulkan);
- storage capacity/performance hints;
- local network interfaces without publishing private addresses;
- installed supported inference runtimes;
- configured/listening OpenAI-compatible local servers;
- locally cached model artifacts where discovery is safe;
- power/thermal telemetry support.

## Propose, do not silently mutate

Generate a proposed node configuration containing:
- candidate runtime adapters;
- deployable model artifacts;
- likely safe initial resource envelopes;
- benchmark plan;
- gateway enrollment/config;
- local admin binding;
- storage/cache roots.

Administrator reviews/applies the proposal. Automatic privileged driver/kernel/BIOS changes are forbidden.

## Model fetch

Model acquisition is resumable, checksum/revision pinned, storage-aware and license-aware. Never download a massive model merely because a model name appeared in a remote request; deployment intent/policy must authorize it.

## Reconciliation

Periodically compare actual hardware/software/runtime/model state to the active fingerprint. Material drift marks affected profiles `REQUALIFICATION_REQUIRED` and can drain them safely.

## CLI

Target shape:

```text
inferweave-node discover
inferweave-node configure --interactive
inferweave-node enroll
inferweave-node deployments plan
inferweave-node deployments apply
inferweave-node tune plan
inferweave-node status
```
