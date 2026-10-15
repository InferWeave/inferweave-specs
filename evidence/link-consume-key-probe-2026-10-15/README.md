# Evidence: a key is accepted by the public HTTPS API today

Measured 2026-10-15 from bender against `https://llm.metabolomics.us` (the key itself is not
recorded here).

* `GET /v1/models` with `Authorization: Bearer <key>` returned HTTP 200 and 9 model entries.
* `POST /v1/chat/completions` with the same key, model `x` (not a real model) and `max_tokens`
  1 returned HTTP 429. This is **not** evidence that completions work with the key.

Reproduce: `curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $KEY"
https://llm.metabolomics.us/v1/models`. This shows only that a key authenticates a read on the
public API; it says nothing about the link protocol.
