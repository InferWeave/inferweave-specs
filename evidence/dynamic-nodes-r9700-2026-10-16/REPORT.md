# P5-T35 / IW-DYNNODE-001 — Operational proof on R9700 (beast), 2026-10-16

The specs/64 dynamic-node contract was proven end-to-end on real hardware, on the operator's
R9700 host, with a node that joined with nothing being given a model, measured, configured and
served over the protocol.

## Environment

- **Host:** `beast` (100.96.156.65) — 2× AMD Radeon AI PRO R9700 (32 GiB each), 504 GiB RAM.
- **Source:** `InferWeave/inferweave` @ `5ac2fdad3691babffbd2889f30d5ae627d0d53b7`
  (detached worktree, debug build). `crates/iw-gateway/src/dynamic_provisioner.rs` present.
- **Engine image:** `ghcr.io/ggml-org/llama.cpp@sha256:815720cb50a090db0c1d48b6e3b2b4ca656c3b99409cf4f31e63ff154ce586c4`.
- **Gateway:** `127.0.0.1:18080`, `IW_DYNAMIC_MODELS=dynamic-models.json`
  (`qwen3.8-27b-modality-vision-quant-q8_k_xl` priority 10; `qwen3.8-flash_next-modality-vision-quant-q8_0`
  priority 5). The node joined unattended via `--admin-secret-file` (`--model dynamic`,
  `--artifact-root <root>`, `--endpoint-host 127.0.0.1`).
- **Production impact:** the host's production vLLM engine + node
  (`iw-beast-qwen27b-mxfp4-262k-{engine,node}`) were stopped for the proof and **restored
  afterwards** (vLLM reloaded to ~34 GiB/GPU, `GET /metrics 200`, throughput log active).

## Acceptance checklist — evidence (each item maps to P5-T35 "Required tests")

1. **Hardware-only register with dynamic facts + capability offer, no telemetry while idle.**
   Node `node_beast` registered hardware-only (role `node`), capabilities
   `[iw.dynamic-node/1, iw.link-chunked-request/1]`, hardware facts 2× R9700 / 504 GiB RAM.
   Node log: `dynamic node: 2 Radeon AI PRO R9700 card(s), artifacts under …, engine dialled at
   127.0.0.1`; `capabilities in force … iw.dynamic-node/1`. `20-serving.json` →
   `nodes[0].capabilities`.

2. **Every card of one assignment is on one node.** The 27B measure and serve assignments both
   carried `gpuIds: [iw-gpu-b7e02b2c…, iw-gpu-d0a2a806…]` — both R9700s on `node_beast`, one
   physical host. (`30-failure.json`, `60-recovered.json`.)

3. **Serve assignment fetches artifacts with size + SHA-256 verified and a cut HTTP download
   resumed.** The 27B GGUF was streamed to `<name>.part`; a download cut at **31,457,991,680 B**
   (the full size, reached over a half-dead HTTPS connection) was **resumed** — the `.part` was
   re-hashed from disk and continued with a `Range` request (206 from the offset), then
   SHA-256-verified and renamed into place. Verified digests (each with an on-disk `.sha256`
   verification record under `artifacts/dep_22865cfe…/`):
   - `Qwen3.8-27B-UD-Q8_K_XL.gguf` (31,457,991,680 B):
     `af36ecb6b5db1407953345b746c14ac93f0657dda413910b4348683a2d990377`
   - `mmproj-F16.gguf` (927,607,488 B):
     `cbb841a9ee0636b2ec172f5bb8df2ea8dfeb01e90fe7c6126581d662a0b4e43e`

4. **The deployment id is the one derived from the entry's payload.** The verified artifacts live
   under the derived reservation dir `dep_22865cfe1d53383c6d549bd358414487b2ee3866d414f3d93da31f71749fef1e`;
   the serve status reports `deployment: dep_315508bbb7972ea373952228a14d456fec913be27bd54e4ee14ef4ff358b0955`.
   Both are `dep_`-prefixed ids derived from their entry payloads (specs/64 §5 rule 6); they differ
   because the measure and serving entries carry different payloads. (`60-recovered.json`.)

