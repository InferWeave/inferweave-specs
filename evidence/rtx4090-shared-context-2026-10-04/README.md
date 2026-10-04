# Bender/Fry shared-context qualification and activation — 2026-10-04

These files preserve the staged successes **and failures** that informed the bounded
Bender rollout decision. They contain request metrics and operational outcomes, not
prompt bodies or credentials. The final section records the later production
activation and programming-client checks separately from staged qualification.

## What the staged runs showed

- `stage-cache-overcommit.jsonl`: nine controlled red/blue/green image requests
  answered correctly, cancellation held admission closed, and a 257,468-token
  request completed after cancellation. The following concurrency case failed.
  Idle physical slots retained earlier KV; the revised proxy binds physical slots,
  clears retained KV when needed and disables cross-slot RAM restoration.
- `stage2-probe-contention.jsonl`: the revised profile repeated the nine correct
  image controls and cancellation/reuse, and completed two 117,468-token requests
  concurrently. Its next matrix case failed while Fry's real Go admission probes
  competed for the same shared capacity. A zero-backpressure guarantee is not
  claimed. Probe requests use the authoritative Rust ledger like user requests.
- `isolated-matrix.jsonl`: with staging workers withdrawn to isolate the hardware
  capacity test, two 117,468-token requests, three 77,468-token requests and a mixed
  117,468/77,468 pair completed. Observed peak busy slots were two, three and two.
  These are bounded capacity tests with two-token outputs, not long-output decode
  throughput benchmarks.
- `isolated-long-vision.jsonl`: 2048px blue-image requests answered blue correctly
  at all three classes, with actual prompt counts 77,536 / 117,536 / 257,536 and
  elapsed times 125.878 / 151.997 / 279.471 seconds. CPU vision projection remains
  a material latency limitation.
- `staging-gateway-check.json`: authenticated Fry staging requests returned text
  and the expected red/blue/green images across the three aliases; the legacy
  c64k spelling also worked. A temporary worker registered during an active 260k
  reservation remained enabled, with no suspension hold. Staging workers were
  withdrawn after testing. This record proves busy registration behavior; it is
  not a separately instrumented stale-offer race trace.
- `rollback-drill.json` preserves the earlier successful old-service recovery.
  `rollback-drill-stage2.json` preserves the later failed Fry SSH step: the engine
  restored, the activation quarantined without another automatic attempt, and a
  manual repetition recovered the authenticated old route. The bounded Fry-only
  retry correction then passed the exact-build drill in
  `rollback-drill-stage3.json`: automatic old-engine restoration, old registrar
  and worker route recovery, authenticated HTTP 200, and no quarantine.

Cancellation records sampled the barrier every 100 ms for 916 busy samples.
Sampling does not establish continuous observation between samples. The rollback
trigger was applied only after leases and physical slots were idle; preservation
of other active leases is covered by implementation tests, not this live drill.

## Candidate and rollback identity

`stage3-attestation.json` records the exact stage3 engine/proxy container IDs,
image IDs, argv and entrypoints captured in the protected watchdog configuration,
plus model/projector hashes, installed watchdog binary hash and source-file hashes.
The engine, proxy and watchdog hashes agree with the successful stage3 drill.
The launch includes a 262144-token unified pool, three sequences, Q4_0 K/V,
`--cache-ram 0`, a CPU vision projector and an 8192-token output limit.

The Bender and Fry rollback bundles remain protected on their respective hosts at
`/var/lib/inferweave/rollback/shared-context-20261004T032252Z`. The Bender image
archive SHA-256 is recorded in the attestation. Credentials and complete environment
snapshots remain only in the protected host bundle and are not published here.
Source files were uncommitted when captured; final source-review and commit linkage
must be recorded before production promotion. Host artifact capture is local evidence;
it does not replace the waived private GHCR/CI provenance check.

## Final probe-coexistence candidate

The final proxy image is
`sha256:0d955cc1e1bae569a9ffb4a6aa43bcc899a70df03a11bd31806b1770cdbf0d0e`;
`final-candidate-attestation.json` captures its exact stage4 identities and source hashes.
Plain-completion probes now reserve measured tokens, and chats wait at most five
seconds only behind those probes. Focused code/security reviews approved this change;
the implementation session reports 727 Rust tests, 34 focused proxy tests and strict
Clippy passing. Final spec review and commit linkage remain required.

