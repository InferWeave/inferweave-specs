# 28 — Zero-Friction Bootstrap / Init Client

## Goal

Setting up InferWeave must be simple enough that an operator can paste one instruction into an AI coding/operations assistant and let it perform the installation.

The canonical interface is one Rust binary:

```text
inferweave
```

The same CLI initializes:
- gateway/control plane;
- GPU node;
- edge/relay node;
- site connector;
- Slurm allocation worker;
- local client/proxy;
- all-in-one development environment.

No role should require hand-writing YAML for the normal path.

## AI-first operating contract

Every discovery/planning/health command supports:

```text
--json
```

Output must use versioned machine-readable schemas and stable exit codes.

An AI assistant should be able to execute:

```text
inferweave doctor --json
inferweave init plan gateway --json
inferweave init gateway --yes --json
inferweave verify --json
```

and make safe decisions from structured results.

## Installation UX

The project should publish:
- a signed standalone CLI binary;
- platform packages where useful;
- a minimal bootstrap installer;
- container images.

Documentation may present a one-line installer, but scripts must be inspectable and cryptographically verifiable before execution.

Example documentation shape:

```text
Install the InferWeave CLI, then run:
inferweave init gateway
```

Avoid making `curl | sh` the only supported installation method.

## Core commands

```text
inferweave doctor
inferweave probe
inferweave init plan <role>
inferweave init <role>
inferweave enroll
inferweave verify
inferweave status
inferweave logs
inferweave update
inferweave backup
inferweave restore
inferweave uninstall
inferweave mcp
```

Roles:

```text
gateway
node
edge
site
proxy
slurm-worker
dev
```

## `doctor`

Read-only checks:
- operating system/kernel/architecture;
- CPU/RAM/storage;
- Docker/Podman availability/version;
- container runtime health;
- ports/listeners;
- DNS/FQDN;
- outbound/inbound connectivity;
- TLS prerequisites;
- filesystem paths/free space;
- time synchronization;
- GPU vendor/model/UUID/VRAM/topology;
- NVIDIA/AMD/Intel driver stack;
- ROCm/CUDA/Vulkan;
- Slurm environment when present;
- current InferWeave installation;
- potential conflicts.

`doctor` never makes changes.

## `probe`

Produces the canonical InferWeave hardware/software fingerprint and recommended role configuration.

Example JSON includes:

```text
hardware
gpus
drivers
runtimes
network
storage
scheduler
container_runtime
recommendations
warnings
blocking_issues
```

## Planning before mutation

`inferweave init plan <role>` must generate an explicit plan:

```text
containers/images to install
ports
volumes
networks
directories
users/groups
TLS/enrollment actions
database/object-store actions
GPU device mappings
firewall changes requested
systemd/launch integration
estimated disk footprint
rollback plan
```

The plan can be reviewed by a human or AI before `init`.

## Gateway init

`inferweave init gateway` should be capable of setting up the complete first usable control-plane stack using containers.

Default components:

```text
inferweave-gateway
inferweave-web
inferweave-mcp
postgres
prompt/artifact object store if enabled
telemetry/metrics support required by selected profile
```

Responsibilities:
- create config directories/volumes;
- generate gateway identity;
- generate internal service secrets;
- initialize DB/schema;
- create bootstrap administrator;
- configure TLS or provide explicit local-only mode;
- expose web UI;
- expose enrollment API;
- configure backups/retention defaults;
- run health verification;
- emit gateway enrollment information.

## Node init

`inferweave init node --gateway <gateway>`:

1. run hardware probe;
2. detect GPU/runtime/container requirements;
3. obtain or accept one-time enrollment credential;
4. establish persistent node identity;
5. generate container configuration;
6. configure only allocated/approved GPUs;
7. start node service;
8. connect outbound;
9. verify registration;
10. run smoke benchmark;
11. display stable node/GPU IDs.

The normal path should be interactive and require only:
- gateway URL or enrollment code;
- operator approval.

## Edge init

An **edge** role is a persistent network/data-plane helper, usually without a GPU.

It can combine approved subsets of:
- regional/site relay;
- rendezvous;
- artifact cache;
- local proxy aggregation;
- public API edge;
- site connector functionality;
- metrics forwarding.

The init plan asks which edge capabilities are desired and generates only those containers.

## Site connector init

`inferweave init site` detects:
- Slurm binaries/config;
- cluster name;
- scheduler connectivity;
- shared filesystem/cache locations;
- outbound connectivity;
- local relay possibilities.

It creates:
- stable cluster/site identity;
- scheduler adapter config;
- cache config;
- worker enrollment mechanism;
- persistent connector service.

## Slurm worker init

Normally invoked inside a job:

