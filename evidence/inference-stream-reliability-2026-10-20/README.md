# Inference stream reliability: local site-gateway evidence, 2026-10-20

## Scope and source pin

This record covers the Go site-gateway, admission and existing console portions
of `AC-STREAM-06`, `AC-STREAM-07` and `AC-STREAM-08` in
[`contracts/inference-stream-reliability.json`](../../contracts/inference-stream-reliability.json).
The feature/task mapping is `IW-OBS-001` / `P1-T20` and `IW-OBS-002` / `P1-T12A`.
The existing Go site-gateway exception is D-001; this evidence does not establish
Rust serving-gateway conformance.

Implementation repository: `metabolomics-us/inferweave-gateway`.
Pinned commit: **`566a93a4f8234543cf3e6788b192d311039e0e6d`**.
All implementation and test paths below refer to that commit, not this specs
repository, except the later real-database verification at
**`a29e0b9fc513f9a1e798727d0d25d3db30e69df7`**. That follow-up changes only one
historical-report test fixture to match the new request-correlation scan column;
production source at `a29e0b9` remains identical to `566a93a`. Both revisions were
checked against the local Git history. A narrowly scoped envelope-completion
follow-up is pinned separately at
**`179f20c1d647fa5dde0480a3b4bb02d23eb5957e`**; its local verification is recorded
below. Earlier browser, database and binary results remain attributed to their
original revisions, not silently extended to that new product revision.

**Full acceptance status: owed for AC-STREAM-06, AC-STREAM-07 and AC-STREAM-08.**
Named local controls below are proven by their listed tests; they are not a claim
that the complete fleet acceptance scenario has been exercised. Contract gates
remain owed. Rust implementation proof is not asserted here. No production
recovery, rollout, canary or comparable-traffic post-rollout result is asserted.
Disposable PostgreSQL integration is proven below. Production database behavior
and production-serving rollout remain outside that local proof.

## Reproduced Go evidence

At the pinned commit, the following command was executed locally, with no
production endpoints or credentials:

```bash
umask 077
go test ./cmd/gateway ./internal/proxy -run 'TestReliability|TestTimeoutEvidence|TestStreamTimeout|TestDiagnosticStreamFailureAttribution|TestModelDiagnosticRequestsOwnerScopeAndPrivacy|TestInferenceDiagnosticsSurviveCommittedHTTPLinkAbort|TestTrafficSearchFindsDiagnosticAndRequestIDs|TestDiagnosticReportIncludesBothCorrelationIDs|TestAdmissionDiagnostics|TestAdmissionDefaultIdentityGroupingEnforced|TestAdmissionSharedPrincipalDefaultAgentBudget|TestAdmissionAggregateUsesAuthenticationAndOmitsIdentityMaps|TestAdmissionIdentityUserScope|TestAdmissionIdentityPersonalKeysShareUserBudget|TestProxyReportsMidResponseErrors' -count=1
```

Observed output:

```text
ok github.com/metabolomics-us/inferweave-gateway/cmd/gateway 0.223s
ok github.com/metabolomics-us/inferweave-gateway/internal/proxy 0.029s
```

An additional fresh run covered the singularly named finite-label test:

```bash
go test ./cmd/gateway -run '^TestAdmissionDiagnosticLabelsBoundedAndDetached$' -count=1
```

```text
ok github.com/metabolomics-us/inferweave-gateway/cmd/gateway 0.009s
```

The durations are local test-run times, not inference latency measurements.
The restrictive umask avoids an unrelated provision-journal fixture rejecting a
group-writable temporary directory. `-count=1` forces a fresh test run.

### AC-STREAM-06: authenticated, bounded and honest diagnostics

Local control status: **proven** for the listed Go behavior.
Full acceptance status: **owed**, including the serving gateway and deployed
cross-hop behavior.

