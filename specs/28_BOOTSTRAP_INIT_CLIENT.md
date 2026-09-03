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
