# Pi/Qwen Context Guide — 50K–100K

Use `implementation/CONTEXT_50_100K_STRATEGY.md` as canonical.

## Default
Implementation task: target **55K–70K supplied context**.

## Integration
Use **65K–82K** for cross-service contracts.

## Review
Use **80K–100K** for independent review/E2E/spec verification, with minimal code generation.

## Pack order
1. `pi/PI_IMPLEMENTATION_SYSTEM_PROMPT.md`
2. `specs/00_INVARIANTS.md`
3. exact canonical task from `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`
4. target spec files
5. exact current contracts/types
6. relevant source/tests
7. current focused failure output

## Avoid
Do not provide all specs or the whole monorepo. Large context is a budget, not a target.

## Prefix reuse
Keep the system prompt + invariants stable across tasks for inference prefix caching.