| Verified control | Implementation | Executed regression tests |
| --- | --- | --- |
| Operator authentication on both reliability routes; ordinary browser users refused; effective local execution/link limits exposed separately from unknown downstream settings | `cmd/gateway/reliability.go`, `cmd/gateway/main.go`, existing `cmd/gateway/security.go` | `TestReliabilityEndpoint`, `TestReliabilityOperatorBoundaryAndEffectiveLimits` |
| Default 15-minute window, validated 1-second–24-hour bounds, model filtering, bounded group/sample counts, eviction/reset/coverage semantics and sanitized samples | `cmd/gateway/reliability.go`, existing bounded store in `cmd/gateway/traffic.go` | `TestReliabilityEndpoint`, `TestReliabilityWindowAndCardinality` |
| Complete bounded SSE events preserve only allowlisted timeout codes and optional bounded numeric evidence; arbitrary response text is not promoted to a failure label | `cmd/gateway/model_diagnostics_capture.go`, `cmd/gateway/telemetry.go` | `TestStreamTimeoutFailureCode`, `TestTimeoutEvidenceIsBoundedAndOptional`, `TestDiagnosticStreamFailureAttribution` |
| Actual upstream read failures are distinguishable from an unproven downstream cause; committed HTTP-link aborts still abort while retaining failure accounting, worker and correlation metadata | `internal/proxy/traffic.go`, `internal/proxy/link_http.go`, `internal/proxy/proxy.go`, `cmd/gateway/main.go` | `TestProxyReportsMidResponseErrors`, `TestInferenceDiagnosticsSurviveCommittedHTTPLinkAbort` |
| Admission diagnostics distinguish current blocking occupancy from retained reason/scope counters; source labels are finite and snapshots detached; aggregate authentication does not disclose identity maps | `cmd/gateway/admission_diagnostics.go`, `cmd/gateway/admission_status.go`, `cmd/gateway/admission.go`, `cmd/gateway/admission_queue.go`, `cmd/gateway/admission_types.go` | `TestAdmissionDiagnosticsRetainsTerminalBlockingScope`, `TestAdmissionDiagnosticsMetadataSourcesAndBlockingNow`, `TestAdmissionDiagnosticsSaturationWithoutWaitingRequests`, `TestAdmissionDiagnosticsStatusPrivacy`, `TestAdmissionDiagnosticLabelsBoundedAndDetached`, `TestAdmissionAggregateUsesAuthenticationAndOmitsIdentityMaps` |

The reliability endpoint's `coverage.complete` concerns its local recorded
attempt ring only. It is not a fleet-completeness assertion. `admission` contains
current/cumulative process state, explicitly separate from the historical
request window. Numeric timeout evidence is retained in bounded memory/JSON
telemetry; this commit does not add those numeric fields to PostgreSQL.

### AC-STREAM-07: authenticated parent isolation and default subdivisions

Local control status: **proven** for fixture-based admission enforcement.
Full acceptance status: **owed** for the complete deployed/federated scenario.

Implementation: `cmd/gateway/admission_identity.go`,
`cmd/gateway/admission.go`, `cmd/gateway/admission_queue.go`,
`cmd/gateway/admission_diagnostics.go` and existing admission accounting.

Executed tests:

- `TestAdmissionIdentityUserScope`: subdivision scope derives from the
  authenticated parent.
- `TestAdmissionIdentityPersonalKeysShareUserBudget`: personal-key fan-out does
  not mint additional parent budget.
- `TestAdmissionDefaultIdentityGroupingEnforced`: default subdivision grouping
  remains enforced while distinct authenticated users retain separate scopes.
- `TestAdmissionSharedPrincipalDefaultAgentBudget`: a shared credential retains
  its shared default budget despite spoofed user metadata.
- `TestAdmissionDiagnosticsMetadataSourcesAndBlockingNow`: diagnostics identify
  missing versus explicit metadata and current blocking scopes.

The implementation deliberately preserves safe shared/default grouping. It does
not assign synthetic per-request identities or increase the incident's
concurrency policy to conceal queue pressure.

