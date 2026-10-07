# InferWeave Protocol v1 — security

Security in the protocol is about describing and carrying security-relevant state without
forcing one mechanism.

## Identity and privacy

- Public node/device identifiers are pseudonymous and rotatable where practical; they are never
  stable private node addresses (invariants 17/18).
- Stable internal identity and the public pseudonymous label are distinct values.

## Trust and provenance

Reported information carries origin and confidence (`direct`, `reported`, `measured`,
`verified`, `estimated`, `cached`, `operator_supplied`, `unknown`). Trust is never auto-promoted
by passing through a trusted gateway. Federated resources may advertise trust domain (`local`,
`trusted`, `partner`, `external`, `untrusted`); actual policy remains gateway-specific.

## Authentication

Authentication metadata is extensible and MUST NOT force one system. Potential mechanisms:
bearer token, mTLS, signed registration, service identity. Upstream credentials MUST NOT
automatically be forwarded downstream; each gateway authenticates independently to its peer.

## Data handling / privacy

Federated resources SHOULD optionally advertise `prompt_retention`, `response_retention`,
`logging`, `ephemeral_execution`, `training_usage`, `storage_location`, `trust_domain`, so
routing policy can prevent sensitive jobs from reaching unsuitable peers. This builds on
`specs/16_SECURITY_PRIVACY_TRUST.md` and invariant 6.

## Admin separation

Administrative operations are defined separately from public inference APIs; exact
authorization policy is implementation-specific. The gateway enforces organizational access
controls but must not mutate protocol semantics.
