# 32 — Demand Forecasting and Deployment Pre-Staging

## Goal

Use observed demand and available future/ephemeral capacity to reduce cold-start time and improve useful capacity.

## Forecast dimensions

Forecast at useful levels:
- model/deployment;
- workload class;
- region/site;
- time-of-day/day-of-week;
- user/team class;
- expected context/concurrency.

Do not require ML initially. Begin with transparent moving-window/seasonal statistics.

## Decisions

Forecasting may suggest:
- which artifacts to pre-stage at a site;
- which model to assign when a Slurm GPU appears;
- which resident model to keep loaded;
- where to preserve large-context headroom;
- which benchmark candidates to explore during spare capacity.

## Objective

Conceptually optimize:

```text
predicted demand
× model/workload usefulness
× measured hardware efficiency
× cache locality
× expected resource lifetime
× reliability
- download/warmup cost
```

## Safety

A forecast never overrides:
- hard model/capability constraints;
- owner priority;
- site license/policy;
- privacy;
- resource lifetime feasibility.

## Explainability

Every pre-stage/deployment suggestion stores reasons and input forecast facts.
