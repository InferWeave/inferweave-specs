# 16 — Security, Privacy, Policy, License and Node Trust

## Identity/auth

- node enrollment + rotating short-lived credentials;
- API keys with scopes/rotation/revocation;
- OIDC for durable user accounts before public multi-user launch;
- route-scoped direct/relay transfer tickets;
- TLS everywhere.

## Node trust

A TLS connection is not proof of honest capabilities. Use:
- signed advertisements;
- freshness TTLs;
- benchmark/profile evidence;
- optional challenge/verification jobs;
- reliability history;
- quarantine after severe/runtime-integrity failures;
- public verification bands without leaking private operator identity.

## Data minimization

Prompts/outputs are excluded from public snapshots, economic receipts and ordinary metrics. Raw payload logging defaults off.

## Policy/license

Deployment manifests declare license and allowed policy profiles. Security/privacy/license constraints are hard during fallback. Private/reduced-refusal model profiles, if supported, are distinct authenticated deployments and never silently fall back to differently governed providers.

## Node admin

Local-only by default. Hosted dashboard cannot retrieve private logs/secrets/model-install controls merely because it can see the node.

## Supply chain

Pin model revisions, container digests and custom kernel/runtime revisions. Scan dependencies/images; preserve qualification artifacts; mount models read-only where feasible; avoid privileged host-wide access.
