# Context Pack Checklist

Before launching a Pi implementation session, verify:

- [ ] Exactly one canonical task card selected.
- [ ] Dependencies are merged/passing.
- [ ] `PI_IMPLEMENTATION_SYSTEM_PROMPT.md` included.
- [ ] `specs/00_INVARIANTS.md` included.
- [ ] Task-specific specs only.
- [ ] Current public types/interfaces loaded from repository.
- [ ] Relevant source/tests selected by symbols/call path.
- [ ] Old build logs removed; latest focused failure included.
- [ ] Historical InferWeave repositories excluded.
- [ ] Downstream task specs excluded unless needed for a current public contract.
- [ ] Input context fits the task's C50–C100 class.
- [ ] At least ~20K context headroom remains for implementation/tool/repair work on a 100K session when code generation is expected.
