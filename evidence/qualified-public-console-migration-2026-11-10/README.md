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

At the initial incident capture, proof status was **owed**, not inferred from
this note. Required closure at that checkpoint:
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

**Remaining at the CI-only checkpoint (see the later production observation):**
final required repository CI and independent review closure,
production composition parity, freshness of the independently qualified target
and fallback at adoption, actual owned production transition/recovery receipts,
and public model verification after restoration. The CPU fixture proves control
and transport behavior, not production model context/performance envelopes.
This validation does not establish source provenance for the old short-labeled
artifact and does not open a deployment gate by itself.


## Selected production adoption, 2026-11-11

The required Core CI and independent review completed, and
[Core PR #1545](https://github.com/InferWeave/inferweave/pull/1545) merged as
`8f65e6ef3a096e21efc1e8a860d06819cd296d65`. The explicitly authorized selected
forward production migration then completed with live Go source
`e42e0cb2f8f3fc31586757232677179b45baffd1` and immutable image
`sha256:1aee8a26721d5f445c2e8220783eedf75d7d6959a721cbb798c0f5dc70e2d449`.
The loaded default-deny policy retained digest
`8d8e0f8f704167ba615ddc0c621810654ececa0f6b6507283eab02909f0b8d5d`.
Actual internal and off-host public checks for the four canonical baseline chat
models returned HTTP 200, terminal `stop`, SSE `[DONE]` and nonempty visible
content, including after owned scratch/tunnel cleanup. Paid gateway health, its
bridge and capacity were checked; paid inference was not exercised.

The [sanitized Core incident record](https://github.com/InferWeave/inferweave/blob/88a464d/docs/operations/public-console-recovery-20261111.md)
and [receipt summary](https://github.com/InferWeave/inferweave/blob/88a464d/docs/operations/evidence/public-console-recovery-20261111/summary.json)
pin public identities and private source-receipt hashes. They publish no
credentials, private addresses, prompts, response bodies or latency claims.
The private backup and full-source fallback artifacts were preserved.

Inventory is observation-scoped: six serving-worker nodes/eleven workers at the
pre-drain rejoin snapshot, then ten workers after controlled retirement of owned
old Farm job `40564432`. Its occupancy and all four slots were idle, an independent
Hive inference floor and public path were proven, and ownership/resource guards
passed before retirement. Candidate `40578710` remained `PENDING` with `Priority`
in the retained receipt. The selected CLI/queued spool requests 57,344 MiB
(56 GiB); the actual running replacement flag and worker reappearance remain
**owed**, without scheduler priority changes or a promised start time.

The monitor activation at 08:55 UTC succeeded, but its later scheduled 09:06:49
UTC run correctly failed for the missing expected Farm serving node. Its public
canary, revision and paid checks stayed OK. The off-host 09:10:33 UTC scheduled
run passed and its timer remained enabled/active. Email evidence establishes
provider acceptance only, not inbox delivery. This is not an all-green fleet
claim while the Farm candidate queues.

**No production rollback was exercised.** Actual CI rollback/recovery and live
scratch fallback qualification are distinct evidence. This closes the selected
forward production-parity observation, not general production approval, every
configuration, remaining mutation proof or all P1-T22 controls. The pending actual
56 GiB runtime observation can be appended when the owned candidate starts;
until then it must not be described as active.
