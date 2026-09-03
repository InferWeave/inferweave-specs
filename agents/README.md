# Agent Roles

This folder describes recommended responsibilities for agents collaborating on InferWeave specifications.

## Roles

### Spec Author
See `agents/spec-author.md`.

Turns requirements/research into canonical specifications and feature IDs.

### Implementation Planner
See `agents/implementation-planner.md`.

Maps approved specifications into bounded 50–100K-context implementation tasks and dependency gates.

### Spec Reviewer
See `agents/spec-reviewer.md`.

Independently checks consistency, missing failure modes, security, observability, acceptance and task coverage.

### Operations / Hardware Reviewer
See `agents/hardware-ops-reviewer.md`.

Checks GPU, Docker, Apptainer, Slurm, watchdog, telemetry, recovery and deployment feasibility.

No role may silently override resolved decisions.
