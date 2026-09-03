# 02 — Protocol and API Surfaces

## Public compatibility `/v1`

Initial:
- `GET /v1/models`
- `POST /v1/chat/completions`
- `POST /v1/responses`
- `POST /v1/embeddings` when an embedding capability is present

Later/conditional:
- `POST /v1/images/generations`
- compatible image edit endpoints where semantics can be honored

OpenAI compatibility is a public contract. InferWeave-specific metadata may be supplied through documented headers or an optional `inferweave` request object without breaking standard clients.

## Native `/api/v1`

Minimum:
- nodes/capabilities/capacity/heartbeats
- deployments and model lifecycle
- sessions
- route preview/decision inspection
- FairShare policy/admin
- benchmark profiles
- asynchronous jobs/events/artifacts
- public snapshot/status
- API-key/account administration
- drain/undrain and other authorized admin mutations

## Routing preference object

Support:
- purpose/workload class;
- selection mode: fastest/cheapest/private/greenest/balanced;
- allowed/denied model families;
- minimum context;
- exact deployment flag;
- quantization/precision preferences;
- GPU vendor/class preferences;
- regions/max RTT;
- privacy/retention tier;
- verification requirement;
- maximum queue/TTFT and minimum decode targets;
- relay allowance;
- explicit fallback flags.

Hard constraints never relax. Soft preferences may relax only when their matching fallback flag permits it, and every relaxation is reported.

## Response metadata

At minimum:
- request ID
- actual deployment/model
- coarse GPU class
- region band
- route reason
- fallbacks applied
- queue time
- TTFT where known

Never disclose private stable node addresses to untrusted public clients.
