# Link initial-credit interoperability — 2026-11-04

## Scope

Feature IDs: `IW-DP-001`, `IW-DP-002`; task `P1-T18`; spec 59.

This evidence covers one compatibility boundary: the initial response-credit
allowance between the Rust Link peer and the Go site gateway. It does not qualify
production rollout, other Link behavior, or alias execution.

## Defect and measured boundary

The live failure investigation observed the mismatch on edge revision `3437fae4589d7d985aa97947d050f4f9aadd7661`
and the Farm Rust peer identified by deployed revision `b7924517bdf747104c32dc76db2184cdbd1fc9d8`. The deterministic
reproduction used Go source `b8d7de7` and Rust source `2109b15c`; the constants
and behavior below were read and exercised from those trees rather than copied
from an earlier report.

The Rust `NodeDataPlane` starts a Request with a default allowance of 16 response
items. The Go receiver also sends an explicit initial Credit of 16, but previously
buffered only 16 items. A paused consumer therefore allowed the Rust peer to send
32 authorized items into a 16-item receive queue. The Go receiver terminated that
stream as a credit-window overrun while the shared Link stayed connected.

The specification did not state whether initial credit was implicit or explicit.
That omission caused the implementations to make individually plausible but
incompatible choices.

## Reproduced implementation evidence

The Go implementation tests exercise legacy, HTTP JSON, and operator-control
dispatch with both peer conventions: zero implicit credit and the Rust default
implicit window. With the old receive bound, all three implicit-window cases fail
before the consumer reads. With the compatibility receive bound, all six cases
pass. A separate test sends one item beyond the combined allowance and proves
that only the offending stream ends.

The mixed-language fixture runs the real Rust `NodeLink` and `HttpEngine` against
the Go receiver. It pauses `NextHTTP` until the full initial allowance is buffered,
then verifies that consuming one item returns one credit and permits the final
item. Replacing the compatibility receive bound with the old bound makes this
fixture fail; restoring it makes the fixture pass.

Commands used by the implementation change:

```text
go test -race ./internal/link
IW_TEST_RUST_HTTP_PEER=<reviewed-loopback-fixture> go test -tags integration ./internal/link -run TestHTTPRustInitialCreditsSurviveAPausedConsumer -count=1
```

The fixture path is deliberately environment supplied and loopback-only. This
specification repository does not contain or execute the implementation binaries,
so these command results are reported implementation evidence rather than
reproduced by `validate_specs.py`.

## Remaining proof

- sustained mixed-version production traffic after rollout;
- cancellation and heartbeat progress during saturation;
- production error-rate comparison before and after rollout;
- a negotiated single initial-credit convention that retires the compatibility
  buffer without deadlocking older peers.

Status: the bounded interoperability control is proven in the implementation
fixtures; production qualification remains **owed**.
