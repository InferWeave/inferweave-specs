# Existing Farm gateway: registration with zero serving capacity

Date: 2026-10-12. Status: approved only for the existing Farm-to-Fry
control-plane registration correction, subject to reviewed source and rollout
checks below.

The operator reported that Farm was absent from Fry's network map and authorized
investigation, fixes and redeployment as needed. Authenticated read-only checks
in that investigation found Farm's gateway reachable with an empty `/v1/models`
list while its GPU jobs waited for Slurm priority. Fry's topology had no Farm
registration. Tracked Farm `gateway-peer.sh` withheld enrollment until
`peer-model.py --publish-ready` found a READY model. A future implementer
following that condition literally would again hide an idle but live gateway.

**Decision:** an authenticated gateway-role peer may register with no model
advertisements when its endpoint, deployment identity and held link are valid.
Serving models and slots remain a separate, current, owner-controlled claim.
Successful empty catalogue snapshots withdraw old model claims; failed reads
retain the last acknowledged state and retry. The GPU-worker rule requiring a
real model and positive slots is unchanged. `hardwareOnly` node registration
does not substitute for a gateway's held link.

This is a narrow correction of existing Farm/Fry visibility, not authority to
launch a new deployment target, schedule work, add a tunnel, change enrollment
credentials, or advertise queued GPU jobs as READY. It preserves the topology
and owner-admission boundaries in specs 40 and 42.

Release conditions: merge independently reviewed source based on the deployed
Farm revision; pass CLI, Farm bootstrap/ops, gateway registration and topology
tests; retain current credentials/identity and rollback artifacts; deploy the
CLI and Farm peer/bootstrap scripts together; observe Farm's vertex in Fry with
zero model capacity before any Slurm grant; then observe READY publication and
withdrawal only when actual capacity changes. A failed health, registration,
link or inference check restores the known-good revision. PR
`InferWeave/inferweave#867` carries the proposed implementation; its merge and
live validation are not established by this decision.

Proof status: local regression tests on the proposed branch have passed, but
the cross-gateway production observation and rollback rehearsal are **owed**.
