# Contracts

Canonical external contracts should be generated from this directory in the implementation repositories.

Required schemas:
- node registration/heartbeat;
- deployment manifest;
- capacity snapshot;
- session/lease;
- routing preferences;
- route explanation;
- error body;
- job/event/artifact;
- public snapshot;
- usage receipt.

Recommended source of truth:
- OpenAPI for HTTP;
- JSON Schema for signed/persisted message documents;
- protobuf only if/when a binary internal transport requires it.

Generated bindings must be CI-checked for drift.


Additional canonical schemas required by resolved decisions:
- encrypted prompt-ledger ingest/acknowledgement;
- GPU hardware inventory;
- software/runtime/deployment fingerprint;
- high-frequency GPU telemetry sample;
- per-request performance/contribution fact;
- direct-route ticket/rendezvous offer.