`probe-coexistence-final.jsonl` passes a small probe alongside a 260k request and three
80k requests. `gateway-active-concurrency.jsonl` records two120/three80/mixed requests
routed through Fry, each HTTP 200 on its first attempt. These gateway requests use
55-token prompts and 128-token outputs; they test actual concurrent routing rather
than full contexts. `gateway-active-engine-overlap.log` records three physical slots
launching overlapping work.

`final-gateway-active-hardware.jsonl` supplies the complementary full-context test
through the Rust proxy while Fry staging workers remained registered: nine controlled
colors, a sampled cancellation barrier, 257,468-token reuse, two 117,468-token requests,
three 77,468-token requests and a mixed pair all pass. The final barrier had 914 busy
samples. This supersedes the earlier requirement to isolate the capacity matrix from
Go probes. `final-260k-long-vision.jsonl` also passed: a 2048px blue image was
recognized correctly in a 257,539-token request in 257.4 seconds.

## Stage4 failure and corrected stage5 rollback

`rollback-drill-stage4.json` records the intentional idle stop of the final proxy.
The watchdog restored the old engine, but three Fry companion attempts returned
immediate nonzero exits and the activation remained quarantined. Later manual
execution of the same command succeeded, restoring the registrar, old worker and
authenticated gateway HTTP 200. Manual recovery does not qualify automatic rollback.
The stage4 attestation remains historical identity evidence, not the final watchdog
identity. The correction spaces bounded Fry retries and records sanitized attempt
outcomes. It passed 25 watchdog tests, strict Clippy and focused review.

`rollback-drill-stage5.json` then passed on the final proxy image and corrected watchdog:
automatic restoration of the old 122880/2 engine, active Fry registrar, enabled worker
and authenticated gateway HTTP 200, with rolled_back=true and quarantined=false. The
Fry companion succeeded on the first attempt. `stage5-attestation.json` independently
records matching proxy/engine IDs and installed watchdog SHA-256
`762ee92bdec12516b5b7138e71a253d1fb6b8d26de656696b3332b8653dd8003`.
Final spec review and reviewed-commit linkage remain required; production activation
and fresh-client checks are not inferred from this successful staging drill.

## Final validation

An earlier full Rust run completed with 728/729 tests passing. The parallel run of
`node_proxy::tests::probe_completion_rejects_alias_auth_and_unsupported_payloads`
failed with a reqwest TCP connection reset; focused proxy and serial runs passed.
After the test-fixture correction, the exact command
`cargo test -p iw-cli --lib --quiet -- --test-threads=2` passed **729/729** in
107.80 seconds. Strict Clippy for lib/tests and formatting passed. This is a full
library test run with bounded parallelism, not a claim that the earlier unconstrained
parallel run passed. Final source-commit and rebuilt-image linkage remain owed.

## Rebuilt image requires fresh qualification

The test-only fixture edit rebuilt the proxy as
`sha256:e5187e64ac51a5406f5e375904d57035e8f234d19b0c3275adc7ef69bf8f54f1`.
Its executable digest also differs from the previously qualified image. Stage5 and
image `0d955cc…` remain historical evidence; the new image requires stage6 hardware
qualification and an exact-image automatic rollback drill. The 729-test source result
and spec review remain valid, but do not establish binary equivalence.

## Exact e518 hardware matrix and explicit answer check

`exact-e518-full-hardware.jsonl` records a complete matrix on rebuilt image
`e5187e64…` while Fry staging workers remained active. All nine small-image colors,
cancellation/reuse, two120/three80/mixed requests passed. Long-image requests also
completed at 260k/120k/80k with actual prompt counts 257542/117542/77542 and times
257.171/152.013/127.632 seconds, all HTTP 200.

The full-run harness omitted validation of the long-image answer. Its summary pass
therefore proves long-image transport/context usage, not long-image color correctness.
The benchmark harness has been corrected and its 18 tests pass. The separate
`exact-e518-color-260k.jsonl` then explicitly verified blue at 260k: 257542 prompt
tokens, 282.149 seconds, correct=true and HTTP 200. The exact e518 80k/120k long-image
records prove context/transport, not their answers; nine small-image controls passed
across all classes and the earlier artifact had color-checked long tests at each class. This benchmark-only correction does not change
the deployed node proxy source or image. The exact-image rollback drill remains owed.

