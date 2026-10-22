# 66 — Normalised engine metrics: one traffic contract over every serving runtime

## Status

**SPECIFICATION — PROPOSED.** Describes behaviour that is **implemented** in the reference
implementation (`InferWeave/inferweave`, merged as #1139, `crates/iw-cli/src/node_metrics.rs`
and `metrics_adapter.rs`). Where this text and the implementation disagree, this text is the
contract and the difference is a defect to record in `OPEN_GATES.md`. Required tests are recorded
`owed` until a conformance fixture set exists (section 7).

The key words MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119.

## 1. Purpose

A node serves through llama.cpp, vLLM, SGLang, Strata or another runtime. Each names its
Prometheus counters differently and counts different things. Anything that shows or reasons about
a node's traffic (the node's own page, `ADR 2026-10-21 role-scoped embedded UIs`) MUST read one
normalised shape, so that no consumer branches on the runtime. This is the runtime-neutral rule
for metrics.

Non-goals: authoritative accounting (usage, billing and admission stay with the gateway); anything
reported upstream; a metrics store (section 6 is display only).

## 2. The normalised sample

One read of an engine's `/metrics` yields a **sample** (read time in unix seconds, the engine
family, cumulative totals, and two gauges).

| Field | Meaning |
| --- | --- |
| `prompt` | Prompt tokens received, cached or not. |
| `processed` | Prompt tokens the engine computed (the prefill work). |
| `generated` | Tokens generated. |
| `prefill_secs`, `decode_secs` | Seconds the engine reports spending on each phase. Optional. |
| `cache_hits`, `cache_queries` | Prompt-cache hits and the lookups they were counted against, in tokens. Optional. |
| `requests`, `errors` | Finished requests and those that ended in error. Optional. |
| `busy`, `waiting` | Requests being processed and waiting for a slot now. Gauges. |

Rules, all normative:

1. **Unknown is not zero.** A figure the engine does not report is *unknown* and MUST be shown and
   stored as unknown. A measured zero is a different value.
2. **Cumulative counters only.** Every total is derived from a cumulative `_total` counter or a
   histogram sum, never from a per-interval gauge, which some engines reset when read.
3. **A counter that goes backwards means the engine restarted.** That window is dropped: no rate,
   no history row. Counters of different engine families are not comparable, so a change of family
   between two reads drops the window as well.
4. **A rate with a zero denominator is unknown.** Prefill and decode speed use the time the engine
   reports for each phase, which engines count differently; generated tokens per second uses the
   wall clock between the two reads, stamped at the scrape and not before slower probes.
5. **A family that does not report requests or errors does not get them invented.** The node
   MAY count requests at its own link, labelled as such and since the process started (section 5).

## 3. Built-in families

The family is judged from the metric names in the scrape, never from a configured runtime name.

| Family | Detected by | Notes |
| --- | --- | --- |
| llama.cpp | `llamacpp:prompt_tokens_total` | `prompt = processed + cached`; reports no request or error counts. |
| vLLM | `vllm:generation_tokens_total` | Labelled series (finish reasons) are read label-aware. |
| SGLang | `sglang:generation_tokens_total` | Names are as documented, **not yet verified against a live engine**; absent figures stay unknown. |

## 4. Declared adapters (custom runtimes)

A runtime no built-in family claims is described in YAML, loaded with `--metrics-adapters <file>`
(never an environment variable). The file is strict: an unknown key, a missing required figure, a
malformed metric name, a duplicate adapter name or detection marker, or a built-in family name
used as an adapter name MUST fail the load. A failed load costs the custom runtime its figures,
not the node or its page.

```yaml
adapters:
  - name: Strata                       # 1 to 32 printable characters
    detect: strata_generated_tokens_total   # the metric that proves it is this engine
    prompt_tokens: strata_prompt_tokens_total        # required
    generated_tokens: strata_generated_tokens_total  # required
    processed_tokens: strata_prefill_tokens_total    # optional; absent = unknown
    prefill_seconds: strata_prefill_seconds_total
    decode_seconds: strata_decode_seconds_total
    cache_hit_tokens: strata_prefix_hit_tokens_total
    cache_query_tokens: strata_prefix_query_tokens_total
    requests: strata_requests_total
    errors: strata_request_errors_total
    running: strata_running_requests
    waiting: strata_waiting_requests
```

A metric name matches every series of that name and a labelled metric is the **sum over its
labels**, so `requests_total{status="ok"}` and `{status="error"}` read as one total. Cache fields
require `processed_tokens`. Built-in families are tried first, then adapters in file order.

## 5. Link request tally

Because llama.cpp counts no requests, the node's link, which sees every request its parent sends,
keeps a tally since process start: requests answered, requests failed, and the most recent failure
with its time. A failure counts when the engine answers a non-success status, refuses, or its HTTP
reply fails; a cancelled stream counts as neither. The text shown with a failure is the engine's
**error body for a status refusal only**; output the model had already streamed MUST NOT be kept
or shown.

## 6. Local history

A node MAY keep a display-only history of deltas in a SQLite file on its own disk (35 days,
hourly buckets). It is never reported upstream and is not authoritative for anything. A write MUST
NOT hold up a page request; a page that cannot reach its history in under a second says the
history is busy.

## 7. Conformance (owed)

Fixture scrapes per family (idle, busy, restarted, partial); an adapter file with each failure in
section 4; a counter reset; a family swap between reads; labelled series summed; a link failure
with and without a streamed body. Recorded `owed`; the reference implementation carries unit
tests for each.

## 8. Open items

1. Verify the SGLang names and the Strata adapter against live engines.
2. Probes send no local client token; an engine run with an API key shows no figures.
3. Whether the normalised sample should become an optional field of the node heartbeat (it is not
   one today and this document does not add it).
