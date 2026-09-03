# ADR-NNN — Title

**Status:** Proposed  
**Decision owner:**  
**Date:**  
**Authorizes:**  
**Relationship:**  

## Status vocabulary

A status states what the record authorizes, and nothing broader is implied:

- `Proposed` — authorizes nothing.
- `Accepted for design` — authorizes the design only. Name explicitly what it does **not**
  authorize: deployment, enrollment, spending, real value, production traffic.
- `Accepted for implementation` — authorizes building it, still not deploying it.
- `Accepted for production` — requires the corresponding gate in `OPEN_GATES.md` to be
  APPROVED in the same change.

## Relationship

State the exact relation to prior records, one of:

- `supersedes ADR-NNN` — replaces it entirely;
- `re-decides <invariant> of ADR-NNN` — a narrow, explicit amendment; every other invariant of
  that record is preserved unchanged;
- `discloses` — states an operational fact about a prior record without amending it.

A record that changes an earlier decision by implication is not acceptable. Say which
invariant, and say that the rest stand.

## Measured basis

Any figure this record relies on is measured by its author against the pinned commit and
reproduced here. Do not quote a number from another document without reproducing it.

## Context
What requirement/constraint forces a choice?

## Options
1.
2.
3.

## Decision
Chosen option.

## Consequences
Positive, negative, operational and migration effects.

## Requirements affected
- IW-...
- AC-...

## Rollback/revisit trigger
What evidence would justify changing this decision?
