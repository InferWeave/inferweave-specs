# Bender 4090 shared-KV qualification (2026-10-03)

The InferWeave implementation candidate (`deploy/engine/rtx4090-qwen3.8-27b-unified-candidate.yml` in the implementation repository) ran temporarily on the local RTX 4090 with Qwen3.8-27B Q4_K_M, Q4_0 K/V, `--ctx-size 262144`, `--parallel 3`, `--kv-unified`, MTP off, and the F16 vision projector on CPU. `--image-max-tokens 4096` and `--fit-target 768` were pinned. The direct test bound host port 8081; the staged Compose file binds 8082 so the Rust admission proxy can own 8081. `/props` and `/slots` reported three 262144-token sequence ceilings over the single pool. The startup and final logs contain no CPU *model-layer* warning and no OOM. A 500 ms `nvidia-smi` sample stream recorded 22,343 MiB peak GPU memory use during the requests.

The direct-engine probe generated unique cold synthetic prompts, calibrated with the backend's `/apply-template` and `/tokenize` endpoints, then checked actual backend usage and nonempty output for every request. It did not send prompts through the Rust node admission facade or the Go gateway. All scenarios returned HTTP 200 and completed without truncation.

| Scenario | Actual prompt tokens per request | Wall time | Outcome |
| --- | --- | ---: | --- |
| One near-max | 259,974 | 190.1 s | 1/1 complete |
| Two medium | 119,974 + 119,974 | 172.6 s | 2/2 complete |
| Three small | 79,974 × 3 | 174.9 s | 3/3 complete |
| Mixed | 119,976 + 79,976 + 49,976 | 185.9 s | 3/3 complete |
| Long vision, 2048px red square | 249,020 including image | 274.3 s | 1/1 complete; answer Red |

The long-vision backend timing was 267.2 s prefill and 2.2 s for 59 generated tokens. Its last image chunk added about 97 s at the CPU projector; a small-image smoke request completed much faster. This is a latency limitation, not a context-capacity failure.

Evidence: `requests.jsonl` (outcomes and usage, no prompt bodies), `engine.log` (backend timings/placement), `gpu-samples.csv` (memory/utilization), `props.json`, `slots-at-start.json`, and `startup.log`. The production two-slot 120k vision container and gateway registration were restored and checked after the test.

## Rust facade run and provenance limits

The later facade run is recorded in `node-proxy-hardware.jsonl`. A 257,947-token prompt returned HTTP 200 in 186.61 seconds with 22,339 MiB peak sampled GPU memory. While a 117,448-token 120k request was active, the 260k/120k/80k aliases offered 0/1/1 slots and another request completed through 80k. A 128px red image returned `Red` through each alias. The original 122,880-token, two-slot engine was restored; its registrar succeeded and an authenticated gateway chat returned HTTP 200. That is a restoration smoke check, not a full production rollback drill.

`compose-candidate.yml` preserves the candidate launch flags. After the run, local image inspection reported engine image ID `sha256:797c320bf6a87c72ce165fa7e28863cc374e586dab4fc3bbfd10b3d8e2ebb3cd` and Rust proxy image ID `sha256:9d7d29bf1cb73679c3b785569229d0adf1855e5984f1e92189d56148af0637c7`. The tested proxy source files match the present implementation by SHA-256: `node_proxy.rs` = `9913747bda9ff178aa50a5970d41983bb67b0d4e0f6a3ee9377bbc9f2bf79abe`, `shared_context.rs` = `6e1189adf817c06ff0e85076174b6554aa9009a88c5d6aa152f63b4aae0ea201`. These identifiers were checked **after** the run, not captured as a run-time image digest or engine argv attestation. Exact runtime-flag qualification remains owed.

The model's native window is 262144 *total* tokens, including output and modality. A 260k prompt leaves little generation room; Rust node sizing adds output and safety before admission. Real-backend cancellation followed by near-capacity reuse, authenticated mixed-class Fry staging traffic and the complete rollback drill remain owed before activation.