`exact-e518-gateway-concurrency.jsonl` repeats routed two120/three80/mixed requests
through Fry staging on the rebuilt e518 image. Every request completed with HTTP 200,
128 output tokens and zero retries. These are short-prompt routing checks; the full
context capacity proof remains `exact-e518-full-hardware.jsonl`. The exact-image
rollback drill remains pending.

## Stage6 SSH sandbox failure

`rollback-drill-stage6.json` records another failed automatic rollback: the old
engine restored, but SSH exited 255 before remote sudo and the activation quarantined.
The failure was reproduced under an equivalent systemd sandbox. Inherited
`ControlMaster auto` tried to create a socket under `~/.ssh/controlmasters`, conflicting
with the watchdog's `ProtectHome=read-only` restriction. Explicit
`-o ControlMaster=no -o ControlPath=none` allowed a sandbox SSH smoke to exit zero;
manual companion execution then restored authenticated gateway HTTP 200.

This root-cause evidence supersedes a transient-SSH explanation for the observed
failure. The production gate remains blocked until the watchdog argv correction,
focused checks/review and a matching automatic rollback drill pass. Successful
manual recovery and the sandbox smoke alone do not qualify the rollback chain.

## Final stage7 automatic rollback passed

`rollback-drill-stage7.json` records the successful automatic rollback on exact proxy
image `e5187e64…` and patched watchdog SHA-256
`7d6b9e0cbea5b4a7a9b78a2a0cd4df6e131d5d835bc1b59911a681ccdeea5f34`.
After an intentional idle proxy stop, the old 122880/2 engine, Fry registrar and enabled
route restored automatically; authenticated gateway chat returned HTTP 200.
The watchdog recorded rolled_back=true and quarantined=false. Fry companion logged
exit_code=0/category=success on the first attempt with ControlMaster=no/ControlPath=none.
`stage7-attestation.json` was independently captured from the protected watchdog
configuration; engine/proxy IDs and installed watchdog hash match the drill.

This closes the earlier stage6 automatic-rollback blocker for these exact artifacts.
Historical sections above describe the qualification state at their stage; their
pending work is superseded by this final result where applicable. Stage6 failure and
root-cause evidence remain intact. Final reviewed-commit linkage is still owed, with
production readiness and client verification deferred until actual activation.

## Final source validation

The final source, including the SSH override, passed
`cargo test -p iw-cli --lib --quiet -- --test-threads=2`: **730 passed, 0 failed**,
110.01 seconds. The terminal summary was checked in `/tmp/iw-final-full-rust.log`.
Focused watchdog tests passed 26/26; deployment Python tests passed 73 and benchmark
tests 18. Strict Clippy for all targets, formatting, diff checks and systemd unit
verification passed. This supersedes the earlier 729-test snapshot; reviewed-commit
linkage remains pending.

## Reviewed implementation linkage

