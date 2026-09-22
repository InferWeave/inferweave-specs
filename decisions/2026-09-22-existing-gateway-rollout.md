# Existing gateway observability rollout — 2026-09-22

## Authority and scope

The operator explicitly requested: “ok please PR, review merge than deploy”
after reviewing the UC Davis console, traffic attribution/history, and topology
v2 implementation in this session. This authorizes review, merge and deployment
of those changes to the existing site gateway and existing Rust gateway service.
It does not authorize creation of a new fleet, replacement of GPU runtimes,
unrelated controller changes, or a claim of general multi-site qualification.

Read-only deployment discovery confirmed the existing serving path:

- The Go site gateway is supervised by `inferweave-gateway.service`, with the
  CI-approved artifact installer and rollback path described in
  `metabolomics-us/inferweave-gateway/deploy/fry/README.md`.
- The registered Rust peer is the existing Hive Slurm service `iw-gateway-rust`
  (job `23850909` at discovery), launched by
  `/quobyte/metabolomicsgrp/it/llm/iw-rust/scale/iw-gateway-run.sh`. Its registered
  identity at the Fry edge is `node_hive-rust`. Updating this existing service
  and preserving its state is within the operator-authorized rollout.

An earlier discovery record named the separate Fry
`inferweave-adaptive-canary-gateway-1` Compose service as the Rust target. The
edge registry identifies Hive as the actual serving peer, so the release target
is corrected here before deployment. This does not authorize changing the
canary controller, GPU engines, worker allocations, or unrelated applications.

## Release conditions

Independent source review findings must be resolved, required CI must pass,
and local verification must cover the exact reviewed revisions before merge.
Deployment preserves the current configuration, credentials, state and rollback
artifacts. Readiness, deployed revision, populated topology/traffic surfaces and
an inference smoke check are verified after the change. A failed readiness check
triggers rollback through the existing deployment mechanism.

## What this does not prove

This is a bounded authorization to update existing services, not evidence of a
successful rollout. Deployment results must be recorded after they are observed.
Cross-site topology qualification, unsupported held-link metadata transport,
and the other open gates remain unchanged.