5. **A measure assignment runs every matrix cell, reports one evidence row per cell, stops the
   engine, and the gateway drafts a profile the next plan selects.** `phase: measured` with three
   evidence rows (one per matrix cell), `readySec: 17.63`:

   | context | decodeTps | prefillTps | ttftP50Ms |
   |---------|-----------|------------|-----------|
   | 122880  | 13.6 | 1256.2 | 93084.9  |
   | 176128  | 12.5 | 1066.2 | 157205.5 |
   | 229376  | 11.5 |  926.7 | 235554.9 |

   The gateway then produced a draft (`experimental: true`, the three evidence rows, full
   llama.cpp `launch` command: `--model … --mmproj … --n-gpu-layers 999 --split-mode layer
   --ctx-size 229376 --parallel 1 --flash-attn on --cache-type-k f16 --cache-type-v f16`), and the
   **next plan selected it**. (`10-measuring.json`, `20-serving.json` → `drafts[0]`.)

6. **A serve assignment launches the assigned runtime profile, probes it, and serves.** Engine
   container `iw-serve-r9700-27b-q8-vision-llamacpp-tp2-draft-dyn-6lbsqr3k023i-000001-nodebeast-241df803`
   (Up, **healthy**, `127.0.0.1:32903→8080`) — the "draft" in the name is the *drafted* profile.
   **Real inference through the gateway** (`POST /v1/chat/completions`, `max_tokens: 8`):
   `model: qwen3.8-27b-modality-vision-quant-q8_k_xl`,
   `choices[0].message.reasoning_content: "We need to respond exactly one word:"`,
   `usage.completion_tokens: 8`, `timings.predicted_per_second: 16.2` t/s (decode),
   `prompt_per_second: 90.4`. Model serving count = 1. (`20-serving.json`.)

7. **A failed placement is recorded; permanent reasons are not retried; transient reasons expire
   after 600 s; a serving engine that stops answering is released.** Provoked by `docker stop` of
   the serve engine:
   - Recorded failure `{reason: "engine_exited", message: "127.0.0.1:32903 stopped answering
     /health", profile: "…tp2-draft-dyn-6lbsqr3k023i-000001-nodebeast"}`; node status
     `phase: failed`, idle `failed_before`. (`30-failure.json`.)
   - The transient failure **expired after 600 s** and cleared (`failures: []`), and the 27B
     **re-served** (new assignment `dyn-…000003`, `endpoint 127.0.0.1:32904`, serving count 1,
     GPUs re-lit ~25 GiB). (`60-recovered.json`, `70-final.json`.)
   - **Permanent, non-retried:** with the node free, the 8-card Flash-Next was rejected with idle
     reason **`no_matching_profile`** (a 2-card host cannot host an 8-card profile).
     (`30-failure.json` → `nodes[0].idle`.)

## Milestone snapshots (`/iw/v1/dynamic`, admin-authenticated)

| file | moment |
|------|--------|
| `10-measuring.json` | 27B `measuring`, matrix 1/3 cells done, engine launched |
| `20-serving.json` | 27B `serving` (draft selected), `drafts[0]` present |
| `30-failure.json` | engine stopped → `engine_exited` failure; Flash-Next `no_matching_profile` |
| `40-retry.json` / `50-recovery.json` | transient failure held (600 s window) |
| `60-recovered.json` | failure expired + cleared; 27B re-served (assignment `…000003`) |
| `70-final.json` | final steady state: 27B serving, Flash-Next `no_matching_profile` |

The full `/iw/v1/dynamic` was also sampled every 30 s throughout the run on the host
(`/home/wohlgemuth/iw-dynproof/evidence/dyn-*.json`, ~200 samples, 18:39–20:20 UTC) and is retained
on `beast` for inspection; the milestone snapshots above are the canonical record committed here.

## Notes / follow-ups (non-blocking for the Rust reference proof)

- The **Go gateway** (`metabolomics-us/inferweave-gateway`) does not implement specs/64 (separate
  codebase; a dynamic node to it is recorded hardware-only and assigned nothing). Tracked as a
  separate follow-up — it is outside P5-T35's scope, which is the Rust reference
  (`InferWeave/inferweave`).
- The **Flash-Next 8-card deployment** could not be placed on this 2-card host (correct
  `no_matching_profile` behavior). Producing its own measured draft requires an 8-card R9700 host.
- A **separate adversarial review** of the implementation is a recommended follow-up (see P5-T35
  completion evidence).
