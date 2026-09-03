# Error Semantics

Canonical machine-readable body:

```json
{
  "error": {
    "type": "inferweave_capacity_exhausted",
    "code": "NO_CONTEXT_CAPACITY",
    "message": "No eligible deployment has safe capacity",
    "retryable": true,
    "retry_after_ms": 2500,
    "request_id": "req_..."
  }
}
```

## HTTP mapping

- `400` invalid request/unsupported invalid parameter.
- `401` missing/invalid authentication.
- `403` authenticated but policy/permission denied.
- `404` resource not found.
- `409` native API state conflict or route preview has no candidate satisfying an explicitly non-relaxable preference contract.
- `413` input/body/artifact metadata too large.
- `429` user/API-key/rate/FairShare restriction.
- `503` model/infrastructure/context/capacity unavailable.
- `504` bounded upstream execution/admission deadline exceeded where appropriate.

## Capacity reason codes

`NO_MODEL`, `NO_DEPLOYMENT`, `NO_CAPABILITY`, `NO_CONTEXT_CAPACITY`,
`NO_RESOURCE_HEADROOM`, `ALL_DRAINING`, `ALL_STALE`,
`REGION_UNAVAILABLE`, `PRIVACY_CONSTRAINT`, `LICENSE_CONSTRAINT`,
`OWNER_RESERVE`, `NODE_OVERLOADED`, `BACKEND_UNHEALTHY`,
`CONTEXT_WINDOW_EXCEEDED`.

## Permanent versus transient capacity failures

Every code above except one describes a condition that may clear on its own.

`NO_CONTEXT_CAPACITY` is transient: this deployment could serve this request later.

`CONTEXT_WINDOW_EXCEEDED` is permanent for that deployment. The request exceeds the model's
context ceiling and no amount of waiting changes that. It maps to `413`, carries
`"retryable": false`, and must name the actual ceiling so a client can shrink deliberately
instead of retrying blindly.

Returning a retryable `503` for a permanently oversized request turns the client's own error
handling into a retry loop, and each attempt pays the full prefill cost before failing.

Hard policy failures may map to 403 rather than capacity responses depending on whether revealing eligibility would leak sensitive policy.

## Retry
`retryable` is explicit. Do not make clients infer retry behavior from string messages.
