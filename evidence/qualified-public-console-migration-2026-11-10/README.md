# Qualified public-console migration (IW-DEPLOY-001 / P1-T22)

The operator's 2026-11-10 incident investigation observed a public console whose
image revision label was `8d8940d`, whose `/healthz` omitted `revision`, and whose
Compose configuration-file label included the missing `/tmp/iw-pin.yaml`.
The current installer requires a full 40-character reviewed image label and an
identical running health revision. Those facts prevent ordinary guarded legacy
restoration and complete composition reconstruction from the historical labels.
The public endpoint had previously returned the exact maintenance marker while
health remained successful; the owned gate was recovered separately.

Reproduce the observation read-only on the operated host with Docker inspect
(image ID/labels, Config.Cmd/User/Env fingerprints, HostConfig/Mounts and Compose
file existence), local health, and the administrative loaded-policy endpoint.
Keep raw inspect, credentials, configuration, subjects and responses private.
Public evidence contains digests/identifiers and verdicts only. The operator's
private host snapshot and stage/qualification receipts are not committed here.

Specification defect: spec37 listed artifact identity without requiring a
rollback artifact that could pass the actual restoration guard, or a complete
existing composition before public admission was closed. The added normative
section prevents a literal implementation from treating an unusable legacy
snapshot as sufficient.

Proof status is **owed**, not inferred from this incident note. Required closure:
independent source review; mutation-sensitive baseline/report/phase/pending/
policy/transport guards; real recovered Compose lifecycle; independently routed
accepted inference and loaded-policy proof for target and fallback; bounded
completed-actor recovery; production composition parity; public-path recovery;
and durable private operational receipts with exact implementation revisions.
The implementation is staged for review in InferWeave/inferweave; it is not
production approval or proof that the old image's source has been established.

## Implementation validation, 2026-11-11

[Core Actions run 42981340166](https://github.com/InferWeave/inferweave/actions/runs/42981340166),
commit `0db2aa943f3411bad554de24fd1d89d721c236da`, completed successfully.
Its recorded commands prove 83 Jev tests, real unmodified Go source-2839 gateway
images, a pinned CPU llama.cpp/GGUF engine, authenticated SSH forwarding, actual
nginx TLS, recovered composition despite a missing historical file, forward
activation, settled-target fallback, and recovery from an actually Docker-paused
target with a genuine completed-Compose receipt and owned pending marker.
The archived marker, loaded paid policy and public inference are checked after
recovery. No product health or model responses are fabricated.

The separate statement/branch gate measured 482/539 executable statements
(89.42%) and 208/260 branches (80.00%). Coverage is not guard-removal proof.
A real mode-0600 file of 16,777,217 bytes exercises the private evidence limit;
removing that size guard from a copied implementation makes its regression fail.
The underlying unit guards also reject changed source/configuration/policy,
unowned or incomplete pending state, and a working model route that still depends
on the replaced gateway. The fixture tests real root-owned files and OpenSSH
process metadata without returning secret contents.

**Still owed:** final required repository CI and independent review closure,
production composition parity, freshness of the independently qualified target
and fallback at adoption, actual owned production transition/recovery receipts,
and public model verification after restoration. The CPU fixture proves control
and transport behavior, not production model context/performance envelopes.
This validation does not establish source provenance for the old short-labeled
artifact and does not open a deployment gate by itself.
