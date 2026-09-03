# AI Assistant: Install and Configure InferWeave

You are configuring a machine for InferWeave.

The operator will tell you the desired role: `gateway`, `node`, `edge`, `site`, `proxy`, or `slurm-worker`.

## Rules

- Prefer the official `inferweave` CLI over hand-written configuration.
- Do not inspect or reuse historical InferWeave repositories.
- Do not disable host security controls to make installation easier.
- Do not expose credentials, enrollment secrets, API keys or prompt contents.
- Do not delete/reset an existing installation unless the operator explicitly approves it.
- Do not open firewall ports until `inferweave init plan` states they are needed.
- Prefer outbound connectivity for nodes.
- Prefer direct data paths and local/site/regional relay fallback.
- Use containers generated/managed by the InferWeave CLI.

## Procedure

1. Verify/install the official signed InferWeave CLI.
2. Run:

   ```text
   inferweave doctor --json
   ```

3. Inspect blockers/warnings and explain any blocker that cannot safely be resolved automatically.
4. Run:

   ```text
   inferweave init plan ROLE --json
   ```

5. Review the plan for:
   - disk;
   - ports;
   - GPU/container compatibility;
   - TLS;
   - volumes;
   - enrollment;
   - changes requiring elevated privilege.
6. Apply safe prerequisites.
7. Run:

   ```text
   inferweave init ROLE --yes --json
   ```

8. For a node/site/edge, securely complete gateway enrollment using the operator-provided gateway/enrollment code.
9. Run:

   ```text
   inferweave verify --json
   inferweave status --json
   ```

10. If verification fails, use only supported diagnostic commands first:
    - `inferweave doctor --json`
    - `inferweave logs --json`
    - `inferweave support-bundle`
11. Finish only when the requested role is healthy and, when applicable, visible at the gateway.

Report:
- installed version;
- role;
- stable InferWeave identity;
- detected GPUs;
- gateway connection;
- containers/services;
- health;
- remaining warnings.

Never print secrets.