```text
inferweave init slurm-worker --site <site>
```

It is non-destructive and allocation-scoped:
- discovers only allocation-visible GPUs;
- obtains short-lived worker credentials;
- registers;
- requests desired deployment;
- fetches/loads;
- serves/benchmarks;
- drains on signal/time limit.

## Container runtime

Supported deployment runtimes are role-specific:
- Docker Engine + Docker Compose for gateway/node/edge/site/proxy/dev;
- Apptainer for `slurm-worker`.

Do not generate Podman/Kubernetes/bare-host production deployment.

Prefer non-root container execution where GPU/runtime requirements permit. GPU support is vendor-aware and validated before service startup.

## Generated configuration

The CLI may generate Docker Compose or Apptainer launch artifacts, but those are implementation artifacts, not the user interface.

Configuration is stored in a clear standard directory and can be exported:

```text
inferweave config export
```

## Idempotency

Running init twice must not create a second identity or duplicate stack.

The CLI:
- discovers existing installation;
- shows intended changes;
- upgrades/reconciles when safe;
- requires explicit destructive flags for reset/re-enrollment.

## Enrollment UX

### Gateway-created one-time enrollment

On gateway:

```text
inferweave enroll create --role node
```

Returns:
- short human-readable code;
- expiry;
- optional copy/paste command.

On node:

```text
inferweave init node --gateway https://gw.example --code ABCD-EFGH
```

The code is one-time/short-lived and exchanges for normal node credentials.

### Browser/QR path

The gateway web UI may generate enrollment links/QR codes for convenience.

## Truthful operational results and explicit external inspection

IW-BOOT-004 / IW-BOOT-002: command success describes the operation actually
performed. A sizing plan must not report that a node started or joined. A
failed initialization smoke check returns a nonzero operational result while
retaining the structured diagnostic report. Artifact preparation alone is not
gateway enrollment or runtime readiness.

`inferweave system status --deployment-dir <directory>` (legacy spelling
`inferweave status`) may inspect an explicitly selected external deployment
package without taking lifecycle ownership. The first supported implementation
is the versioned Beast external package; this does not establish a generic
profile loader or a new deployment substrate.

The optional status extension reports the spec-50 deployment ID/key, model,
engine/backend, external ownership and configured resource limits only after
checking schema versions, closed top-level field sets, canonical identity,
bound profile/resource/policy digests and the exposed resource-limit invariants.
Nested launch, hardware and policy fields outside these checks are opaque digest
inputs: their types and execution semantics are not fully validated. A rehashed
package may be self-consistent while unsuitable for execution; the external
owner's verifier and qualification remain required before adoption or admission.
Earlier wording, "checking supported schemas", overstated this inspection boundary
and could cause consumers to mistake digest agreement for launch validation. Do
not reuse the inspector as a general nested runtime/profile-schema validator.
Read a bounded set of fixed regular documents with duplicate-key rejection,
bounded size and supported canonical encoding. Do not follow document-supplied
paths, symlinks or access credentials, start processes, query Docker or contact
an endpoint. Errors must not echo document content.

Hash agreement means self-consistency, not authenticity or qualification: a
modified package whose hashes are recomputed remains a different deployment.
Offline inspection reports runtime state UNKNOWN, available capacity unknown
and evidence not checked. It cannot grant admission, publish READY, transfer
ownership or replace the existing owner's verifier, guard or pinned lock.
The command does not establish that the public gateway preserves deployment
identity or runtime observations. Missing this capability is disclosed, never
inferred from a health endpoint. No routing or production gate opens here.

Public profile decision/report output redacts credential-bearing launch
arguments and environment values unless explicit reveal is requested. An
explicitly requested protected local launch-state artifact may retain launch
values for drift checking; it is private state, not a public report.

## Foreground managed-profile client

IW-BOOT-001/IW-BOOT-004 and IW-RT-003 reuse the existing owner control contract in
spec50. The normal managed invocation is:

```text
inferweave node run --profile FILE --controller https://owner.example --control-token-file TOKEN_FILE --worker-ids worker-a,worker-b --json
```

`--gateway` aliases `--controller`; both may be supplied only for the same origin.
This client neither enrolls a node nor starts a new controller, allocator or standalone
Docker engine. `--model` selects an optional owner-canonical ID; otherwise the profile's
`match.model.name` is used. `servedModel` remains the separate backend HTTP identity.
The exact raw-file SHA-256 must match the owner's binding. `--request-id` supplies a
stable retry identity; omitted IDs use fresh OS entropy. IDs use the same validation as
the owner and worker IDs must be unique, with at most 256 workers.

