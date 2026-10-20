# Retain bounded failure evidence beside request rollups

Status: additive contract decision within the accepted 2026-10-20 observability
scope; runtime implementation and publication proof remain owed. Independent
review is required before integration.

The existing request rollup retains status totals and timing/token distributions
for 90 days, but failure reasons, layers and phases exist only in diagnostics
with a 7-day lifetime. Implementing that specification literally loses the
ability to explain retained failure counts after diagnostic pruning. This is a
specification gap, not evidence of a measured production incident.

Add `iw.observability.failure-rollup/1` as a separate bounded companion to the
unchanged event and rollup v1 schemas. Bind it to the entire exact canonical
parent fingerprint and identity/revision/sealed state. Preserve complete closed
reason/layer/phase maps for the four non-success statuses and a bounded
existing-timeout-reason by existing-outcome-phase table so queue-timeout counts
are correlated observations. Keep valid `none` phase/layer values and explicit
unknowns. The parent remains the source of dimensions, denominators and coverage;
missing companions mean unavailable. Spec23 defines encoding and conservation.

Reject expanding frozen v1 objects: their additionalProperties=false contracts
must remain compatible. Reject retaining raw diagnostics for 90 days or deriving
historic failures from whatever 7-day traces survive. Reject a full unconstrained
reason/layer/phase cube and free-form strings: bounded marginals plus the explicit
timeout-phase table answer the required question with existing event codes.

Parent and companion share transactional replacement/sealing/pruning and the
existing persisted late-ingest fence at all three resolutions. Keep aggregate
and dedupe evidence through the parent lifetime. This does not change legacy
730/365-day retention, shared backups, Rust global normalization authority, Go
own-edge scope, or publication authority. Public per-cell evidence and suppression
remain separate gates; parent cohort eligibility does not authorize subcells.

Feature/task mapping remains IW-OBS-001/IW-TEL-001/IW-BENCH-002, P1-T20/P2-T03.
AC-REQOBS-09 and OPEN_GATES distinguish executable offline contract proof from
owed runtime transaction, restart, retention and public-privacy evidence.