### AC-STREAM-08: diagnostic IDs versus transport correlation IDs

Local Go control status: **proven** for API/export/search and simulated transport
failure accounting. Full acceptance status: **owed** for an actual deployed
request traced through the recent-error UI and downstream logs.

| Verified control | Implementation | Executed regression tests |
| --- | --- | --- |
| Diagnostic request rows expose `request_id` separately from `diagnostic_id`, retaining owner/operator access filtering | `cmd/gateway/model_diagnostics_api.go` | `TestModelDiagnosticRequestsOwnerScopeAndPrivacy` |
| Operator report labels both identifiers | `cmd/gateway/request_content_api.go` | `TestDiagnosticReportIncludesBothCorrelationIDs` |
| Live and durable Traffic search include both identifiers | `cmd/gateway/traffic.go`, `cmd/gateway/traffic_history.go` | `TestTrafficSearchFindsDiagnosticAndRequestIDs` (live matching and SQL predicate assertion; not a live database execution) |
| A committed HTTP-link failure retains a distinct capture ID and supplied transport ID alongside the worker and cause | `cmd/gateway/main.go`, `internal/proxy/link_http.go` | `TestInferenceDiagnosticsSurviveCommittedHTTPLinkAbort` |

Console implementation: `web/src/console/modelDetailInsights.ts`,
`web/src/console/model_diagnostics.ts`, `web/src/console/traffic.ts` and the
tracked embedded console bundle. Relevant browser regression programs are
`web/tools/attention-diagnosis-check.mjs` and `web/tools/traffic-check.mjs`.
The former asserts distinct ID labels, explicit missing historical IDs, plain
text rendering of upstream values, HTTP-200-after-headers explanation, and an
operator-only statistics link that does not issue automatic private queries.
The latter checks Traffic's ID disclosure and diagnostics controls.

Browser proof status: **proven for local fixtures**. This evidence author
reproduced all three browser programs at `a29e0b9` (unchanged browser source from
`566a93a`). From the implementation repository's `web/` directory:

```bash
export PLAYWRIGHT_MODULE=/home/wohlgemuth/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs
node tools/attention-diagnosis-check.mjs
node tools/traffic-check.mjs
node tools/model-diagnostics-check.mjs
```

`CHROME_PATH` was unset; the programs used `/usr/bin/google-chrome`. Each program
bundled the source into a temporary directory and used local fixtures. All three
exited zero and emitted their `PASS` summaries, respectively:

- `PASS model diagnosis`: attention/drilldown, history/current-state distinction,
  failure explanations, retained state, and 320px reflow.
- `PASS: Traffic filters, lazy private headers, Markdown copy, retained-data labels,
  keyboard disclosure, flat controls, and mobile reflow`.
- `PASS: response axes, 4h default, keyboard and table bin drilldowns, exact
  interval/model/outcome bookmarks, and mobile Traffic`.

The first program includes the separately inspected assertions for both IDs,
missing historical IDs and operator-only reliability links described above.
These passing fixture runs do not prove production authentication or actual
Hive log correlation.

## Effective timeout evidence follow-up: 179f20c

The finalized serving error envelope distinguishes the base idle setting from
the effective bound used during prefill. Product follow-up commit
**`179f20c1d647fa5dde0480a3b4bb02d23eb5957e`** extends
`cmd/gateway/model_diagnostics_capture.go` to retain optional
`effective_idle_timeout_ms`, `elapsed_ms` and `phase` alongside the existing
base idle, silence and request timeout values. It changes only that capture
implementation, `cmd/gateway/reliability_test.go` and the operation documentation.

The phase is limited to `prefill` or `generation`; absence remains absent. Every
reported duration must be an integer from zero through seven days in
milliseconds. Malformed optional fields discard timeout evidence while retaining
the safe failure code. Arbitrary error text and backend IDs are not retained in
the evidence object. These fields remain downstream reports, not independently
measured local timings, and are not added to the SQL schema.

