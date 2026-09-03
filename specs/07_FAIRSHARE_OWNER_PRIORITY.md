# 07 — FairShare, Owner Priority and Anti-Gaming

## Separation

Routing answers **where** eligible work can run. FairShare answers **which** eligible principal receives scarce service next.

## Principal hierarchy

`organization → team → user/service account → application → API key → session → agent → request`

Fairness is charged primarily to stable parent identities. Creating more API keys, sessions, agents, gateways or regions cannot manufacture new budget.

## Policy

Versioned effective policy can define:
- minimum demanded throughput/share;
- maximum throughput/share;
- weight;
- burst tokens/work;
- target wait;
- concurrency cap;
- model/region overrides;
- allowed workload classes;
- borrowing;
- owner reserve;
- effective/expiry time.

Unused reserved service is borrowable.

## Owner priority

Tentative invariant: the provider/owner can reclaim their own hardware. Remote/network work is explicitly `interruptible` or `non_interruptible`. New remote admissions stop first; interruptible work may be gracefully drained/preempted to restore owner reserve.

Owner priority must be observable and cannot be faked by an arbitrary public workload-class hint.

## Workload classes

`interactive | implementation | review | planning | batch | background | vision | image`

These are scheduling hints constrained by identity/policy, not independent entitlement pools unless configured.

## Algorithm

Use deficit/weighted fair scheduling with:
- guarantee deficit;
- current/historical wait credit;
- starvation prevention;
- SLA recovery;
- recent service penalty;
- burst penalty.

Provide simulation and shadow mode before activating new policy.

## Status code

A FairShare/user-level delay/rejection is `429`, not `503`. Do not reroute merely to evade a user's fairness policy.
