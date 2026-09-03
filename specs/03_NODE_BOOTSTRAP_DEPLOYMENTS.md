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

### Serviceability gate

`run admission smoke test` means a real request traversing the full authorization and
admission path, not a liveness probe. A node becomes schedulable only when that succeeds.

Every fail-closed gate ships a working default policy with its installer. A correctly
fail-closed gate with no policy present refuses every request while the process reports
healthy: the node starts and serves nothing.

A node that cannot serve fails its own installation. This class of defect must not be
discovered by the first user request.

## Deployment identity

A deployment is an immutable normalized manifest including:
- model repository/revision/hash;
- tokenizer revision/hash;
- modality/tasks;
- runtime/backend + exact versions/container digest;
- quantization/precision;
- context/KV precision;
- maximum context window (`max_context_tokens`);
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

### Context-size aliases

A context-size alias — `…-32k`, `…-128k`, `…-262k` — is a request-shaping hint carrying the
caller's intended context against a single deployment. It is not a separate qualified
deployment.

Treating each size as its own deployment multiplies deployments for one loaded model and
reintroduces the fixed context tiers invariant 4 forbids.

The ceiling always belongs to the deployment. An alias may request less than
`max_context_tokens`; it can never raise it. An alias naming more than the deployment provides
is refused under the ceiling rule rather than silently downgraded.

## Context window sizing

A deployment loads at the largest context its measured resource envelope safely permits, not
at an operator-chosen constant, and the resulting value is published as its
`max_context_tokens`.

Node-local context size is therefore derived, not configured. When nodes choose windows
independently, a request that fits one node fails on another and the fleet stops being
interchangeable — clients cannot share capacity whose shape they cannot predict.

A smaller window may be chosen only to satisfy a stated resource or safety constraint, and
that reason is recorded with the deployment.

## Capability precedence and cold start

A runtime that loads models on demand reports no context window for a model it has not loaded.
Measure-before-admit therefore cannot bootstrap: the model does not load until a request is
admitted, and no request is admitted until the model is measured.

Capability claims resolve in a fixed precedence:

1. **declared** — taken from the immutable deployment manifest, usable before first load;
2. **measured** — observed from the running runtime, superseding declared;
3. **persisted** — the last measured value, retained across restarts so a model that has been
   resident once remains admissible while unloaded.

Persistence is keyed by deployment fingerprint, so a new fingerprint starts from declared
again. Invariant 16 governs when a claim goes stale; this section governs what may be trusted
before any measurement exists.

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
