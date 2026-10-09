# 51 — Typed Inference Pipelines

## Relationship to existing surface

[`schemas/v1/jobs/`](../schemas/v1/jobs/), [`state-machines/job.md`](../state-machines/job.md),
and [`specs/15_ASYNC_JOBS_ARTIFACTS.md`](15_ASYNC_JOBS_ARTIFACTS.md) define the
durable job and artifact model. [`specs/33_RESUMABLE_BENCHMARK_DAG.md`](33_RESUMABLE_BENCHMARK_DAG.md)
defines a benchmark DAG. This specification generalises the DAG into a **typed
inference pipeline** contract — a DAG of runtime-family stages executed against
the native `/inferweave/v1` surface — and defines its wire schema. RAG-as-a-pipeline
is a canonical first-class pipeline, not a special ad-hoc path.

## Pipeline contract

A pipeline is an ordered acyclic graph of stages. Each stage:

- has a `stage_id`;
- references exactly one runtime family (from the
  [`specs/48`](48_RUNTIME_FAMILIES_AND_CAPABILITIES.md) registry) and a
  resolved runtime target;
- declares typed inputs and outputs (modality + shape);
- declares a dependency set (DAG edges) within the same pipeline;
- may declare a fallback runtime target.

Extend `schemas/v1/requests/request.json` (or add `schemas/v1/requests/pipeline.json`)
with a `pipeline` request object carrying: `pipeline_id`, `stages[]`, and the
entrypoint inputs. `POST /pipelines/execute` accepts this object, validates the
DAG, resolves each stage to an admitted runtime, and returns either an inline
result or a durable job reference ([`specs/52`](52_DURABLE_INFERENCE_JOBS.md)).

## RAG as a pipeline

A canonical `rag` pipeline is defined as the composition of `embeddings` (or
`reranking`) retrieval stages and an `llm` generation stage, wired by explicit
DAG edges. It must not bypass the `embeddings`/`reranking`/`llm` admission and
capacity accounting that applies to the individual stages. The pipeline graph
is the single definition; no separate ad-hoc RAG path exists.

## Validation

- The DAG must be acyclic; a cycle is a typed validation error.
- Every stage's family must be present in the canonical registry and resolvable
  to an admitted runtime at execution time.
- Stage outputs must match downstream stage inputs (modality + shape) or the
  pipeline is rejected.

## Required tests

- dag-acyclicity: a cyclic pipeline is rejected with a typed error.
- stage-family-resolution: a stage referencing an unknown or unadmitted family
  fails validation.
- rag-composition: the canonical `rag` pipeline is expressible as stages and
  respects per-stage capacity accounting.