Implementation commit
[`a82ca88bc7b8235d5ce6c8ed876199321f927f21`](https://github.com/InferWeave/inferweave/commit/a82ca88bc7b8235d5ce6c8ed876199321f927f21)
contains the reviewed source and staged qualification records. The source-file hashes
recorded in `stage7-attestation.json` were compared directly with this commit and match.
This closes the final pre-activation linkage gate; historical pending statements above
refer to their stage. Promotion is approved after the reviewed PRs are merged.
Production readiness and client verification remain owed until activation is observed.


## Production activation and client observations

`production-activation.json` records the 2026-10-04T07:41:55Z observation after code
merge `5ffef477ff29c327e3248408d56c268227c5558e` and spec approval merge
`52e899752ead34c41371bc6ede53779a2301c121`. Activation `prod-20261004-0722`
retained the exact stage7 proxy image `e5187e64…`, engine image `797c320b…` and
watchdog binary `7d6b9e0c…`. Proxy health was HTTP 200, the timer active and fence
ready, with no rollback attempt or quarantine. Fry's production gateway and registrar
were active, the old worker retired, and the three aliases advertised per-request
contexts 260000/120000/80000 with idle offers 1/2/3. Authenticated production text,
red/blue/green controls and the legacy c64k image request passed.

`production-gateway-concurrency.jsonl` records two120, three80 and mixed requests:
every request returned HTTP 200 on the first attempt, using 55 prompt tokens and
128 output tokens. This tests production routing concurrency; staged full-context
records above establish the capacity envelope. `production-dynamic-slots.json`
records offers 0/1/1 during an active 120000-class request that finished with HTTP 200
and 512 output tokens. These alias offers are alternative views of one shared pool
and must not be added together.

Fry staging was restored with zero shared workers and active gateway/autodeploy timer.
Pi, Hermes and OpenCode each showed the three aliases and returned `OK` in a fresh
text request. Pi and OpenCode also returned `Red` for a fresh red-image request.
The initial Hermes one-shot CLI check covered text only. The later native image
attachment observations below cover fresh sessions at c80k, c120k and c260k.
Hermes' global `max_tokens` was lowered to 8192 and therefore also affects unrelated
models. OpenCode's stale provider key was synchronized. Private configuration backups
were retained; no keys, credential files or private backups are included here.

These observations close the prior activation and catalog-refresh deferrals where
stated. The later Hermes results below cover each client alias; no sustained production soak,
independent human audit or fleet-scale behavior is inferred. The operator's CI/private
GHCR waiver remains in force and is not a green CI or provenance result.

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

## Hermes native image attachment follow-up

`production-hermes-vision.json` records a fresh Hermes one-shot request at
2026-10-04T08:12:32Z using the c80k alias and `metabolomics` provider. The command
shape was `hermes chat -q <color-question> --image /tmp/iw-red-128.png -m <c80k-alias>
--provider metabolomics -Q --oneshot`. It exited 0 and answered `red` for the
128×128 solid-red PNG. The record contains no credentials or private configuration.

A stale explicit `auxiliary.vision` operator route forced text transcription through
the old model and supplied reasoning options. Removing that route and setting
`providers.metabolomics.models[<target-alias>].supports_vision=true` enables native
image delivery for the three aliases. The global `agent.reasoning_effort` was also
cleared because the custom provider otherwise sends unsupported `reasoning_effort`.
The existing default model preserves its prior `medium` setting through
`agent.reasoning_overrides`; global `max_tokens` remains 8192. Private configuration
backups were retained and active sessions were not interrupted.

This initial record exercised only the c80k fresh Hermes image path. The follow-up
records below close the c120k/c260k attachment gaps. Gateway exact-image vision
checks at every class remain separate evidence; this client check does not replace
full-context qualification or establish a sustained soak, fleet qualification or
a green CI result.

The Hermes correction and sanitized observation are linked to implementation commit
[`af4fac477c5d016c82d16f63e7c32214f1da00c1`](https://github.com/InferWeave/inferweave/commit/af4fac477c5d016c82d16f63e7c32214f1da00c1).
Separate review, 18 focused tests and Ruff passed, together with the live red-image
check above. This client correction does not change the promoted engine, proxy or
watchdog identities.

## Hermes image attachments at every class

`production-hermes-vision-all-contexts.json` consolidates the original c80k observation
with fresh native c120k and c260k one-shot sessions on 2026-10-04. The initial
checks used the same 128×128 solid-red PNG and `metabolomics` provider. Session
`20261004_092647_ad19e1`
selected c120k, exited 0 and answered `Red`; session `20261004_092737_46ca38`
selected c260k, exited 0 and answered `red`. Additional controls kept the question
identical and supplied no color in its text: c120k session
`20261004_093119_c93558` answered `blue` for a 128×128 solid-blue PNG, and c260k
session `20261004_093219_d9f239` answered `green` for a 128×128 solid-green PNG.
Both exited 0. Prompt text, image bytes, credentials and private configuration are
omitted. The original c80k-only record remains intact.

These short requests close the remaining per-class Hermes image-attachment gap.
They do not fill the advertised contexts. Backend/Fry vision and full-context
capacity measurements above remain separate qualification evidence.

## Health snapshot after 9.14 hours of uptime

`production-health-9h.json` records the 2026-10-04T16:29:33Z observation: candidate
engine and proxy both running after 9.14 hours of uptime, zero restarts and no OOM;
engine healthy, proxy HTTP 200; active watchdog timer, ready fence, no rollback
attempt and no quarantine. Fry's gateway and registrar timer were active with
exactly three unsuspended production aliases and no legacy worker. A bounded
watchdog error-journal query returned no entries; its literal host-time query is
preserved in the record.

This snapshot does not measure continuous endpoint availability or workload intensity
throughout the interval. No predefined sustained or 24-hour soak criterion was
exercised. It does not change the CI waiver, independent-review staffing gap, fleet
qualification or any unrelated blocked gate.
