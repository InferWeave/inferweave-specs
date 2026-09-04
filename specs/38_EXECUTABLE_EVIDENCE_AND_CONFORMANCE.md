# 38 — Executable Evidence, Conformance Vectors and Machine-Checked Registries

## Goal

A specification that only asserts intent is indistinguishable from an untested claim. This
document defines how these specifications are made enforceable rather than aspirational.

It governs how contracts are expressed, how conformance is proven, and how a guard earns the
right to be trusted.

## Registries are executable data, not prose

Where a specification defines a table that implementations must honour — a decision table, an
entity contract, a threat/boundary catalogue, an error vocabulary — that table is expressed
three times and reconciled by test:

1. **frozen data** in the implementation, the authority at runtime;
2. **a published document**, the authority for a reader;
3. **conformance tests** that fail when the two disagree, cell by cell.

Prose alone is unenforceable: nothing fails when an implementation drifts from it. A table
that exists only in a document will diverge, and the divergence is discovered by an operator
rather than by CI.

A new value in a shared vocabulary — an outcome, a reason code, a lifecycle state — requires a
decision record, because it changes a vocabulary every consumer shares.

## Guards must be able to fail

Every structural guard is additionally executed against a deliberately broken copy of the data
it guards. A guard that passes against known-bad input is itself a test failure.

This is not redundancy. A guard that silently stops checking — because a field was renamed, a
path moved, or an exception is being swallowed — reports success indefinitely and is
indistinguishable from a guard that works.

## Coverage measures coverage, not truth

A mechanical scanner reports which code a test suite reaches. It cannot report whether the
reachable behaviour is correct, and it cannot see a data state no test constructs.

**Deleting a guard on the strength of a coverage signal is therefore forbidden.** A guard may
be removed only when the condition it detects has been made unreachable at the point of
writing, and that unreachability is itself asserted by test.

## Proof status is explicit

Every required test carries one of two statuses, and they are never conflated:

- **`proven`** — a test exists today, runs in CI, and fails if the control is removed;
- **`owed`** — the control is specified and the test does not exist yet, naming the task that
  owes it.

A registry that reports `owed` work as `proven` asserts proof it does not have, which is worse
than recording no proof at all: it stops anyone looking.

## Conformance vectors

Every protocol-level contract publishes hash-pinned conformance vectors: input, expected
output, and the exact contract version they bind to. A manifest records the digest of every
vector file, and the manifest digest is what an implementation pins.

Vectors are the only practical way a contract stays identical across two languages. Rust and
TypeScript agreeing with the same document is not evidence; both agreeing with the same vector
is.

Vectors are required for at least: the message envelope, identity, discovery results, the
error envelope, receipt chains, capability advertisement and the deployment context ceiling.

### Hostile vectors

Every vector set ships adversarial cases beside valid ones — malformed, replayed, truncated,
reordered, over-large, wrongly signed, and boundary-value inputs — each with its expected
refusal.

A vector set containing only valid inputs proves an implementation can succeed. It proves
nothing about how it fails, which is the half that matters under attack.

## Integrity checks are whole-object, not page-shaped

Where a specification requires an ordered, gapless record — a journal, a receipt chain, a
sequence of events — verification proves the property over the entire object, not over the
page currently in hand.

A gap below a reader's cursor is invisible to a page-shaped check while the stream replays as
complete. An interrupted operation can then be closed on evidence read out of a record nobody
verified.

Where the proof relies on a property of the storage engine — that a column is integral, that a
constraint is enforced, that a uniqueness guarantee holds — that premise is asserted against
the live engine by attempting the write that would violate it. A declared type is not always an
enforced type, and a proof resting on an unenforced premise is arithmetic with a false
conclusion.

## Relationship to other specifications

This document constrains how every other specification is proven. It does not define what any
of them require. Where another specification defines a table, that table is subject to the
rules above.
