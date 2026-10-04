# Bender RTX 4090 shared-context rollout — 2026-10-04

**Status:** Accepted and activated on the existing Bender/Fry service. Production routing, dynamic offers and concurrent requests passed; Pi, Hermes and OpenCode fresh text checks passed, and Pi/OpenCode image checks passed. Hermes image attachment verification remains owed.
**Decision owner:** InferWeave operator  
**Date:** 2026-10-04 UTC  
**Requested scope:** The operator directed: “ok do all of these please, than PR, merge and redeploy whats needed for this to work system wide.” This covers qualification and, after the release gates, replacing the existing Bender Qwen3.8-27B vision service behind Fry.  
**Relationship:** Extends the existing-service exception in `decisions/2026-09-22-existing-gateway-rollout.md` to one already serving GPU. It does not approve a new site, general fleet deployment, GPU reset, host reboot, or cross-site capacity routing.

## Measured basis

The prior exploratory run and its limitations are recorded in
[`evidence/rtx4090-shared-context-2026-10-03/`](../evidence/rtx4090-shared-context-2026-10-03/).
It demonstrated useful capacity and an image response, then restored the old service.
Those historical measurements are not reproduced by this decision and are not release
qualification. The later staged records below provide exact runtime attestation,
cancellation recovery, controlled image-content tests, authenticated Fry routing and
automatic rollback evidence.

The operator subsequently answered “ignore CI, its broken here” when told that the
private GHCR pin check could not be read using the available token and Woodpecker
required sign-in. This waives the CI/pin-check release gate for this bounded rollout;
it is not a successful CI result or proof of registry artifact provenance. Fresh local
validation, recorded exact image identities and separate agent review remain required.

## Options

1. Retain the current two fixed 122,880-token vision slots.
2. Add shared-pool arithmetic to the legacy Go gateway.
3. Put one weighted, authoritative Rust admission facade in front of a qualified unified llama.cpp engine. The Go gateway receives only per-alias current virtual slot availability.

## Decision

Choose option 3 for this existing Bender GPU only. The public 260k, 120k and 80k aliases are alternative views of one 262,144-token KV pool and at most three active sequences. Every request must pass Rust tokenization, bounded output and modality accounting, atomic admission and cancellation cleanup before reaching the engine. Idle session hints last at most ten minutes and are reclaimable on demand; they confer no cache ownership. A 260k class refers to total context, including output and safety margin.

The model-serving engine and Rust ingress remain Docker Compose services. A narrowly scoped **Rust host watchdog** is approved as the Bender Docker lifecycle adapter because the Docker socket must not be given to arbitrary inference traffic. This is an explicit host-management exception to the persistent-role deployment rule, limited to inspecting and recovering the two named candidate containers and the retained old profile. It may drain, fence, perform one bounded rollback and quarantine. It may not reset the GPU, reboot the host, touch unrelated containers, or change Slurm allocations. The exact implementation passed separate source/spec review and the hardware rollback drill before production activation, as recorded below.

For this same bounded release, D-001 permits the existing Fry registration adapter and
a one-shot Python rollback companion to restore only the saved Bender registrar,
worker and routing state. The companion runs only through the pinned watchdog rollback
command, with protected inputs, bounded timeouts and a checked authenticated smoke
response. Python is not authorized for inference, admission, capacity accounting or
new persistent services. Offline qualification and one-shot configuration preparation
remain tooling. These exceptions do not change the default language or container rules
for future deployments.

## Release conditions

1. Separate implementation and spec agent review plus local validation of the exact candidate pass. This procedural review does not satisfy the broader unstaffed independent-review gate. The operator explicitly waived the private GHCR/CI pin check for this rollout as broken in this environment. Record that waiver; do not report CI or the pin check as green. Candidate and rollback image identities must still be captured and verified locally.
2. The exact candidate engine/proxy image IDs, launch arguments, model and projector hashes and resource envelope are captured at runtime. The prior Compose configuration, image artifact and Fry worker/registrar/routing state remain restorable.
3. A real backend cancellation followed by near-full reuse succeeds; red/blue/green image controls answer according to image content at every class; concurrent and long-vision matrix cases complete without OOM or context truncation.
4. Fry staging registers three aliases through its own credentials and direct tunnel, passes the real Go admission probes, authenticated requests across all classes and busy-registration checks, then withdraws its test workers. Stale-offer race behavior requires local regression tests. The final live capacity matrix must also pass while staging workers and their probes remain registered. Busy aliases remain registered rather than being falsely suspended.
5. A bounded watchdog drill closes admission before recovery, preserves active work while drain is possible (covered by local regression tests), restores the old two-slot engine and authenticated Fry route on failure, and quarantines after an unsuccessful rollback or repeated fault.
6. After production registration, Pi, Hermes and OpenCode model configurations are refreshed from the gateway's **per-request** context fields with an 8,192-token output ceiling and image support. New programming sessions prove text and image behavior without disrupting active sessions.

