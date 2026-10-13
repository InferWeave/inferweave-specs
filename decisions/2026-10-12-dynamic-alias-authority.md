# Dynamic alias authority and existing site operator UI

Date: 2026-10-12. Status: adopted by operator implementation handoff, independent implementation
review still required. Amends D-002 narrowly; preserves D-001/D-005 and spec 00.

The operator supplied an end-to-end alias handoff for the existing Rust engine and Go production
site gateway. Source audit (`docs/alias-implementation-gap-matrix.md`) found level-1 alias objects,
Rust logical routes, Go legacy selection, and no authoritative revisioned alias management.
D-002's prior exception covered only runtime-family views, so applying it literally would exclude
the requested alias operator screens. This is an explicit architecture amendment, not an assertion
that the old text already permitted them.

Permit only the existing Go embedded operator UI to consume Rust alias CRUD/preview/history,
routing/federation evidence and model/GPU crosslinks. All domain policy, persistence, selection,
admission and scheduler/backend interactions remain Rust-owned. Existing Go analytics metadata
cannot become policy storage. A read cache carries source age/revision and is never a router.
Direct-first transport remains normal; compatibility relay does not become gateway scheduling.

Negotiate dynamic_aliases level 2 rather than overwrite level 1. Keep protocol 1.1.0's current
unreleased additive contract, explicit HTTP negotiation and strict unknown-policy rejection.
Instance-level evidence prevents features merged across workers from becoming a false verified
profile. Native authentication and trusted edge identity must be demonstrated before activation.

Rejected: independent Go alias engine (two authorities); wholesale Go rewrite (unnecessary scope);
level-1 reinterpretation (mixed-version policy weakening); hardcoded checkpoint launch aliases
(names express intent, operators publish policy against observed capacity).

Proof: contract guard and schema fixtures are artifact evidence only. Runtime/security/UI/load and
rollout acceptance are owed in OPEN_GATES and contracts/dynamic-alias-acceptance.json.
