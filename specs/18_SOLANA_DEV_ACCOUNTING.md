# 18 — Deferred Development-Only Settlement Adapter

## Status

**DEFERRED. Do not implement this specification yet.**

Re-open only after the owner confirms InferWeave has a working deployed GPU weave with:
- direct-first routing;
- durable prompt ledger;
- full per-GPU telemetry;
- stable deployment qualification;
- global benchmark/contribution warehouse;
- routing/admission/FairShare stable under real load.

## Future constraint

When re-opened, core usage/contribution accounting remains independent of any chain. A replaceable settlement adapter may then be tested against:
- in-memory/local ledger;
- PostgreSQL;
- `solana-test-validator`;
- Solana devnet.

Inference and routing must remain available when settlement is offline.

## Still forbidden

- Solana mainnet;
- real-value payment dependency;
- production minting;
- exchange/value/yield promises;
- plaintext prompts or outputs on-chain;
- rewards for idle or self-reported unverified work.

This file exists only to preserve future design intent without consuming current implementation effort.