Local control status: **proven** for this extension of AC-STREAM-06. Full
acceptance status remains **owed**. The new regressions were run before the
implementation and failed because the effective bound, elapsed time and phase
were missing and malformed newly introduced fields were ignored. After the fix:

- `TestTimeoutEvidenceRetainsEffectiveBoundAndPhase` passes for both phases,
  preserves the complete safe envelope through a reliability sample, and proves
  that unallowlisted backend IDs/error text are absent.
- `TestTimeoutEvidenceRejectsInvalidEffectiveFields` rejects nonnumeric,
  fractional, negative and oversized timing values and arbitrary/non-string
  phases, while checking safe-code preservation and absent historical fields.

This author ran:

```bash
go test ./cmd/gateway -run 'TestTimeoutEvidence|TestReliability|TestDiagnosticStreamFailureAttribution|TestInferenceDiagnosticsSurviveCommittedHTTPLinkAbort|TestStreamTimeoutFailureCode' -count=1
go vet ./cmd/gateway
go build -o /tmp/iw-console-timeout-evidence-check ./cmd/gateway
git diff --check
```

Observed targeted-test output:

```text
ok github.com/metabolomics-us/inferweave-gateway/cmd/gateway 0.104s
```

Vet, build and diff checks exited zero. The earlier `566a93a` binary smoke
results below establish only the earlier core behavior; they do **not** verify
this new envelope extension. A rebuilt artifact and any associated new binary
smoke proof must identify their own revision and digest.

## Additional leader/agent verification

### Real disposable PostgreSQL: proven local integration

The admission verification agent ran PostgreSQL **16.15**
(`16.15-1.pgdg24.04+2`) against the fixture-only follow-up revision
`a29e0b9fc513f9a1e798727d0d25d3db30e69df7`. This evidence author inspected
`/tmp/iw-postgres-verification.msp97485/standard.log`,
`both-id-overlay.log`, `overlay.json` and the overlay source diff. This section
attributes execution to that agent rather than claiming a second database run.

The verifier created two private temporary directories, each with an `initdb`
cluster and a private Unix socket. PostgreSQL listened on **no TCP interface**:

```bash
/usr/lib/postgresql/16/bin/initdb -D "$cluster/data" -U iw_history_test -A trust --no-locale
/usr/lib/postgresql/16/bin/pg_ctl -D "$cluster/data" -l "$cluster/postgres.log" \
  -o "-p 55439 -k $cluster -c listen_addresses='' -c unix_socket_permissions=0700" -w start
```

The content fixture used the equivalent separate cluster with user
`iw_content_test` and port 55441. `IW_HISTORY_TEST_SOCKET` and
`IW_CONTENT_TEST_SOCKET` selected these disposable sockets. Test commands were:

```bash
go test ./cmd/gateway -run 'Test(ModelDiagnostic|ModelQueue|History|RequestContent)' -count=1 -v
go test -overlay /tmp/iw-postgres-verification.msp97485/overlay.json \
  ./cmd/gateway -run '^TestModelDiagnosticPostgresIntegration$' -count=1 -v
```

Observed log results: the standard selection passed **35 top-level tests**, with
**zero skips**, in **0.471s**. Its actual database cases were
`TestModelDiagnosticPostgresIntegration`, `TestModelQueuePostgresIntegration`,
`TestHistoryPostgresIntegration`, `TestRequestContentPostgresIntegration`, and
`TestRequestContentHistoricalReportPostgresIntegration`. The overlay run passed
`TestModelDiagnosticPostgresIntegration` in **0.059s**.

The overlay changed test fixtures only: it seeded distinct `request_id` values
`corr-1` through `corr-7`, tested diagnostic-ID and transport-ID searches for own
and foreign owners, operator access and foreign-gateway exclusion, and asserted
that returned rows scanned the actual nonempty PostgreSQL `request_id`. The
production implementation was not overlaid. This closes the local SQL-execution
gap in AC-STREAM-08; it does not prove production database access or availability.

