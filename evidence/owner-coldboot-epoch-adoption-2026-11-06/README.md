# Owner cold-boot catch-up and epoch adoption — 2026-11-06

Feature/task scope: `IW-WATCH-001` / `P1-T20A` (complete fault evidence),
`IW-WATCH-003` / `P3-T18A` (authorized operator recovery). Spec 28's external
inspection boundary remains read-only. No new feature, task or dependency edge
is introduced, and no capability or production gate is marked proven.

## Operational input and specification defect

The owner supplied a private post-access snapshot and a read-only recovery
proposal for the Beast external W3A8 deployment after a confirmed host reboot.
They report an unchanged engine container/image and serving inputs but a new
start time/native process; the guard refused identity drift, remained
quarantined/unarmed, and its registrar stayed stopped. Native health was
available, but fresh cold-boot context/concurrency/full-path proof was absent.
The retained kernel checkpoint belonged to the previous boot; the pending
current-boot journal exceeded the pinned monitor's single-read bound. Native
logs retained unread bytes that had not been qualified.

These are supplied incident observations, not measurements reproduced by this
specification author. No raw snapshot, process/container identifier, checkpoint
contents, credentials, prompt/response content or private host address is
published here. No figure from the private proposal is used as a measured proof.
The retained public profile is a requirement to preserve, not new performance
or qualification evidence.

The old specification required requalification and fail-closed monitoring but
did not define supported cross-boot catch-up and coherent multi-file checkpoint
adoption. A literal implementation could safely quarantine forever, or attempt
an unsafe cursor deletion/tail reset to bypass its bounded monitor. Spec 36 now
requires complete retained-history replay and transactional owner epoch
adoption; it does not weaken the earlier same-generation false-positive replay
rule. This is a supported operation to implement, not an existing guard API.

## Authorized design and proof boundary

The owner approved a recovery helper and this operational-spec correction while
retaining the existing guard executable, unchanged profile, and existing safety
gates. Catch-up must prove full retained-boot continuity and, when discounting
foreign OOM, protected historical engine/registrar capture/anchor provenance.
Root-owned JSON claims alone cannot supply it; a live producer cannot backdate
proof. Explicit `whole_machine_conservative` replay can instead use complete
candidate-free history without historical scopes because it discounts no OOM or
GPU-fault candidate. Its mode/coverage receipt proves neither historical
attribution nor absence of every machine fault. Conservative/scoped agreement
under comparable budgets and rejection of all candidate forms remain owed.
Carry OOM state only within a boot, scan every
pending native byte with lineage/lookbehind, bind fixed watermarks, and leave
subsequent appends pending for a gap-free guard handoff. Any ambiguity, loss,
fault or bound exhaustion leaves quarantine in place.

Only fresh local qualification can precede protected generation/checkpoint
publication. A durable manifest and quarantine-last transaction must contain
crashes and mixed state; strict startup cannot bootstrap an absent/stopped
engine. Fresh authenticated route/context/concurrent-session proof is required
before ordinary traffic resumes. No old ready proof or interrupted request may
be reused as new qualification or replayed work.

**All new implementation and operational proofs are owed.** The required tests
are registered in the existing task cards, task graph and canonical sequence;
none has been marked proven by this documentation. Independent implementation
review, removal-sensitive failure tests, applicable CI and explicit owner
operational qualification remain required. CI capacity intentionally disabled by
the owner is not authorization to bypass checks or change infrastructure.
No implementation revision, test success, service start, state adoption,
quarantine acknowledgement or production recovery is asserted in this record.

## Assurance correction before adoption

The merged recovery text left candidate families and the pre-ingest loss boundary
underspecified. A literal implementation could reuse narrow resident markers or
mistake contiguous retained global journal sequence numbers for complete kernel
history. Spec 36 now requires broader global-only candidate recognition,
boot-local bounded cross-record state, all-transport loss message-ID inspection,
trusted kernel/driver loss text checks and a receipt bounded by declared collector
assumptions. Current protected collector configuration is required; historical
continuity remains an assumption. This correction supplies no runtime evidence
and opens no gate. All new source/runtime and removal-sensitive proofs are owed.
