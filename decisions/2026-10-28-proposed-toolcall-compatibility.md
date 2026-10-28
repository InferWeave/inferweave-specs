# Proposed: native tool-call compatibility and qualification — 2026-10-28

**Status:** Proposed — needs owner acceptance. This record decides and authorizes nothing.  
**Decision owner:** InferWeave operator  
**Authorizes:** no protocol change, verifier authority, routing activation, runtime restart,
profile promotion or production deployment.  
**Relationship:** reconciles the operator-supplied `inferweave-toolcall-compat-v1` bundle with
specs 24, 54, 56, 63 and 64. The existing qualification-verifier proposal remains unaccepted.

## Input and observed incident

The input ZIP was transferred from the operator's Mac Downloads directory and checked on both
hosts with SHA-256 `2da08ee33b3943bc9717aff663baddea64a812e730481671701cba704a60cd04`.
The implementation checkout retains its unmodified `SPEC.md` and `START_PROMPT.md` under
`docs/specs/inferweave-toolcall-compat-v1-c13102d4a8/inferweave-toolcall-compat-v1/`.
The bundle explicitly calls its protocol fields proposed and requires canonical approval.

The implementation session on 2026-10-28 sent a synthetic `bash` function schema with
`tool_choice: auto` to the existing public gateway for
`deepseek_v4.1-flash-modality-text-quant-mxfp4`. Both nonstreaming and streaming requests
returned HTTP 200, visible DSML, no structured tool-call entries, and `finish_reason: stop`;
the stream included `[DONE]`. No generated command was executed. The local sanitized summary
was inspected for this proposal; its reproducible request and durable evidence belong in the
implementation evidence report before acceptance.

Read-only serving inspection in that session identified llama.cpp build `b10921-32bf0eb37`,
the `mx-llamacpp-cuda.sif` image name, an eight-A100 allocation and template SHA-256
`f8b442fab67e75b3aa468334b5cdda671003b852ffd71f23cb23377d31d9c7be`. An image name is not an
image digest. Served weight hashes and exact launch arguments still require evidence. The same
request directly against that runtime reproduced HTTP 200, visible DSML, zero tool entries and
`stop` in both modes; streaming terminated with `[DONE]`. Pi, with built-in tools disabled and
only a harmless mock `bash` handler, exited with visible DSML and no tool-execution event.
This localizes the failure to the runtime/model parsing boundary; it does not distinguish
degraded native generation from parser behavior. The installed image's help lists Jinja
(enabled by default), `reasoning-format deepseek` and chat-template/file options, with no
`tool-call-parser` option observed. That is flag evidence, not proof of a working configuration.

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
The proposed enforcement must be separately opt-in; changing that default globally would
break existing exact-model callers without providing qualified alternatives.

## Reconciliation required before implementation

**P2 privacy boundary.** The bundle's blanket byte-transparency wording cannot replace spec 63's
success-response allow-list, recorded in `OPEN_GATES.md` under the final 2026-10-16 update.
Preserve permitted tool-call IDs, indices, names, argument strings, finish reasons and separate
reasoning fields through that reduction. Preserve byte transparency on paths whose existing
contract requires it. Backend identity, unknown extensions and node error detail remain subject
to canonical redaction. A test must prove both tool fidelity and the privacy boundary.

**P3 qualification authority.** Passing a new suite does not itself authorize a catalog row to
become `verified`. Spec 56 requires a trusted verifier/evidence binding; its store, record and
authority are still proposed in
[`2026-10-16-proposed-qualification-verifier.md`](2026-10-16-proposed-qualification-verifier.md).
`OPEN_GATES.md` explicitly records this as unsatisfied. Do not introduce a parallel boolean
verification field or silently accept that older proposal through this feature.

**P4 replay boundary.** “Before client tool execution” is insufficient to make an inference
retry safe. Existing dispatch/idempotency contracts still govern ambiguous dispatch, partial
responses, cancellation and reconnects. A detected DSML string cannot establish that a request
is replayable, cannot become an executable call, and cannot be upgraded to a native success.

## Proposed owner decisions

1. **P1 profile schema and parser authority.** Approve additive optional metadata on the existing
   runtime profile, with exact engine/build/template identity and separate supported operations
   for nonstreaming, streaming, continuation, parallel calls and forced choice. Select the
   canonical spelling, schema version and unknown-field behavior before changing the wire.
   Native parser names/flags must come from the installed version and serving tests; no universal
   `deepseek_v41` parser name is assumed. Default absence preserves current launch behavior.
2. **P3 trusted qualification.** Decide whether to accept or amend the existing spec 56 verifier
   proposal, including who may attest tool fidelity, trusted record source/key purpose, immutable
   deployment and generation/epoch bindings, expiry, revocation and owner policy. Choose the
   required repeat/pass policy from measured results. A raw benchmark record or operator-declared
   parser name alone grants no verified capability. Unknown identity remains unqualified.
3. **P3 routing scope.** Approve a default-off enforcement flag scoped to explicitly selected
   deployments/requests, using existing feature eligibility and refusal semantics. Missing,
   stale, failed or mismatched tool evidence excludes a deployment only under that policy;
   tool-free traffic keeps its existing selection. Decide how empty tools and `tool_choice: none`
   affect the requirement, and freeze the capability-refusal vocabulary before implementation.
   Rollback disables the new policy without restarting engines or changing active reservations.
4. **P4 diagnostics and recovery.** Approve a bounded, content-free counter/reason vocabulary in
   canonical machine-readable contracts, plus retention and audience. Raw traces stay opt-in,
   locally restricted and subject to existing encryption/recording rules. Permit no automatic
   DSML conversion; any recovery uses the existing bounded no-replay rules and an independently
   qualified alternative. No new retry path is authorized by this proposal.

Acceptance should name which decisions are accepted; unspecified parts remain proposed. Accepted
design must then be reflected in relevant specs, contracts, schemas, task cards and coverage,
with executable hostile vectors. No new feature ID or accepted task is assigned by this draft.
Candidate ownership is the existing IW-DP-001/002, IW-REC-001/002, IW-BENCH-002 and runtime/alias
tasks; their final allocation is part of that canonical change.

## Work allowed by the current task and proof still owed

The operator's current request supports P0 read-only audit/reproduction, sanitized evidence,
P2 regression tests for existing behavior, and the isolated benchmark-argument evidence fix.
These do not require new protocol semantics. This draft supplies no additional authority.

Full P1–P4 delivery remains **owed**: approved profile schema and native parser validation;
qualified nonstream/stream/continuation through the real runtime, gateway and Pi; T01–T16 with
failure counts and mutation-sensitive protections; exact artifact identity and version-change
invalidation; trusted promotion and opt-in routing; canonical telemetry/recovery controls;
live Qwen regression, dynamic hot-swap and independent release evidence. Local fixtures prove
only the controls their executed tests exercise, never compatibility of an untested engine.

Retain active R9700 workloads, owner priority, availability floors, watchdogs, rollback artifacts
and scheduler authority. No engine replacement, hot swap, new GPU allocation, production
deployment or independent-review gate is approved here. Existing `OPEN_GATES.md` entries and
accepted contracts remain unchanged.