The setup/cleanup driver was `/tmp/iw-admission-native-postgres-verify.py`.
It stopped its clusters with `pg_ctl -m fast -w stop` and removed only the
private directories it created. No production DSN or credential was used.

### Full Go build gates and isolated real-binary smoke

The leader reported fresh success for:

```bash
umask 077
make fmt-check vet test build
```

All Go packages passed; reported package durations included `cmd/gateway`
**53.488s** and `internal/proxy` **11.467s**. These are test durations, not service
performance. This is leader-verified evidence, separate from the focused test
execution reproduced by this document's author above.

The leader also ran the real Go binary locally and on **Zapp** in temporary,
loopback-only processes with generated test credentials and seeded synthetic
telemetry. This is **proven isolated binary smoke**, not a production-serving
canary or deployment. It neither read the production configuration/store nor
replaced the running gateway.

- Binary built from `566a93a`; SHA-256:
  `acbb96f2b2d5e78416eb86b8316a277fd5113bf8d8e57920ca62420bab40252e`.
- Local driver: `/tmp/iw-stream-reliability-566a93a/go-smoke.py`; SHA-256:
  `161d74fe1728a212788f07338da3517b4ebea3a43b5fc66a6d49524a8c86fbc9`.
- Local binary: `/tmp/iw-stream-reliability-566a93a/gateway`.
- Zapp artifacts: `/tmp/iw-reliability-canary-566a93a.jM9KqK/`, containing that
  driver and binary. This author checked the local digests and driver; the
  remote execution result is attributed to the leader.

Invocation: `python3 go-smoke.py ./gateway` from the relevant artifact directory.
The script removes inherited `IW_*` settings, generates temporary credentials,
binds `127.0.0.1` on an ephemeral port and seeds one synthetic failed attempt.
It checks health, operator rejection/acceptance, telemetry replay with both IDs
and timeout reason, `no-store`, bounded windows, unknown downstream settings and
identity-free authenticated admission aggregates. It terminates its own process
and cleans its temporary working directory.

Leader-observed output for both local and Zapp runs:

```json
{"aggregate_admission":true,"both_ids":true,"bounded_window":true,"loopback_only":true,"operator_auth":true,"passed":true,"synthetic_history":true,"timeout_attribution":true}
```

This tests the readout of a seeded timeout event, not generation of a real
inference timeout. No serving-path recovery or reduction in actual upstream
errors follows from this smoke result.

## Original incident context and provenance

The following is the **reported initiating incident from the operator/session
investigation**, not a new measurement made by this evidence author. Original
production logs and the full diagnostic-ID-to-transport-ID mapping are not
included in this evidence directory. Consequently these historical counts and
timings are excluded from the local `proven` acceptance claims; they require the
original retained query/log evidence for independent revalidation.

The operator's closed 15-minute view, checked at 10:42:05 PDT on 2026-10-20,
reported **24 queue timeouts, 39 upstream errors and 3 next-hop busy outcomes**.
The investigation identified **Zapp** as the production edge and **Hive** as the
serving peer; **Fry is no longer a gateway**. The reported upstream route was
`node_hive-rust:qwen3.8-27b-modality-vision-quant-q8_k_xl` / `hive-gateway`.

These four IDs were copied from the operator's diagnostic list. They are
**diagnostic IDs**, not transport request IDs. The initial investigation reported
matching them to transport logs with the following results:

| Displayed diagnostic ID | Listed request time (PDT) | Reported Hive backend | Reported time from first response bytes to failure |
| --- | --- | --- | --- |
| `63438e04-ce8f-44e2-afad-c86103888157` | 10:40:11 | `hive-dc-7-6-14` (A100) | 30.09 s |
| `7e8f268c-7528-41fe-8cf4-6ae8a60604d2` | 10:40:55 | `hive-dc-7-5-58` (Blackwell) | 30.15 s |
| `1f376c11-b556-4a51-b952-e814d6eb9c5d` | 10:41:02 | `hive-dc-7-5-58` (Blackwell) | 30.12 s |
| `c07371ab-8326-4c14-8c05-81ec137327e7` | 10:41:28 | `hive-as-11-4-30` (A100) | 30.26 s |

