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

Hardware still to qualify before promotion: cancellation followed by near-capacity reuse, bounded gateway admission with authenticated mixed-size requests, and an explicit rollback drill. The model's native window is 262144 *total* tokens, including output and modality. A 260k prompt leaves little generation room; gateway sizing adds output and safety before admission.
