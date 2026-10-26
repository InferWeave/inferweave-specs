# ADR — InferWeave Bench authenticated users and Cognito federation

**Status:** Accepted for implementation; production activation remains gated.
**Date:** 2026-10-25
**Scope:** `inferweave-bench` authenticated web/control-plane surfaces.
**Feature IDs:** `IW-UI-001`, `IW-BENCH-002`, `IW-EVENT-001`.

## Decision

Use the existing Amazon Cognito User Pool as the single authentication authority.

- Local users register in the Cognito User Pool and verify their email there.
- Google is configured as a Cognito federated identity provider.
- The web client uses Cognito Managed Login with Authorization Code + PKCE.
- InferWeave verifies Cognito issuer, audience, signature, expiry and nonce before creating a local session.
- Stable identity is `(issuer, sub)`. Email is display/linking metadata, never the identity key.
- InferWeave owns application roles: `viewer`, `requester`, `reviewer`, `admin`.
- Cognito groups may provide an initial role claim, but role grants and revocations are persisted and audited by InferWeave.
- Account linking between local and Google identities requires an authenticated explicit confirmation; matching email alone never links accounts.
- Raw benchmark prompts, outputs, traces and artifacts require reviewer/admin authorization. Aggregate public benchmark data remains content-free.

## Registration and approval

New local or Google users receive the `viewer` role. A viewer may request access to benchmark work; only an admin may grant `requester`, `reviewer`, or `admin` roles. Benchmark-plan approval is separate from authentication and remains a complete-plan admin action.

## Session and API boundary

Next.js owns the browser authorization-code callback and keeps the resulting session in Secure, HttpOnly, SameSite cookies. Rust remains authoritative for protected control-plane authorization and must verify bearer/session-derived claims at its API boundary. Browser identity headers are never treated as grants.

## Non-goals

- No second local password database.
- No direct Google token acceptance by benchmark workers.
- No public exposure or production Cognito/Google configuration change from this implementation change.
- No claim that the security qualification gate is closed; live pool, redirect, cookie, role, audit and revocation proof remain required.

## Required proof

- OIDC state, nonce and PKCE mismatch tests.
- Issuer/audience/signature/expiry rejection tests.
- Local sign-up and email-confirmation error handling tests.
- Google federation callback tests using a fake OIDC issuer.
- Role escalation, account-linking and revoked-session tests.
- Protected raw-artifact read tests for viewer/requester/reviewer/admin.
- Browser smoke tests for login, logout, unauthorized, expired and role-denied states.

## References

- `specs/10_DASHBOARD_PORTAL.md`
- `specs/15_ASYNC_JOBS_ARTIFACTS.md`
- `specs/58_MODEL_INTELLIGENCE_UI_COHESION.md`
- `OPEN_GATES.md`
