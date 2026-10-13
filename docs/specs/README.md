# Operational specification bundles

Numbered specifications under [`/specs`](../../specs) are canonical and
versioned. This directory holds **operational bundles**: a specification written
against a live fleet and a live client, delivered together with the work breakdown
and the acceptance criteria that made it land. They do not replace the numbered
documents; they are the detail behind clauses that were already true and were not
implemented.

## dynamic-context-capabilities

Model context capability, request-scoped admission, and the Pi client contract.

It is here because the fleet and its client disagreed with `specs/04` and
`specs/05` in a specific, measurable way:

- `05` step 5 already requires filtering **context feasibility against each
  candidate deployment's hard `max_context_tokens` ceiling**. Admission did not do
  this: a request's reservation was a share of the model's maximum window, so a
  4K prompt and a 250K prompt cost the same, and a request could be placed where
  it could not be served.
- `04` already states **"Seat count is descriptive, not admission capacity."**
  The implementation used a seat as the capacity unit anyway, held for the life of
  a session, which is how idle sessions came to look like busy callers and
  `caller_concurrency` came to be refused at low real concurrency.
- `02` already requires OpenAI compatibility with extension. The bundle specifies
  the extension concretely: `context_window`, `max_model_len`, `max_output_tokens`
  and an `inferweave` capability document, with `ETag` = capability generation.

Read it in this order: `00-overview-and-architecture.md`, then
`12-acceptance-criteria.md`, then the subsystem documents referenced by
`10-cross-repo-work-breakdown.md`.

Where the two disagree: the numbered specification governs the **contract**;
this bundle governs the **mechanism**, and its `12-acceptance-criteria.md` is the
thing a reviewer should be able to run.

## model-intelligence-kit

[`MASTER_SPEC.md`](model-intelligence-kit/MASTER_SPEC.md) preserves the operator's
v1.0 implementation kit unchanged. Numbered spec 58 normalizes its repository,
existing embedded UI, authorization and Rust ownership boundaries. Acceptance
remains owed until implementation and runtime evidence are recorded.
