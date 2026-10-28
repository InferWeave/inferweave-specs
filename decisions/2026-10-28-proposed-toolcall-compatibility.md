# Native tool-call compatibility and bounded qualification — 2026-10-28

**Status:** Accepted for implementation and bounded isolated qualification only.
**Decision owner:** InferWeave operator
**Authorization record:** the operator's “ok work on all of these here” follow-up accepted the
scoped implementation work. On 2026-10-28 the operator then explicitly approved, in the same
thread: (1) submitting the CPU-only native candidate image build on Hive, (2) obtaining the
capacity a separate isolated canary needs, (3) running the canary's runtime, gateway and Pi
qualification including the Qwen regression, and (4) every open decision in this record and
its canonical proposal PR. This does not authorize production activation or promotion, replacing
or cancelling the running production allocation or its profile, interrupting active R9700
workloads, taking capacity from protected benchmark or owner-floor allocations, or acceptance of
the general verifier proposal. A canary is a new, separately owned allocation that the existing
executor can retire, with the prior profile/image preserved for rollback.
**Relationship:** amends specs 03, 24, 56 and 64 through the closed camelCase contract
`contracts/tool-call-compatibility.json`. Existing invariants and all unrelated open gates apply.

## Input and observed incident

The input ZIP was transferred from the operator's Mac Downloads directory and checked on both
hosts with SHA-256 `2da08ee33b3943bc9717aff663baddea64a812e730481671701cba704a60cd04`.
The implementation checkout retains its unmodified `SPEC.md` and `START_PROMPT.md` under
`docs/specs/inferweave-toolcall-compat-v1-c13102d4a8/inferweave-toolcall-compat-v1/`.
The bundle originally called its fields proposed; the bounded implementation acceptance above
supersedes that status only for the contract and scope recorded here.

The implementation session on 2026-10-28 sent a synthetic `bash` function schema with
`tool_choice: auto` to the existing public gateway for
`deepseek_v4.1-flash-modality-text-quant-mxfp4`. Both nonstreaming and streaming requests
returned HTTP 200, visible DSML, no structured tool-call entries, and `finish_reason: stop`;
the stream included `[DONE]`. No generated command was executed. The local sanitized summary
was inspected for this decision; the implementation evidence report retains the request and
sanitary structural observations without exposing prompts, arguments or credentials.

Read-only serving inspection in that session identified llama.cpp build `b10921-32bf0eb37`,
the `mx-llamacpp-cuda.sif` image name, an eight-A100 allocation and template SHA-256
`f8b442fab67e75b3aa468334b5cdda671003b852ffd71f23cb23377d31d9c7be`. An image name is not an
image digest. Served weight hashes and exact launch arguments still require evidence. The same
request directly against that runtime reproduced HTTP 200, visible DSML, zero tool entries and
`stop` in both modes; streaming terminated with `[DONE]`. Pi, with built-in tools disabled and
only a harmless mock `bash` handler, exited with visible DSML and no tool-execution event.
This localizes the failure to the runtime/model parsing boundary. The native dialect
evidence correction below replaces the earlier malformed-generation hypothesis. The installed image's help lists Jinja
(enabled by default), `reasoning-format deepseek` and chat-template/file options, with no
`tool-call-parser` option observed. That is flag evidence, not proof of a working configuration.

## Native dialect evidence correction

