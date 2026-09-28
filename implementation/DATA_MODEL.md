# Logical Data Model

Names are conceptual; implementation may normalize differently.

## Control plane
- `nodes`
- `node_credentials`
- `service_instances`
- `deployments`
- `deployment_aliases`
- `capability_profiles`
- `hardware_snapshots`
- `software_snapshots`
- `benchmark_runs`
- `benchmark_samples`
- `gpu_devices`
- `gpu_hardware_snapshots`
- `gpu_telemetry_samples`
- `software_runtime_fingerprints`
- `request_performance_facts`
- `contribution_facts`
- `sessions`
- `session_leases`
- `requests`
- `prompt_records`
- `prompt_messages`
- `prompt_execution_attempts`
- `prompt_access_audit`
- `routing_decisions`
- `route_candidates`
- `fairshare_policies`
- `fairshare_usage`
- `api_keys`
- `accounts`
- `jobs`
- `job_attempts`
- `job_events`
- `artifacts`
- `receipts`
- `public_snapshots`
- `incidents`
- `audit_events`

## Important keys
Deployment fingerprint is immutable.
Session ID survives multiple requests.
Attempt ID distinguishes retries.
Node's private stable identity is separate from rotating/public pseudonym.
Prompt content accepted by a durable sink is stored in the dedicated encrypted
prompt-ledger tables. Ordinary gateway requests first enter the bounded
best-effort recorder and may be absent after an explicitly measured drop;
explicit durable-ingest acknowledgement still proves the record exists. Prompt
content is not duplicated into route/public/economic/metric tables.

## Time series
Do not retain raw high-cardinality telemetry forever. Compact/roll up according to operational needs while preserving audit evidence needed for incidents or qualification.

## No shared DB across planes
AutoSpec, autospec-orchestrator and InferWeave do not share ownership of database tables. Integrate through versioned APIs/events and correlation IDs.


## Resource identity / scheduler tables

```text
providers
clusters
hosts
host_generations
gpus
gpu_partitions
scheduler_allocations
worker_instances
worker_connections
resource_leases
deployment_assignments
artifact_cache_inventory
```

Stable host/GPU rows survive disconnects. Allocation/worker/connection rows are append-only historical lifecycle records where practical.


## Site/cache/lifecycle/bootstrap tables

```text
site_connectors
site_connector_instances
artifact_objects
artifact_locations
artifact_cache_inventory
artifact_transfers
workload_contracts
resource_events
resource_health_assessments
resource_quarantines
demand_forecasts
prestage_requests
benchmark_campaigns
benchmark_tasks
benchmark_task_leases
bootstrap_installations
enrollment_codes
mcp_audit_events
prompt_payload_locations
```
