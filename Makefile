# Executable gate set for the InferWeave protocol repository.
# Satisfies the autospec executor's gate-execution requirement for the
# pre-existing `.github/workflows/protocol-ci.yml` gate declaration.

.PHONY: check test smoke

# `check` and `test` are the canonical executable gates the executor runs.
check: smoke
	@echo "check: all smoke tests passed"

test: smoke
	@echo "test: all smoke tests passed"

smoke:
	python3 -m pytest tests/smoke/ -q