The initial “malformed wrapper” interpretation is withdrawn. DeepSeek's
[official encoder at revision 314113f8a7dadb388215396ba5fbee2c610a04d6](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/314113f8a7dadb388215396ba5fbee2c610a04d6/encoding/encoding.py#L428)
defines the spaced V4.1 tags. Spacing is not evidence of quantization damage.
The canonical parser source at reported build pin
[32bf0eb37cfecbc7d74b1dd2594ce285bed2f55f](https://github.com/ggml-org/llama.cpp/blob/32bf0eb37cfecbc7d74b1dd2594ce285bed2f55f/common/chat.cpp#L2188)
recognizes older unspaced wrappers. Official native V4.1 support was added in
[74bca3950054eed1795f525cb9cf06bfe796492d / PR #31086](https://github.com/ggml-org/llama.cpp/commit/74bca3950054eed1795f525cb9cf06bfe796492d),
including template detection, spaced DSML parsing, reasoning and continuation
handling. The measured effective template also contains an unspaced call-wrapper
fragment and no spaced counterpart. This explains a concrete runtime/template
dialect mismatch rather than a gateway schema-loss failure.

A candidate must align native handling and the V4.1 template. Updating a binary
while retaining an old embedded template may still select the older dialect.
The private serving image may contain downstream modifications despite its build
string; exact loaded-image/source and served-weight binding remain owed. A
read-only CPU step observed actual redacted argv for the exact model/port,
including --jinja, and hashed the current staged SIF file, but those observations
are not cryptographic running-deployment attestation. No serving change was made.
At upstream 74bca395, eight CPU-only parser fixtures passed. Disabling only V4.1
recognition made the third fixture fail with spaced tags left in content;
restoring the source restored all eight passes. A fresh leader rerun passed.
The upstream minimal template warns that it does not natively describe tools:
this is parser/incremental proof only. It cannot close native model, production
template, hardware, Pi, deployment or promotion gates.

## Existing implementation to reuse

Source inspection is pinned to `InferWeave/inferweave@1e03d13df57ffa14c25847198397ab7aeb719ecf`.
The entries below describe code, not qualified production capability.

| Existing surface | Reuse and boundary |
| --- | --- |
| `iw-core/src/runtime_profile.rs::RuntimeProfile` and `reproduction.rs::Candidate` | Extend the existing profile and engine launch identity if approved; do not create another runtime registry. |
| `iw-core/src/runtime_implementation.rs` | Reuse runtime, image, backend, model/tokenizer and capability identity; `supports_tools` is a declaration, not fidelity evidence. |
| `iw-core/src/runtime_evidence.rs` and `requalification.rs` | Reuse exact cohorts, the benchmark warehouse and invalidation on model/runtime/settings changes. Tool-suite results need their own approved evidence meaning. |
| `iw-core/src/alias_resolution.rs` | Reuse feature confidence, fidelity, freshness and instance-generation checks; do not create another scheduler or bypass owner admission. |
| `iw-core/src/dynamic_node.rs::draft_profile` | Throughput drafts retain launch configuration but do not prove tool fidelity. A successful throughput measurement cannot mint verified tool support. |
| `iw-bench/src/suite/agent.rs` | Reuse the bounded tool loop, argument validation and harmless supplied handlers for continuation tests. |
| `iw-runtime-bench/src/runtime.rs::RuntimeConfig::runtime_args` | Fix the independently reproduced loss of equally sized extra arguments in this evidence-map helper. No production caller was found; RuntimeConfig already serializes its argv vector, so persisted-record corruption is not claimed. |

`iw-gateway/src/joined.rs` intentionally reads `NodeModelAdvert.tools == None` as permissive
legacy support. Its source records a prior outage caused by treating absence as a refusal.
The accepted enforcement must be separately opt-in; changing that default globally would
break existing exact-model callers without providing qualified alternatives.

## Canonical boundaries

**P2 privacy boundary.** The bundle's blanket byte-transparency wording cannot replace spec 63's
success-response allow-list, recorded in `OPEN_GATES.md` under the final 2026-10-16 update.
Preserve permitted tool-call IDs, indices, names, argument strings, finish reasons and separate
reasoning fields through that reduction. Preserve byte transparency on paths whose existing
contract requires it. Backend identity, unknown extensions and node error detail remain subject
to canonical redaction. A test must prove both tool fidelity and the privacy boundary.

**P3 qualification authority.** A purpose-specific signed tool record may constrain an exact-model
route under the private owner-installed policy. It does not promote a catalog row or alias
confidence. The general verifier in
[`2026-10-16-proposed-qualification-verifier.md`](2026-10-16-proposed-qualification-verifier.md)
remains proposed. Runtime observations provide current generation/epoch/instance/deployment/GPU
and runtime-implementation bindings, but contain no actual runtime build/version or artifact
hash attestation. The owner's expected build/image/model/template identity is explicit trust
input and must not be described as independently measured by those observations.

**P4 replay boundary.** “Before client tool execution” is insufficient to make an inference
retry safe. Existing dispatch/idempotency contracts still govern ambiguous dispatch, partial
responses, cancellation and reconnects. A detected DSML string cannot establish that a request
is replayable, cannot become an executable call, and cannot be upgraded to a native success.

## Accepted implementation contract

The frozen fields, bounds, enum spellings, signature transcript and task ownership live in
`contracts/tool-call-compatibility.json` and `schemas/v1/runtime/tool-*.json`.

1. Optional profile `toolCalling` is a declaration. Absence preserves legacy serialized identity
   and launch behavior. Active declarations support only the tested native llama.cpp revision or
   exact backport pairing, CPU/CUDA, an explicit read-only template with checked SHA-256 and known
   native arguments. Unsupported combinations fail validation; no guessed vLLM flags are passed.
   Typed dynamic assignments require negotiated `iw.tool-config/1` in addition to the existing
   dynamic capability. Throughput drafts clone declarations, never qualifications.
2. Reports reuse the benchmark Store and exact evidence cohort. Each actual-model repetition must
   pass T02/T05/T06 through direct runtime and gateway, and T05 through the agent. A failed case,
   missing identity, synthetic transport evidence or missing repetition cannot qualify. Parallel
   additionally needs T04 on both runtime/gateway paths. Suite v1 cannot qualify `forcedChoice`.
   Signed records use the purpose-specific binary transcript, trusted owner keys, exact binding,
   policy revision, expiry and revocation. The report hash covers semantic fields, not raw JSON.
3. Private snapshots default to `off`; `shadow` observes and `on` enforces only allowlisted models
   carrying nonempty tools. Nonempty tools require nonstreaming, streaming and continuation even
   with `tool_choice: none`. Required/named choice additionally requires forced choice, and an
   explicit `parallel_tool_calls: true` requires parallel support. Empty/absent tools preserve
   existing behavior. Strictly newer same-owner snapshots replace atomically; failed reload
   preserves the old policy. Registration incarnation additionally invalidates evidence but
   never substitutes for the engine generation/source epoch. Active leases remain untouched.
4. Existing authenticated operator explain/reload routes carry context and atomic snapshot reload;
   no new URL or public projection is introduced. Content-free bounded counters use the closed
   vocabulary. Preserve spec63 redaction, cancellation and all no-replay rules. No new retry,
   DSML conversion or execution authority is introduced.

Minimum three repetitions and a maximum one-hour record lifetime are **unmeasured policy
choices**, not measured reliability or hardware bounds. The owner may configure stricter policy;
actual live qualification and expiry/revocation behavior still require executable evidence.

## Native candidate and remaining proof

The native upstream revision is `74bca3950054eed1795f525cb9cf06bfe796492d`. The bounded older-base
alternative is `32bf0eb37cfecbc7d74b1dd2594ce285bed2f55f` with parser patch SHA-256
`03e81a8aa0b8834e6951f4e46bb30324521343d6581ede5dd0a78da1a94d6696`.
The full V4.1 template candidate has SHA-256
`c9046238d418153ed16c1ece7041873556d4c5ae27918a2cc20106d12b0a23f8`; it adapts the provider
Jinja expression using undefined `**` syntax for the pinned native interpreter. The
implementation session reports eight V4.1 and 57 Qwen CPU parser fixtures passing with the native
backport. Those results are parser/template evidence, not actual-model or GPU qualification.

P0/P2 transport and mock-handler regressions and the isolated argument-evidence helper repair
remain within scope. Full P1–P4 acceptance is **owed** until current implementation checks,
mutation-sensitive controls, exact artifacts and the complete T01–T16 matrix are evidenced.
Actual DeepSeek and Qwen generation, Pi mock dispatch and continuation, GPU serving, dynamic
hot swap, post-change floor/rollback behavior and independent release proof remain **owed**.
No eligible existing spare with availability-floor proof has been established. Do not create a
new GPU allocation or disturb R9700 workloads to fill this evidence gap.

No production deployment, route activation, profile promotion or general verifier acceptance
is granted. Preserve owner priority, availability floors, watchdogs, rollback artifacts and
scheduler authority. The bounded `OPEN_GATES.md` entry records implementation authority separately
from those unsatisfied operational controls; unrelated entries retain their prior meaning.
