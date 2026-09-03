# 33 — Resumable Benchmark DAG

## Goal

Benchmark/qualification work must survive Slurm preemption and other ephemeral-resource loss.

## Decomposition

```text
benchmark_campaign
  └── suite
       └── deployment/profile
            └── workload
                 └── case
                      └── repetition
```

Each leaf is:
- immutable;
- independently schedulable;
- idempotent;
- small enough to fit common backfill windows;
- committed as soon as complete.

## Scheduler

Workers lease benchmark leaves with deadlines.

A lease includes:
- benchmark task ID;
- required hardware/resource class;
- deployment fingerprint;
- estimated runtime;
- input artifact references;
- result schema;
- lease expiry.

If a worker disappears:
- incomplete lease expires;
- task returns to READY;
- completed samples remain committed.

## Partial campaigns

A campaign can produce provisional evidence before 100% completion, but recommendation confidence reflects missing samples.

## Slurm integration

Before assigning a leaf:

```text
estimated setup/load time
+ estimated case runtime
+ result flush margin
< remaining safe allocation time
```

Prefer already-loaded/cached profiles.

## Checkpointable long evaluations

For evaluations that cannot be decomposed sufficiently, define explicit checkpoint artifacts with immutable continuation metadata.

## Dashboard

Show:
- campaign completion;
- pending/running/expired tasks;
- resource classes;
- confidence achieved;
- remaining expected compute;
- preemption losses;
- resume history.
