# 03 — Node Bootstrap, Deployment Resolver and Model Lifecycle

## Enrollment/bootstrap

A new node can be brought online with:

```text
install agent
→ generate/load local node UUID
→ enroll with short-lived operator token
→ establish outbound mutually authenticated connection
→ advertise hardware/runtime discovery
→ configure desired model intents/deployments
→ resolve/fetch/verify/start/warm
→ publish healthy immutable deployment fingerprints
→ run admission smoke test
→ become schedulable
```

Inbound firewall openings are not required.

## Deployment identity

A deployment is an immutable normalized manifest including:
- model repository/revision/hash;
- tokenizer revision/hash;
- modality/tasks;
- runtime/backend + exact versions/container digest;
- quantization/precision;
- context/KV precision;
- attention implementation;
- TP/PP/sharding;
- speculative/MTP/drafter configuration;
- adapters/workflow hashes;
- policy and license compatibility;
- resource envelope;
- validation/benchmark profile.

Any material change produces a new fingerprint.

## Deployment resolver states

`DECLARED → RESOLVING → FETCHING → VERIFYING → STARTING → WARMING → HEALTHY`

Other states:
`DRAINING`, `STOPPED`, `FAILED`, `INCOMPATIBLE`, `QUARANTINED`.

State transitions are idempotent and observable.

## Lifecycle operations

- ensure/install
- verify checksums/license metadata
- load/start
- warm/health-check
- drain
- stop/evict
- update by creating a new deployment
- rollback to previously qualified deployment
- requalify after driver/runtime/kernel/model/topology changes

Aliases such as `inferweave/qwen-coding` resolve to qualified deployment IDs; they are not mutable runtime descriptions.

## Local operator surface

Node configuration, secrets, model installation, payout keys, shutdown and updates remain local-only by default via CLI/TUI/loopback admin UI.


## Stable resource identity vs worker identity

Use `26_RESOURCE_IDENTITY_REDISCOVERY.md`.

A node registration distinguishes stable host/GPU identities from temporary worker/allocation/connection identities. Every reconnect performs fresh discovery and links the new session to the historical resource record.

## Gateway desired-deployment assignment

Nodes register capability/cache/lifetime facts and request desired deployments from the gateway/control plane.

The gateway chooses deployment(s), returning immutable model/runtime/profile manifests and signed artifact references. The node then fetches/loads/verifies/warms and advertises readiness.

The gateway should not normally proxy model artifact bytes itself.


## Container deployment

Persistent nodes run through Docker Compose. The bootstrap CLI generates exact GPU device exposure, volumes, networks and watchdog configuration.

Slurm workers use Apptainer as specified in `37_CONTAINER_DEPLOYMENT_STANDARD.md`.
