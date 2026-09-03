# 29 — InferWeave MCP Servers

## Goal

AI assistants should be able to inspect InferWeave directly instead of asking operators to copy logs, GPU statistics or benchmark tables into chat.

InferWeave exposes MCP servers backed by the same authenticated APIs and authorization model as the dashboard/CLI.

Target current MCP protocol compatibility at implementation time. Initial design targets the 2026-07-28 stateless MCP model.

## Server roles

### Control-plane MCP

Runs alongside/behind the gateway:

```text
inferweave-mcp
```

Provides cluster-wide information.

### Local MCP

The CLI/node/site connector can expose a local MCP transport for machine-specific diagnostics.

```text
inferweave mcp serve --scope local
```

This allows an AI assistant operating on the machine to inspect:
- hardware;
- GPU;
- runtime;
- config health;
- containers;
- connectivity;
- node/site registration;
- local logs;
- caches;
- benchmark status.

## Read-only by default

Default MCP scopes are read-only.

Mutation tools require:
- authenticated principal;
- explicit authorization scope;
- audit record;
- normal InferWeave policy checks.

Dangerous host operations are not exposed as generic shell execution.

## MCP resources

Examples:

```text
inferweave://cluster/summary
inferweave://gpus
inferweave://gpus/{gpu_id}
inferweave://nodes
inferweave://nodes/{node_id}
inferweave://sites
inferweave://sites/{site_id}
inferweave://models
inferweave://deployments
inferweave://recommendations
inferweave://benchmarks
inferweave://routes/recent
inferweave://sessions
inferweave://capacity
inferweave://health
inferweave://events
inferweave://builds
```

Authorized private resources can include:

```text
inferweave://prompts/{prompt_id}
inferweave://sessions/{session_id}/history
inferweave://nodes/{node_id}/logs
```

Prompt resources require prompt-content read permission and create an audit record.

## MCP tools

Read/diagnostic:

```text
cluster_status
list_gpus
get_gpu
list_models
get_model_recommendation
compare_model_profiles
get_node_health
get_site_health
get_capacity
explain_route
get_request_trace
get_benchmark_results
get_resource_history
get_resource_events
get_artifact_cache_status
run_readonly_probe
generate_support_bundle
```

Controlled actions:

```text
create_enrollment_code
request_node_reprobe
request_deployment
drain_node
run_benchmark
qualify_profile
retry_artifact_fetch
```

Higher-risk operations require stronger scopes and may require interactive approval.

## Bootstrap MCP use

After gateway install, the CLI prints/configures an MCP endpoint descriptor suitable for supported AI clients.

An assistant can then ask:
- "Which GPUs are connected?"
- "Why isn't node X schedulable?"
- "What model should this R9700 run?"
- "Which runtime regression reduced Qwen performance?"
- "Show allocation history for this Slurm GPU."
- "Why was request X routed to node Y?"
- "Which sites need model artifact pre-staging?"

## Schema and discoverability

MCP resource/tool schemas are generated from canonical InferWeave domain/API schemas where possible.

Avoid building a second independent data model for MCP.

## Authorization

MCP authorization maps to InferWeave scopes such as:

```text
cluster:read
telemetry:read
benchmarks:read
routes:read
logs:read
prompts:metadata
prompts:content
nodes:operate
benchmarks:operate
enrollment:create
```

No MCP server bypasses tenant/site/privacy boundaries.

## Stateless scale

The remote MCP service should avoid dependence on in-memory client sessions. Any request should be routable to any healthy MCP instance using ordinary load balancing.

## Caching

Stable list/catalog responses should expose appropriate MCP cache metadata where supported.

Never cache private prompt content across principals.

## Auditing

Record:
- MCP caller;
- method/tool/resource;
- target object;
- authorization decision;
- mutating action/result;
- prompt-content access;
- timestamp/request correlation.

## No generic arbitrary shell

Do not expose:
- arbitrary shell;
- arbitrary SQL;
- arbitrary filesystem traversal;
- unrestricted container socket;
- raw secrets.

Use typed, bounded diagnostic/operation tools.