## Consequences and rollback

Higher concurrency is available at shorter contexts, while a near-260k request can consume the whole pool. The staged CPU-projector long-image requests took approximately 126, 152 and 279 seconds at the 80k, 120k and 260k classes. This latency is disclosed for the bounded programming pilot; no interactive image-latency guarantee is made. A stale slot offer may receive a retryable node-side capacity response; the gateway never gets a second KV ledger.

Stop candidate registrations and route offers before rollback. Fence the proxy, drain or bound active work, stop only the candidate containers, restore the retained old engine and Fry registrar/worker state, and require an authenticated routed smoke response. Failure leaves the candidate quarantined with no new offers. Revisit the decision on OOM, device reset, correctness failure, profile drift, repeated restarts, stuck cancellation, rising context-capacity errors, or an unacceptable long-image latency distribution.

## Qualification record

The reproduced request and drill records, including failed stages, are preserved in
[`evidence/rtx4090-shared-context-2026-10-04/`](../evidence/rtx4090-shared-context-2026-10-04/).
Its README states the limits of each observation. Runtime qualification does not imply
fleet qualification or a sustained production soak.

| Release condition | Status | Record and limits |
| --- | --- | --- |
| Latest-candidate local validation | proven | After the test-fixture correction, `cargo test -p iw-cli --lib --quiet -- --test-threads=2` passed 730/730 in 110.01s on the final source. Strict Clippy for all targets, formatting, diff checks and systemd verification passed. Final watchdog 26, deployment 73 and benchmark 18 checks also passed |
| Separate implementation/spec review | proven | Focused code and security reviews approved the revised proxy; final spec review approved with no blockers. Procedural agent review does not staff the independent-review gate |
| Reviewed-commit linkage | proven | Implementation commit [`a82ca88bc7b8235d5ce6c8ed876199321f927f21`](https://github.com/InferWeave/inferweave/commit/a82ca88bc7b8235d5ce6c8ed876199321f927f21); recorded runtime source hashes match this commit, with exact image/watchdog identities in `stage7-attestation.json` |
| Rebuilt candidate hardware matrix | proven | Image `sha256:e5187e64ac51a5406f5e375904d57035e8f234d19b0c3275adc7ef69bf8f54f1` passed the complete matrix with staging workers active in `exact-e518-full-hardware.jsonl`; matching final attestation and successful automatic rollback are recorded for stage7 |
| Retained rollback artifacts | proven | `stage3-attestation.json`, model/projector hashes, protected Bender/Fry bundles and image archive hash |
| Final cancellation/reuse and vision/concurrency matrix | proven | `exact-e518-full-hardware.jsonl`: nine checked colors, sampled cancellation barrier, 257468-token reuse, two120/three80/mixed all pass while staging workers remain registered |
| Rebuilt-image long-vision transport/context | proven | Exact e518 image completed long-image requests at 260k/120k/80k with 257542/117542/77542 prompt tokens in 257.171/152.013/127.632 seconds, all HTTP 200 |
| Rebuilt-image long-vision answer correctness | proven | `exact-e518-color-260k.jsonl` explicitly checks blue at 260k: 257542 prompt tokens, 282.149 seconds, correct=true, HTTP 200. Exact-image 80k/120k long requests prove context/transport only; nine small-image color controls cover every class, and earlier artifact long-color tests cover all three |
| Fry staging routing and probe coexistence | proven | Original routed text/vision/legacy and busy-registration checks plus probe coexistence. `exact-e518-gateway-concurrency.jsonl` repeats two120/three80/mixed through Fry on the rebuilt image: every request HTTP 200 without retry, 128 output tokens each. Earlier engine log records physical overlap |
| Earlier watchdog rollback/quarantine | proven | Stage2 failed recovery quarantined; stage3 automatic rollback restored old 122880/2 engine, registrar and authenticated Fry HTTP 200; live drill began idle |
| Rebuilt-image rollback | proven | `rollback-drill-stage7.json`: patched watchdog disabled inherited SSH multiplexing, restored old 122880/2 engine and active Fry registrar/route, and verified authenticated HTTP 200; rolled_back=true, quarantined=false. Stage6 failure/root cause retained |
| Production activation and routed capacity | proven | `production-activation.json`, `production-dynamic-slots.json` and `production-gateway-concurrency.jsonl`: exact promoted artifacts healthy, three aliases registered, routed text/colors/legacy requests passed, two120/three80/mixed returned HTTP 200 without retry, and an active 120k request showed 0/1/1 available offers |
| Programming-client catalog refresh and fresh text | proven | `production-activation.json`: Pi, Hermes and OpenCode each expose three aliases and fresh text returned `OK`; output limits are 8192 |
| Pi/OpenCode fresh image requests | proven | `production-activation.json`: each answered `Red` for a red image |
| Hermes image attachment request | owed | The one-shot CLI verification exercised text only; gateway vision and the other clients do not establish Hermes attachment behavior |
| CI/private GHCR pin check | waived | Operator's explicit CI waiver above; no green result or registry provenance proof claimed |

The final stage7 drill used proxy image
`sha256:e5187e64ac51a5406f5e375904d57035e8f234d19b0c3275adc7ef69bf8f54f1`,
engine image `sha256:797c320bf6a87c72ce165fa7e28863cc374e586dab4fc3bbfd10b3d8e2ebb3cd`,
and patched watchdog binary SHA-256
`7d6b9e0cbea5b4a7a9b78a2a0cd4df6e131d5d835bc1b59911a681ccdeea5f34`.
`stage7-attestation.json` records matching profiles and source hashes. Earlier
attestations remain historical evidence, not the promoted identities.

Go plain-completion probes reserve their measured token envelope; chats can wait
up to five seconds only behind such probes. This removes the earlier full-alias probe
reservation contention. The final direct matrix passed with staging workers registered,
and gateway-routed short-prompt concurrency passed without retries. The watchdog
spaces bounded Fry retries, records sanitized attempt outcomes and explicitly sets
`ControlMaster=no` and `ControlPath=none` so the read-only-home sandbox cannot inherit
a writable multiplexing-socket requirement. The stage7 Fry companion succeeded on
the first attempt. Exhausted attempts still quarantine; the stage6 failure and its
root cause remain preserved rather than replaced by the later successful result.

## Production activation observed

After implementation merge
[`5ffef477ff29c327e3248408d56c268227c5558e`](https://github.com/InferWeave/inferweave/commit/5ffef477ff29c327e3248408d56c268227c5558e)
and approval merge
[`52e899752ead34c41371bc6ede53779a2301c121`](https://github.com/InferWeave/inferweave-specs/commit/52e899752ead34c41371bc6ede53779a2301c121),
activation `prod-20261004-0722` promoted the exact stage7 proxy, engine and watchdog
identities above. At 2026-10-04T07:41:55Z, the proxy returned HTTP 200, the watchdog
timer was active with a ready fence, and no rollback or quarantine had occurred.
The production Fry gateway and registrar timer were active; the old worker was retired.

The three production aliases advertise total-context classes 260000/120000/80000 and
idle offers 1/2/3. They share one pool: while a 120000-class request was active,
observed remaining offers were 0/1/1, and that request completed with HTTP 200 and
512 output tokens. Routed text passed all three classes; controlled red/blue/green
requests and the legacy c64k alias passed. Production two120/three80/mixed requests
all completed without retry. These routed concurrency checks used 55-token prompts
and 128-token outputs; the staged full-context matrix remains the separate capacity
proof. Fry staging was restored with zero shared test workers and active gateway and
autodeploy timer.

Pi, Hermes and OpenCode consumed the production catalog and each passed a fresh text
request. Pi and OpenCode also passed fresh red-image requests. Hermes image attachment
was not tested through its one-shot CLI and remains owed under condition 6. The local
Hermes global `max_tokens` was lowered to 8192, which also affects unrelated models;
the OpenCode provider's stale key was synchronized. Private configuration backups were
retained. The evidence README records these client limits. This bounded activation
observation does not establish sustained production reliability or fleet qualification.

The production client compatibility correction and sanitized observations are linked
to implementation commit
[`c41841f8b94592e3cded4d11b4bd07e1db59a6ac`](https://github.com/InferWeave/inferweave/commit/c41841f8b94592e3cded4d11b4bd07e1db59a6ac).
Its separate review approved the change; 13 focused tests and Ruff passed. The client
follow-up [PR #697](https://github.com/InferWeave/inferweave/pull/697) merged as
[`810632ab5006998a30bf4f8aa10fec4999a25247`](https://github.com/InferWeave/inferweave/commit/810632ab5006998a30bf4f8aa10fec4999a25247). It did not change the
promoted engine/proxy/watchdog identities. Both `pi-stack-pi-web` and
`pi-stack-pi-web-sessiond` listed all three aliases with 80k/120k/260k context,
8192 output tokens and image support. This proves model visibility in those
containers, not a separate browser/sessiond inference request; active sessions were
left intact.

## Requirements affected

- `IW-CAP-001`, `IW-CAP-002`, `IW-CAP-003`: shared capacity, hard context ceiling and reservation liveness (`P1-T11`, `P1-T11A`, `P1-T11B`).
- `IW-ROUTE-004`: context aliases for one deployment (`P1-T13A`).
- `IW-WATCH-001`, `IW-WATCH-002`: incident detection and bounded rollback (`P1-T20A`, `P1-T20B`).
- `IW-DEPLOY-001`: narrow host-management exception (`P0-T11A`, `P1-T23`).
- D-001 and D-018, with the bounded exceptions above; invariants 3–4, 21–23, 28, 32–37 and 42.

No task proof status, feature ownership or general deployment ordering changes in this
scoped decision. Unexercised fleet controls retain their existing `owed` status.
