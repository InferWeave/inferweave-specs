# 31 — Resource Health, Degradation Detection and Quarantine

## Goal

InferWeave continuously compares each resource against:
- its own historical baseline;
- equivalent peer hardware;
- current deployment/profile expectations.

## Signals

Examples:
- ECC/error counters;
- GPU resets;
- OOM frequency;
- thermal throttling;
- abnormal temperature;
- abnormal power/clocks;
- PCIe downgrade;
- VRAM errors;
- runtime crashes;
- TTFT/prefill/decode regression;
- repeated request failures;
- corrupted artifact/model validation;
- unstable network;
- node heartbeat issues.

## States

```text
HEALTHY
SUSPECT
DEGRADED
DIAGNOSTIC
QUARANTINED
RECOVERING
```

## Policy

- `SUSPECT`: gather extra evidence.
- `DEGRADED`: reduce scheduling preference / constrain workloads.
- `DIAGNOSTIC`: run bounded diagnostics/qualification.
- `QUARANTINED`: no normal public/shared routing.
- `RECOVERING`: limited canary traffic before return to HEALTHY.

Physical owner policy still applies; InferWeave may warn the owner even when shared routing is disabled.

## Automatic comparison

Use robust statistics and minimum sample counts. A single slow request must not quarantine a GPU.

Never compare unlike workloads/fingerprints as if equivalent.

## Dashboard/MCP

Expose:
- state;
- reasons;
- first/last occurrence;
- evidence;
- peer comparison;
- recommended remediation;
- qualification/recovery progress.
