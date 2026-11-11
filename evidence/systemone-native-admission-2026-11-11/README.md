# Whiteale native admission incident

Observed2026-11-11 at actual site gateway revision
`fff5115c9eed457869ff3bcaf96eb5b0dc7cb075`: generative admission report had no
models, authenticated SystemOne registry had four ready CPU runtimes, and an
authenticated normal `/v1/systemone` decision returned HTTP200. No customer
content or credentials are included. This proves serving independently from
accepted parent admission-report authority.

Core main `8f65e6ef3a096e21efc1e8a860d06819cd296d65` exports only adaptive
generative admission models and CLI filters against generative adverts only.
The Go consumer additionally synthesizes a1024-token SystemOne context.

The deployment dependency lock pins Laya0.4.8. Independently downloaded wheel
SHA256 `05064d8b949803af8cb173561ed0b24d6be5b62cb86d8d319321577c630d0288`
matches that lock. Its native serve source supplies byte/state/question/batch/
option bounds; tokenizer windows vary by checkpoint and state truncation exists.
The worker launcher pins checkpoint revision
`7b928d828b7b0e022f929d9bd2e44165aa270148`. Those source facts support designing
the explicit envelope; they do not prove every deployed process's active
configuration or authorize copying limits across deployments.

All native-report implementation, mutation-sensitive tests, review/CI and
production qualification remain owed at this commit.

Controlled current-child boundary observations (same deployment, harmless local
qualification input, no payload/answers recorded): state50000 characters returned
HTTP200 with answers and usage in3.211s; state50001 returned HTTP503
`system_one.no_compatible_worker` in0.278s. The latter is a real native input
refusal misclassified as infrastructure failure by the old wrapper. The repair
needs an explicit qualified-envelope refusal before runtime acquisition, while
retaining generic legacy schema validation outside qualified native policy.
These observations do not establish accepted parent native authority.
