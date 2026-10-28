# 03 — Node Bootstrap, Deployment Resolver and Model Lifecycle

## Enrollment/bootstrap

A new node can be brought online with:

```text
install agent
→ generate/load local node UUID
→ generate a persistent node keypair
→ enroll by proof of protocol possession (no operator token)
→ establish outbound mutually authenticated connection
→ advertise hardware/runtime discovery
→ configure desired model intents/deployments
→ resolve/fetch/verify/start/warm
→ publish healthy immutable deployment fingerprints
→ run admission smoke test
→ become schedulable
```

Inbound firewall openings are not required.

### Token-free proof enrollment

Enrollment requires no operator-issued bootstrap token. A node generates a persistent
asymmetric keypair before connecting, selects a gateway explicitly, and earns a renewable role
credential by proving what it actually is.

Enrollment is credential-free, not identity-free. There is no operator approval or promotion
step: the gateway issues the credential automatically once proof succeeds.

Two proofs apply:

- **protocol-role proof** is required of every node;
- **model-execution proof** is additionally required for every model and context class a
  worker advertises.

A challenge result grants eligibility to exactly what was challenged — the signed role, model,
artifact, runtime, quantization, feature set, context class and measured resource claim — and
to nothing adjacent. A node may advertise several models and several context classes per model
within one process or allocation, each separately proven.

This makes the published context ceiling something a node proves rather than asserts. A
capability claim that has not been challenged for a given context class does not license
serving it.

Distributing a shared bootstrap token to every joining node makes the token the credential, so
every holder is equivalent regardless of what it can actually do. Proof binds the credential
to measured capability instead.

The wire shapes of `/v1/node/key`, `/v1/node/challenge` and `/v1/node/proof`, the exact signed
transcript, the error mapping and the open registration policy are defined by
`specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md`; this section stays the design statement.
Spec 47 also defines hardware-only registration (a node recorded without being routable).

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
- swap one GPU to another deployment: drain, stop, pinned load, warm (`43_GPU_PLACEMENT_HOT_SWAP.md`)
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

On a node with more than one accelerator the assignment is per GPU: each GPU carries its own desired deployment, and a node may serve several deployments, or several instances of one deployment, at once. Reassigning a GPU is a swap under `43_GPU_PLACEMENT_HOT_SWAP.md` and never bypasses its drain, dwell or availability floor. A runtime's own on-demand loading and eviction do not decide placement.


## Container deployment

Persistent nodes run through Docker Compose. The bootstrap CLI generates exact GPU device exposure, volumes, networks and watchdog configuration.

Slurm workers use Apptainer as specified in `37_CONTAINER_DEPLOYMENT_STANDARD.md`.

## Optional native tool configuration (2026-10-28)

The existing runtime profile may carry optional camelCase `toolCalling`, defined by
`schemas/v1/runtime/tool-calling.json` and `contracts/tool-call-compatibility.json`. Its
`schemaVersion` is 1. It declares parser configuration; even mode `native` is not qualification.
Absent metadata preserves legacy serialization, deployment fingerprint vectors and launch flags.

Active `experimental`/`native` declarations are accepted only for engine `llama.cpp`, backend
`cpu` or `cuda`, and upstream revision `74bca3950054eed1795f525cb9cf06bfe796492d`, or older base
`32bf0eb37cfecbc7d74b1dd2594ce285bed2f55f` with `parserPatchSha256`
`03e81a8aa0b8834e6951f4e46bb30324521343d6581ede5dd0a78da1a94d6696`. Parser is
`llamaCppDeepseekV41`; optional reasoning is `llamaCppDeepseek`. The older-base backport
requires template SHA-256 `c9046238d418153ed16c1ece7041873556d4c5ae27918a2cc20106d12b0a23f8`;
a differently pinned template is unsupported for that base. A full explicit template is
required under exactly one read-only mount. Validate normalized absolute paths and reject
ambiguous/overlapping mounts, mutable template sources and content-hash mismatches before launch.
Materialized flags are `--jinja --chat-template-file <path>` and, when requested,
`--reasoning-format deepseek`. Conflicting raw template/reasoning flags or environment overrides
are refused. Native vLLM flags are never forwarded to llama.cpp by this declaration.

`unsupported` mode has no parser, patch, template, reasoning or supported operations. Other
pairings remain unsupported pending separately pinned engine-native evidence. Configured support
includes independent `nonStreaming`, `streaming`, `continuation`, `parallel`, `forcedChoice`
tokens; this set is not an eligibility grant. The suite-v1 qualification contract cannot grant
forced choice. Dynamic typed configurations require the spec64 negotiation below. Production
activation and real model/GPU/Pi evidence remain governed by OPEN_GATES.
