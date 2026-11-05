# Legacy NVIDIA bounded integration evidence

Feature IDs: IW-REC-001, IW-REC-002, IW-TUNE-001, IW-BENCH-002.

Source requirement archive SHA256:
`60e340207a449c23e3bd12507794191bd3c747d87bc577ac5ee90880f7049e3f`.

Implementation [PR #1457](https://github.com/InferWeave/inferweave/pull/1457)
merged as `50e9f3d87caa1bb401a4687444d34c57cf9bd749`. It extends the existing
catalogue, eval runner, immutable record store, qualification and private workbench;
it introduces no parallel registry, scheduler, runtime controller or warehouse.
The original dirty checkout and concurrent changes were preserved.

The pinned [implementation evidence report](https://github.com/InferWeave/inferweave/blob/50e9f3d87caa1bb401a4687444d34c57cf9bd749/docs/benchmarks/legacy-gpu-integration-follow-up-2026-11-04.md)
records the owned single-TITAN RTX Slurm pilot and authenticated private central
intake/replay. This specification does not independently reproduce its performance
figures and makes no numerical performance claim. The pilot is experimental
single-card Turing smoke evidence; it does not qualify either exact dual-card
sm61/sm75 target, Pascal kernels, concurrency, vision or broad agent quality.
Private raw records remain outside Git; private intake/replay establishes neither
public publication nor production profile promotion.

The merged conductor uses versioned stores: v1 preserves historical leaf IDs and
legacy replay compatibility; new v2 stores retain canonical record IDs. Historical
v1 envelopes remain ineligible for generic canonical-store reads, coverage and
publication. Never relabel them as v2 or weaken canonical record validation.

Full AC-MI-08 remains **owed** and exact-target production qualification remains
**UNSATISFIED**. Compatible pinned builds, actual loaded artifact identity,
independent memory/quality/stability evidence, owner-authorized leases, safe
fallback and deployment review remain required. The occupied legacy targets and
other owner workloads grant no benchmark or preemption authority.
