# Scoped observability persistence, public profiles and capacity disclosure

Status: accepted for implementation by the operator on 2026-10-20; deployment is
conditional on the existing proof gates. This record extends D-001/D-002 only
within the boundaries below. All new runtime acceptance cases remain **owed**.

## Decision and operational basis

The operator requested persisted full telemetry and performance analytics,
public GPU profiles, explicit free GPU/CPU capacity, context-specific serving
offers, and inclusion of the already registered Nibbler in dynamic rebalancing.
The approved design/plan is the 2026-10-20 observability-performance draft in the
production Go gateway's `docs/superpowers/` tree. Approval covers implementation,
independent review, merge and deployment after qualification; it is not evidence
that a control works or that any hardware is qualified.

The prior specifications left two defects: an untyped `Capacity.requests` could
be interpreted as fixed serving slots, and a generic "free CPU" could be computed
from instantaneous idle percentage. Literal implementations would advertise
unsupported concurrent requests or CPU that a process cannot actually use. The
new typed read-only contract prohibits both interpretations.

Rust retains global normalization, warehouse, metric, accounting, recommendation,
capacity and admission authority. The existing conformant Go site gateway may
persist its own bounded, content-free edge observations and their local rollups
in its existing storage, with explicit source and coverage, and adapt authorized
Rust reads. This narrow D-001/spec58 amendment grants no second global warehouse
or domain-authority service. Edge TTFT and upstream wait are edge observations;
Go must not relabel them as node prefill/decode or recompute owner capacity.

New public GPU profiles use the existing `InferWeave/inferweave` Next.js
`apps/web` application under D-002. The existing Go embedded operator UI may
extend its existing analytics pages under the prior exception, with authorized
reads and existing access controls. No new Go public web product is authorized.

## Approved operational scope and remaining gates

The operator authorized the existing Zapp, Farm, Hive and Whiteale path and
Nibbler qualification for this work, subject to host authorization, deployment
substrate, scheduler authority and all existing safety gates. Full GPU telemetry
restoration begins with spec46 `observe` on qualifying real NVIDIA hardware;
it changes no placement policy. NVIDIA evidence cannot prove AMD support.

Nibbler's registration is hardware-only evidence. A Go root without the spec64
provisioner cannot turn that registration into assignments. Dynamic serving needs
the existing Rust owner and executor, exact profile/artifact qualification,
a real full authorization/admission request, watchdog, rollback and applicable
availability-floor proof. This record does not introduce Go dynamic provisioning
or a second rebalancer. Spec64's existing single-engine restriction remains;
read-only telemetry does not authorize a live swap.

## Contract and proof

`contracts/observability-capacity.json` freezes the vocabulary, policy defaults
and AC-OBS-01..09. `schemas/v1/resources/observability-capacity.json` freezes the
read-only shape. Specs 04/09/23 describe semantics. The new-family-only 90-day aggregate and 7-day
diagnostic retention, 5-minute maximum capacity validity and public cohort
thresholds of 30 requests / 5 principals are initial policy ceilings/defaults,
not measured throughput envelopes or universal privacy guarantees. A stricter
owner/tenant policy wins. Private principal identifiers never enter public
responses; counting distinct principals requires authorized internal evidence.
All hardware, runtime, privacy and production-rollout proof is **owed** until a
pinned test/evidence record demonstrates it. See `OPEN_GATES.md`.

## Retention scope boundary

The 90/7-day defaults apply only to newly introduced observability-family records
and their derived caches/exports, explicitly namespaced inside the existing
storage. Existing 730/365-day request/benchmark policies, legacy records and
shared backup lifetimes remain unchanged. No retroactive deletion is authorized.
Any existing-record/cache/backup retention change needs a separate reviewed
migration and deletion authorization; reusing a storage engine does not merge
retention namespaces.