`--dry-run` validates the typed profile and emits an inspectable logical plan without
network, token access, hardware discovery or worker input. It exposes no launch commands,
environment values or readiness claim. Image/engine/backend/runtime/weights, host GPU
selectors and enrollment/port overrides are rejected in managed profile mode rather than
silently ignored. Legacy `node run --model NAME --dry-run` remains sizing only; legacy real
execution without a profile remains unsupported. Managed-only flags require `--profile`.

Real execution requires an HTTP(S) owner origin without userinfo, path, query or fragment,
and a regular token file of mode 0600, at most 4096 bytes, with no symlink following.
Profile and HTTP response reads are bounded to 1 MiB. Calls have bounded timeouts, disable
ambient proxies and redirects, and never echo bearer tokens or raw owner error bodies.
The CLI retains the existing versioned envelope and exit vocabulary; progress uses stderr.

An HTTP 202 ensure acknowledgement means queued, never ready. The client polls
`GET /internal/orchestrator/snapshot?request_id=<URL-form-encoded ID>`, using the bounded
request projection in spec50 so retained history cannot exceed its response-read budget.
The projection retains the original snapshot timestamp/revision rather than manufacturing
freshness; unfiltered diagnostic reads remain compatible. The client
checks request/model/version/profile/worker intent and stable instance identity, and observes
`ready`/`active` only with the matching worker assignment. Snapshots must be fresh within
30 seconds, with nondecreasing timestamps; owner and client clocks must meet that bound.
Readiness observation reports the laboratory lifecycle only. Managed-profile models,
aliases, instances and activation candidates remain excluded from ordinary router
discovery/admission, including the shadow catalogue,
and ordinary demand does not auto-place them, until genuine qualification integration.
There is no configuration boolean that promotes warm/healthy profiles to qualified routing.
The CLI never grants qualification or bypasses existing router/node admission.
The foreground client stays attached after readiness. SIGINT/SIGTERM requests cancellation
of its owner request, then waits for owner-confirmed instance removal and assignment release.
Cancellation while loading uses the same owner path. It never force-deletes an engine or
reuses the enrollment process's force-exit handler.

`--startup-timeout-secs` defaults to 600 (1–86400), `--drain-timeout-secs` to 120
(1–3600), and `--poll-ms` to 500 (20–10000). Startup timeout requests owner cancellation
and remains a nonzero result even after confirmed cleanup. Normal cancellation succeeds
only after confirmed release. Post-submit errors retain `requestId` and
`ownerConfirmedStopped`; stale/mismatched state, control loss or an unconfirmed drain
returns a nonzero result and the reconciliation identity, without asserting the engine
stopped. Composition with a live owner/helper and hardware qualification remain **owed**
in OPEN_GATES; a dry-run or fake-owner test cannot close those gates.

## Runtime-selection configuration boundary

The gateway's optional placement filter is configured through
`routing.runtime_selection_file` in its central YAML file supplied by `--config`.
Unset/null keeps selection off; empty paths and named missing or malformed files
fail startup. The unsupported `IW_RUNTIME_SELECTION_CONFIG` environment variable
is not a fallback. This repairs the implementation's conflict between rejecting
legacy environment configuration and later requiring that variable to activate
the filter. It adds no qualification, reservation, lifecycle or production authority.

## Security

- one-time bootstrap credentials;
- no long-lived secret in docs/examples;
- minimum container privileges;
- no host Docker socket exposed to untrusted containers;
- image digests/signatures verified;
- no automatic firewall opening without plan/approval;
- sensitive output redacted from `--json` unless explicit reveal;
- local configuration file permissions checked;
- generated secrets backed up according to role.

## Updates

`inferweave update`:
- checks signed release metadata;
- shows current/target versions;
- pulls pinned images;
- runs DB compatibility check;
- creates backup/checkpoint;
- performs rolling/restart update;
- verifies;
- rolls back if supported and verification fails.

## Troubleshooting bundle

```text
inferweave support-bundle
```

Produces a redacted archive containing:
- versions;
- hardware/runtime fingerprints;
- config with secrets removed;
- container states;
- recent health/errors;
- relevant telemetry;
- connectivity tests.

Prompt content is excluded by default.

## AI Assistant Bootstrap Prompt

Ship a canonical text file:

```text
docs/AI_INSTALL_INFERWEAVE.md
```

It instructs an AI assistant to:
1. install/verify the CLI;
2. run `doctor --json`;
3. run `init plan <role> --json`;
4. explain blocking issues;
5. perform safe initialization;
6. run `verify --json`;
7. fix only issues supported by the plan;
8. never expose secrets;
9. leave the final machine registered and healthy.

This prompt is designed to be copy/pasted into Pi, Claude Code, Codex or another shell-capable assistant.
