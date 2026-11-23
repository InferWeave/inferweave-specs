# Benchmark publication review — 2026-11-22 Pacific

Scope: existing IW-BENCH-002 / IW-REC-001 / IW-UI-001 and spec58
MI-01/03/04/06. This is operational feedback and acceptance clarification, not a
new feature, qualification decision or production approval.

## Incident and specification gap

The operator's public-site audit found GPU counts inconsistent with placement
labels; task pages omitted results despite family-level coverage; repeated model
labels obscured distinct task observations; capability summaries used a different
population from measured suite coverage; exact ties had inconsistent ranks;
methodology omitted reproducibility inputs; and phone comparison views hid the
score and placement initially. The audit did not establish a grading arithmetic
error or prove that different summary populations meant records were lost.

A subsequent isolated read-only export reproduced an additional publication
failure: the installed publisher rejected `model` fields in speed-group,
speed-row and placement datasets because automatically derived model identifiers
contained operational parenthetical annotations. Removing the recognized private
host/runtime suffix left another parenthesis pair, rejected by both publisher and
browser. Those labels did not match explicit suite/run display-label overrides.
No private labels, rows, source paths, credentials or launch arguments are
reproduced here. The diagnostic used the pinned installed image with networking
disabled, read-only source mounts and tmpfs export; it did not invoke publication.

The earlier spec required exact provenance, explicit unknown values, privacy and
responsive comparisons, but did not spell out publication-versus-measurement
state, row identity despite label collisions, tie semantics, or a consistent
producer/publisher/browser label projection. Following those omissions could
repeat this incident while claiming to satisfy generic provenance text. The
added spec58 section makes these existing acceptance expectations explicit;
it does not authorize broader redaction guesses or exposure of private evidence.

## Evidence boundaries

The source audit report is retained in the operator's local review artifact
bundle (`inferweave-bench-review-2026-11-22/REPORT.txt`). Its figures are not
copied here: live observations and corrected exports are different snapshots.
A corrected-export measurement and reproduction recipe must accompany this
record before any numeric completeness or metadata claim is made.

**Owed:** independently reviewed corrected-export reconciliation, required CI,
production deployment and verification of fresh public publication, and broader
historical metadata acquisition. Spec validation establishes document consistency
only. Controlled equivalence, all-results publication and global qualification
remain unproven; no existing gate closes with this document.

## Corrected-export measurement (local candidate only)

Reproduced directly from the corrected, verified read-only source-store export,
not from the audit report. The
[content-free summary](corrected-export-summary.json) pins every exported file by
SHA-256; its generator prints only dataset counts, family/count categories and
hashes, never model labels or private records. Reproduce against the same retained
export directory with:

```sh
python3 evidence/benchmark-publication-review-2026-11-22/reproduce.py /path/to/verified-data
```

The measured candidate has 11 JSON files (including its manifest), 385
configuration observations, 2,606 flat task-result rows, and 465 speed rows.
Flat task-result rows comprise coding 322, logic 368, science 1,104, MCP 195,
review 247 and SQL 370. Configuration profiles contain 3,783 task rows across
profiles; these are a different population from flat task rows and must not be
added together or treated as missing observations.

Speed rows report count unavailable for 393 observations, one card for 36 and
two cards for 36. Configuration observations report count unavailable for 354,
one for 6 and two for 25. These nullable counts preserve historical uncertainty;
they are not a claim that every previously missing value was reconstructed.
There are 153 public prompt descriptions, independently of the measured task-row
population.

The sibling verification receipt reports status `verified`, no dropped datasets
and the same dataset hashes (the verified projection has its own manifest bytes). This proves only the bounded local export/verification
result. A subsequent read-only pinned-container replay used the production deny policy;
the retained [content-free receipt](production-policy-verification.json) records
11 verified files and zero configured deny-substring rules. Its manifest hash
matches the refreshed verified projection. This is local policy replay, not
production publication. No source-store record was changed, no export was deployed,
and neither source-wide completeness nor privacy/qualification gates are
certified by these counts. Safe task result projection remains distinct from raw
source attempts, excluded observations and private evidence.

Candidate provenance measured for this export:

- implementation base commit: `6895b27bbdc1f06cec6e1ed7ab21702270742bd0`;
- corrected `inferweave` binary SHA-256:
  `e97d66a40a5915b37ccf740c49760a061deec0e33b2f96c8a1a6c3c15a405932`;
- SHA-256 of the binary Git diff for `crates/iw-bench/src/dashboard.rs` and
  `crates/iw-bench/src/configuration_summary.rs` against that base:
  `d14a039c1e3edbaa0e72c05d9ce64e8db023cb0c498c66b588a65c695442dab4`.

These pins identify a local uncommitted correction candidate, not a released
implementation revision. They exclude unrelated browser changes. The bounded
original failure reproduced image
`sha256:ef7f87986f204f293091dc196c797a978cf204d9f43bae43ed85b9c82fa291b0`;
its verifier and the browser both refused leftover parentheses in model labels.

Independent review also identified a malformed-model edge case: returning a
null public model field would still fail the aggregate shape contract. The
correction omits that unsafe source row with a fixed content-free reason rather
than emitting a malformed public row or exposing the original identifier. The updated `crates/iw-bench/src/configuration_summary.rs` SHA-256 is
`c8e527aa604f3ec48f9f0d85abf5c26fe055200ef1c7845b93469046f48f2ac3`.
The refreshed corrected export retains the same ten dataset byte hashes; only
manifest bytes change. This does not erase intentionally excluded/private source
records or turn historical missing metadata into a measurement.
