# Quantization tokens served by the reference lab gateway

Evidence for `specs/61_ALIAS_PRECISION_ADHOC_SELECTION_AND_RESOLUTION_TREES.md`.

**What was measured.** The model ids the reference lab gateway lists to an authenticated client,
and the `quant` qualifier of each, on **2026-10-15T06:16:21Z**.

**How.** `GET /v1/models` against the production container on the lab gateway host
(`inferweave-gateway:prod-current`, image `sha256:82cbffdfa03e4b76787972e05a4b81174a6a40abdc6955e004a1ad94...`
as reported by `docker inspect` on that host; image tags present then: `66384c4`, `940c451`,
`e6405ef`, `cde42f1`, `c654c7d`), with the gateway's client token, ids sorted. The `quant`
qualifier is the segment after `-quant-` of each id, copied, not inferred from other fields.

**Observed ids (9) and their quantization tokens (6 distinct).**

| model id | `quant` |
|---|---|
| `deepseek_v4-flash-modality-text-quant-mxfp4` | `mxfp4` |
| `laya-english-modality-text-quant-fp16` | `fp16` |
| `laya-multilingual-modality-text-quant-fp16` | `fp16` |
| `laya-typed-decisions-modality-text-quant-fp16` | `fp16` |
| `qwen3.8-27b-modality-text-quant-mxfp4` | `mxfp4` |
| `qwen3.8-27b-modality-vision-ctx-c120k-quant-q4_k_m` | `q4_k_m` |
| `qwen3.8-27b-modality-vision-quant-q8_k_xl` | `q8_k_xl` |
| `qwen3.8-flash_next-modality-text-quant-q4_k_xl` | `q4_k_xl` |
| `z-image-turbo-modality-image-quant-fp8_e4m3fn` | `fp8_e4m3fn` |

**Not claimed.** This shows which tokens this fleet advertised at one moment. It says nothing
about quality, nothing about other fleets, and it does not observe any token not listed above.
Tokens in spec 61's table that are absent here are classifications by the authors of that table.