The reported connector symptom was an answer ending before its final HTTP
chunk. The investigation associated the timing with Hive's heartbeat freshness
interval being reused as inference silence at deployed revision `c673fad2`.
These are historical incident statements, not current service status or proof
that a new timeout policy has recovered production.

## Remaining proof obligations

- Rust serving-path implementation and its own authenticated stream statistics
  endpoint are outside this pinned Go proof. AC-STREAM-01..05 remain outside this
  record; the Go abort regression supplies only a narrow supporting control for
  failed accounting.
- Preserve the disposable PostgreSQL execution evidence above when assembling
  the final evidence bundle; production database behavior is not inferred from
  those isolated fixture results.
- Complete independent cross-component review and verify exact source revisions
  and effective settings deployed to each hop.
- Exercise long prefill, meaningful reasoning/tool output, inactivity/deadline
  failures, cancellation and disconnect behavior over the real supported paths.
- Trace a real attempt using the separately displayed IDs through Zapp and Hive
  logs without exposing private request content.
- Perform the production canary and comparable-traffic post-rollout measurement
  before claiming reduced upstream failures, recovered queueing, or fleet health.

This record changes no production state and closes no deployment or GPU
qualification gate. See [`OPEN_GATES.md`](../../OPEN_GATES.md).

## Final Go binary smoke after the timeout-evidence extension

The session leader built product revision `179f20c1d647fa5dde0480a3b4bb02d23eb5957e`
with `CGO_ENABLED=0 go build -mod=vendor -trimpath -ldflags '-s -w'` and verified
artifact SHA-256
`b135276c043fef356c27a7b5ee6d86d2ec5b752d9aa44ce473f24675c63550b7`.
The isolated binary smoke passed locally and on Zapp, including retained
`effective_idle_timeout_ms`, `elapsed_ms`, and finite `phase`, operator refusal
of unauthenticated/client-only callers, both correlation IDs, bounded windows,
unknown downstream configuration, and aggregate-only admission access. The
reproducible synthetic script and binary are staged at
`/tmp/iw-stream-reliability-179f20c/` locally and
`/tmp/iw-reliability-canary-179f20c.YDLByX/` on Zapp. The script uses generated
private temporary credentials and synthetic history and cleans up its process
and temporary state. No production container, credentials, history or route
was changed. This supersedes only the older binary smoke coverage, not its
recorded artifact identity.

## Staged deployment artifacts (not active)

- Rust implementation/canary details: [rust.md](rust.md) and
  [rust-canary.json](rust-canary.json). Product revision `70553036`; test-only follow-up `de12bb70`.
- Hive's candidate directory contains both verified musl binaries, a manifest,
  and a copy of the current production launcher with both binary exports pinned
  explicitly to the intended `70553036` release path. The candidate is **not**
  installed there and the gateway-cycle command has **not** been run. CLI SHA-256:
  `30f81ea7acc921dfc7f170401b089c2ddf6bbb0e792a4e753b915e6b425bd7c7`.
- Zapp's prepared Go image is
  `inferweave-gateway:stream-reliability-179f20c`, image ID
  `sha256:99a159a547898f399d77d6bc41c7e08fcb8cffc499cfd1337f47462e63e20cbf`.
  It preserves the deployed runtime image and replaces only the tested Go binary;
  its revision label and ability to execute were checked. No Compose service was
  recreated and no public frontend was switched.

Production rollout remains a separate external-production approval boundary.
The candidate artifacts, source, tests, canary results, rollback approach and
remaining verification limits are concrete and reviewable before that decision.
