# Model-intelligence HTTP contract and current implementation boundary

This additive [OpenAPI 3.0.3 contract](model-intelligence.yaml) uses server `/`.
It does not change Protocol v1's `/inferweave/v1` base or inference APIs. The
Rust source snapshot is `35ac81e7b0a0c3cba23390c1adae092ea392ca0d` in
`InferWeave/inferweave`; the Go adapter snapshot is
`613c78187af0719b7dc91eda06b677b58f06a2b8` in
`metabolomics-us/inferweave-gateway`. This is an implementation contract, not
proof that all normative spec 58 requirements or the full kit are complete.

## Reads, authority and bounds

GET `/iw/v1/model-intelligence/{summary,timeseries,incidents,tokens,capacity,evaluations,candidates,costs}`
currently returns the same complete report per bounded query. Every route requires
the existing `X-Inferweave-Admin` secret. Ordinary inference/worker bearer tokens
and `x-inferweave-tenant` cannot authorize any of these reads. Both `scope=operator`
and `scope=shared` currently name authenticated operator fleet queries; the latter
is not anonymous publication, a private tenant grant, or an end-user report.
Unknown parameters, duplicate scalar parameters and GET bodies fail closed.

GET `/console/api/model-intelligence/report` uses existing Go `s.operator`: an
operator-authorized `iw_session` cookie or the exact configured registration
secret through its existing Bearer middleware alternative. That explicit secret
is not an inference client token. The adapter forwards neither browser identity
headers nor caller credentials; it authenticates the configured Rust origin using
its configured admin secret. No new tenant delegation or shared-worker credential
is created. Private tenant/user filters are rejected. Nonoperators get protected
presentation rather than private report polling. The normative shared operational
view and private-scope grants remain **owed**, not removed from spec 58.

`start`/`end` are half-open Unix millisecond bounds, at most 30 days and not in the
future. The Rust default is the last hour. `bucket_seconds` defaults to 3600;
`series_metric` defaults to the actual domain key `ttft_ms_p95`. Repeated `model_id`
and `gateway_id` are arrays (at most 200 values, 512 bytes each). `limit` accepts
1..1000 (default 100), while `effective_limit` is at most 20. Model offset `cursor`
is decimal. Keep window, filters and selected metric fixed across pages.

The service coarsens time buckets to at most 400 model/bucket pairs. Each bucket
contains only `series_metric`; pooled full-window metrics remain available.
Responses publish requested/effective bucket seconds, effective limit, next cursor,
coverage and retention clipping. The 10,000-observation cap and 30-day retention
may produce partial coverage; known subtotals are not complete totals. Responses
above 1,900,000 bytes shrink pages, then explicitly omit detail if necessary;
`coverage.display_truncated` and `response_size_limit` disclose this. The Go
adapter retains its 2 MiB cap and 10-second deadline, no redirects/cookie jar,
and HTTPS-or-loopback-HTTP origin restriction. Query reads time out at five
seconds; storage statement timeout is two seconds.

`WarehouseReport` requires the complete measurement and pagination envelope.
`UnsupportedReport` documents the actual smaller backend-unavailable/configuration
absence response: version/window/as_of/cohort/source/status/models remain present,
but bucket/page/coverage metadata is not manufactured. This distinction is an
explicit current capability gap. Report `status=measured` describes available
observations, never completeness of every nested metric or production qualification.

## Typed accounting and qualification

`MetricValue` retains nullable value/numerator/denominator/confidence, sample and
eligible/observed counts, source, cohort, time window and definition version.
`CountAggregate.total` is nullable while `known_total` is a subtotal. Token
`overlap_cache_write` and `overlap_output_reasoning` are separate annotations,
never additive exclusive buckets. These reports currently expose physical attempt
usage; missing logical request or downstream task linkage remains unknown.

HTTP `amount_nanos`, `known_subtotal_nanos` and `unattributed_nanos` are **decimal
strings**, preserving all u64 digits. Null remains null. No money is inferred
from token throughput or VRAM. Cost results remove private allocation subjects.
Capacity is typed `CapacityReport`, multiple such reports, or an explicit missing
section. Evaluations/candidates contain typed `ComparisonReport` cohorts or an
explicit missing section. No opaque JSON bag substitutes for these contracts.
Recommendations are read-only; no routing or model-promotion mutation is exposed.

## Operator configuration, storage and rollback

The Go adapter uses `IW_MODEL_INTELLIGENCE_CORE_URL` and
`IW_MODEL_INTELLIGENCE_CORE_ADMIN_TOKEN_FILE`. Configure them together. Protect
the existing Rust admin credential file as an operator secret; never send it to
the browser. Invalid origins, token files, redirect attempts and oversized replies
fail closed. An unconfigured adapter returns capability absence without demo data.

Rust optionally reads `IW_MODEL_INTELLIGENCE_RATES_FILE`: UTF-8 JSON no larger than
65,536 bytes, with `provider` and `self_hosted` arrays (at most 200 cards each).
The OpenAPI components `RateConfiguration`, `ProviderRateCard` and
`SelfHostedRateCard` also describe this admin-local file; it is not an HTTP write
endpoint. Configuration monetary inputs are exact JSON u64 integers, unlike HTTP
response decimal strings. Empty arrays/missing configuration preserve unknown
prices. Rate version identity, effective time, context tiers, currency and GPU
accounting basis are validated by existing Rust economics constructors; invalid
configuration fails startup without echoing file content. Applying a configured
rate is not invoice evidence. Source billing/physical GPU evidence is still needed.

Migration `0010_model_intelligence.up.sql` adds the observation relation and
indexes in existing PgStore; previous migration checksums are unchanged. Exact
replay is idempotent, conflicting replay fails. Retention deletion is bounded per
write; idle storage may retain older rows on disk while queries exclude them.
Before migration rollback, export any observation evidence that must survive;
the down migration removes the new table/index and historical-time index. Roll
back code/UI/configuration through the existing reviewed deployment process.
This documentation does not authorize deployment, drop data, or promote models.

## Verification record

See [acceptance evidence](../evidence/model-intelligence-2026-10-12/README.md).
Three real local PostgreSQL HTTP fixture exports were checked against typed
schemas, including the default 24-hour/four-model and 30-day/two-model responses.
These are synthetic DEMO inputs, not measured fleet qualification. Missing window,
numeric money, string capacity count and string recommendation flag were rejected.
Both explicitly unsupported envelope forms were accepted. All references resolve
and all eight Rust paths require Rust admin authentication in the document.
Executable runtime authorization and final browser/P5 review remain separate.
