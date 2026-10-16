# Adversarial review — dynamic nodes (spec 64), Rust reference implementation

- **Date:** 2026-10-16
- **Reviewer:** autonomous review, separate from the authoring (PR #918) and from the
  hardware proof (`REPORT.md`, same directory)
- **Target:** `InferWeave/inferweave @ origin/main (5199f8c0)` — the merged
  `iw.dynamic-node/1` implementation

## Scope and method

Adversarial read of the Rust reference implementation of spec 64, with the intent of
finding (a) correctness bugs, (b) security issues (path traversal, command injection,
mount escape, supply-chain, secret leak, DoS), (c) spec-conformance gaps, (d) robustness
defects (overflow, non-determinism, non-idempotency, failure-mode holes), and (e) test
gaps.

Files reviewed (merged `origin/main`):

| File | Lines | Focus |
|---|---|---|
| `crates/iw-gateway/src/server_dynamic.rs` | 133 | control-surface entries + operator view |
| `crates/iw-gateway/src/dynamic_provisioner.rs` | 1209 | store, lock discipline, draft writes, snapshot |
| `crates/iw-core/src/dynamic_node.rs` | 5526 | pure `plan`/`reconcile`/`eligible`/`place`/`measure`, `settle_measurement`, `deployment_id`, `ArtifactSpec`/`validate_artifact_set`, failure/refusal accounting |
| `crates/iw-cli/src/dynamic_node.rs` | 7772 | node runtime: config validation, `deployment_dir`, `with_artifact_root`, `confine_mounts_on_disk`, launcher, fetch orchestration |
| `crates/iw-weight-fetch/src/lib.rs` | 1140 | resumable fetch: resume, digest verification, stall cut |
| `crates/iw-core/src/benchmark_container.rs` | — | `under_a_root` / `normalise_path` confinement primitives |

## Verdict

**No Critical / High / Medium severity defects found.** The implementation is
well-designed, deterministic, overflow-safe, and unusually careful about the failure
modes an adversarial or merely buggy node could trigger. The security posture is strong.
The findings below are informational: one accepted design trade-off and two bounded-ness
observations. Nothing here blocks relying on the implementation.

## Security properties (verified present)

- **Capability + operator-enrollment double gate** (`server_dynamic.rs`). A registration
  that negotiated the capability is provisioned only if its credential came from an
  operator (`operator_enrolled == !is_proved`); an identity that only proved a key is
  assigned nothing, its facts are not stored, and its `provisioning` is not read. Matches
  the "a stranger" rule.
- **Artifact paths cannot traverse** (`ArtifactSpec::validate`). No leading `/`, no
  `.`/`..`/empty segments, `SET_...` placeholders rejected (even inside a source URL), a
  64-hex lowercase digest is required, and sources are restricted to `file://`/`http://`/
  `https://`. `validate_artifact_set` additionally rejects duplicates, file-vs-directory
  collisions, `.part`/`.sha256` collisions, and u64 size overflow.
- **Deployment directory is confined** (`deployment_dir`). Only `dep_` + `[A-Za-z0-9_]`
  is accepted; the content store (`.blobs`) and any separator or `..` are refused.
- **Mounts are confined to the deployment and forced read-only** (`with_artifact_root`,
  `confine_mounts_on_disk`). `$ARTIFACTS` is substituted only as a whole word; `..` is
  refused; any mount that reaches the artifact root outside the deployment's directory is
  an error; every such mount is read-only; on-disk symlink escapes
  (`dir/link -> ../dep_other`) are caught by canonicalizing. This closes the "a container
  replaces another deployment's weights with a same-sized file" attack the code names
  explicitly.
- **No command injection** (`profile_launch`). The engine is launched via
  `run_bounded(docker_bin, &args, …)` — an argv vector, never a shell string. The
  command/env/mounts come from the operator's profile, not from node input.
- **Supply chain.** The engine image is digest-pinned (`<image>@<sha256:…>`); each
  artifact is verified against its SHA-256 after download (`weight_fetch`) with a
  resumable `.part` and a verified `.sha256`.
- **Evidence is cut to the assigned cells** (`settle_measurement`). A measured report is
  filtered to rows at a context×concurrency the gateway actually assigned, finite and
  positive, one row per cell. A draft is then validated like any profile, must be admitted
  (quantization/allowlist), and must itself qualify for the model. This stops a node from
  injecting evidence at a depth nobody asked for.
- **Per-node assignment cap is enforced on both ends.** `wire_for` takes
  `MAX_ASSIGNMENTS_PER_NODE` (8) on the gateway, and the node's `read` takes the same cap
  and counts the skipped entries.
- **Operator view is admin-only** (`dynamic_view`). `GET /iw/v1/dynamic` requires the
  admin secret because a held assignment carries a launch command.

## Correctness and robustness (verified)

- **Deterministic planner** (`plan`). Failures, refusals, and the placement order are all
  total-ordered (priority → model name; then node id; then oldest holding; then id). The
  same inputs give the same state.
- **F1 adoption** (`reconcile`). A restarted gateway adopts a serving engine rather than
  placing a second one beside it; a `refused` is a disagreement (counted and backed off
  60 s → 600 s) and never retires a profile; a holding the node stops naming for
  `HELD_REPORT_SECS` (300 s) is dropped as a transient failure; at most one active id per
  model is adopted, so an invented second id cannot claim a replica or occupy the node.
- **Placement correctness** (`eligible`). Only the node's free (non-busy) GPUs are used;
  a profile's cards come from the same node's free list (the "cards on one node" rule);
  only the model's quantization/allowlist profiles are judged ("family and name alone
  would let an MXFP4 text profile serve a Q8 vision id"); quality tier → measured decode
  at the floor → name/version is a total order.
- **Overflow-safe** throughout (`saturating_add`/`sub`, `checked_add`, `.min` caps,
  count-prefixed hashing in `deployment_id` so one list can never be read as the head of
  the next).
- **Atomic draft writes** (`write_draft`). Stage under the lock, write to a `.tmp-<pid>`
  file, rename after the lock is released; a `WritingClaim` drop guard releases the name
  on panic and backs the retry off. A torn file is never read by the next start.
- **Stall-cutting fetch** (`FetchPolicy`). A transfer that delivers nothing for the stall
  window is cut, so a half-open connection cannot block the single worker thread forever.

## Findings (informational — none blocking)

**I-1. A node's self-reported measurement is trusted for draft generation.** The evidence
in a `Measured` report is the node's word; the gateway cuts it to the assigned cells and
requires it to qualify, but it cannot independently verify the numbers. A misbehaving (or
merely mis-calibrated) node could therefore cause a draft to be written that over-states
what its hardware achieves, and the gateway would then place the model from that draft on
matching nodes. This is the intended trade-off of gateway-driven measurement (spec 64 §8:
a draft "has measured decode evidence and no quality block" and is `experimental: true`),
and it is contained: the draft is flagged experimental, a resulting failure
(`launch_failed`/`engine_exited`, e.g. OOM) retires the (node, model, profile), and an
operator can inspect or reject the draft before promotion. Not a defect; recorded so the
trust boundary is explicit.

**I-2. Node GPU facts are the node's word for placement.** `eligible` trusts
`free_gpus()` (a card is "free" if the node reports `busy=false`). A node that mis-reports
a busy card as free could be handed a placement that then fails; that is recorded as a
transient failure and retried or expired after `FAILURE_RETRY_SECS`. Bounded and
self-correcting; noted for completeness.

**I-3. `read_facts` runs before authentication.** Like `hardware`, the `dynamic` member is
parsed (and size-bounded to 65 536 bytes) before the credential is checked, so a refusal
leaves no registration. The bound makes this a bounded parse, not a DoS; it is a
deliberate, documented choice. Noted only.

## Test coverage

The module is heavily tested, with explicit `CONTROL` tests that would fail if a specific
invariant were removed: F1 adoption (a node already serving is adopted, not given a second
serve nor a failure), a non-report not unlocking placement, a refusal not retiring a
profile, a measured report cut to the asked cells, zero-rate/zero-context evidence
drafting nothing, a bad draft skipped but a bad operator profile not, and a restarted
gateway adopting a serving engine instead of stopping it. This is strong evidence the
invariants are load-bearing and pinned.

## Conclusion

The Rust reference implementation of spec 64 is high-quality, security-conscious, and
well-tested. I found no defect that blocks relying on it. The one substantive trust
boundary (self-reported measurement evidence, I-1) is an accepted, documented design
trade-off that is flagged `experimental` and self-correcting.

Recommendations (non-blocking):

1. Keep the draft's `experimental` flag prominent in any operator UI, since I-1 means an
   operator should review drafts before promotion.
2. For future work, consider an optional server-side cross-check of a draft's headline
   decode figure (a short re-measure on the placing node) before promotion to a shipped,
   quality-blocked profile — not required for the current contract, which already gates
   production qualification on a separate quality suite.
