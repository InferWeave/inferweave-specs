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
