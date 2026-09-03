# Local Development Stack

Initial Compose topology:
- postgres
- inferweave-gateway
- inferweave-node-a
- inferweave-node-b
- mock-openai-a
- mock-openai-b
- Next.js dashboard
- optional solana-test-validator profile

Use deterministic mock backends to simulate:
- model list;
- streaming tokens;
- latency;
- context limits;
- overload;
- mid-stream crash;
- malformed response.

Real GPU backends are separate opt-in profiles.

Bind administrative endpoints to loopback in local examples. Never commit credentials. Use `.env.example` with placeholders.

Add network fault profiles later using `tc`/Toxiproxy or equivalent.


## Prompt/telemetry development
Use PostgreSQL partitions for prompt records, GPU telemetry and request performance facts.
Fixture prompts must include secret-like markers to verify that logs/public APIs never leak stored prompt content.

## Direct-path testing
Run clients/local proxy and nodes on distinct Docker networks/namespaces and assert the gateway process does not receive response-stream bytes on successful direct routes.
