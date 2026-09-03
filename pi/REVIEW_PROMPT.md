# Independent Review Prompt

Review the change against the requirement IDs and `specs/00_INVARIANTS.md`.

Do not assume implementation intent is correct.

Check:
- hard-constraint routing violations;
- capacity/accounting errors;
- 429/503 semantic drift;
- unbounded queue/retry;
- session affinity/cancellation leaks;
- concurrency/idempotency races;
- owner/FairShare gaming;
- private data in logs/snapshots/receipts;
- mutable deployment identity;
- plane/repository ownership drift;
- missing failure tests;
- unsafe node admin exposure;
- mainnet/real-value blockchain dependency.

Return blocking findings first with file/symbol and reproduction/test suggestion. Then non-blocking improvements. Do not approve based solely on style or AI-generated tests.
