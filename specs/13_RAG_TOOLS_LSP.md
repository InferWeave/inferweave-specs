# 13 — Agentic RAG, Tool and LSP Capabilities

## RAG

Retrieval is a composable service/tool, not gateway business logic.

Support sources such as:
- semantic/vector;
- lexical;
- graph/relationship;
- repository filesystem;
- symbols/LSP;
- AST/structural indexes;
- git history;
- issues/PRs;
- documentation.

Every retrieved passage carries source/provenance, confidence and version/lineage. Tenant/project isolation is mandatory.

## Context bundles

AutoSpec can construct deterministic reusable context bundles. Large repository context may be cached at a local InferWeave proxy/node where privacy policy permits. Cache invalidation is revision/fingerprint based.

## Tool services

Tool capability advertisement declares protocol/version/auth/sandbox/resource policy. A request must not be routed to a node merely because it serves the model if required tools are unavailable.

## LSP

Use existing self-hosted language servers. InferWeave may broker remote LSP access where useful but does not reimplement language-server protocols. LSP processes have their own lifecycle/health/capacity separate from LLM seats.

## Security

Public inference nodes never receive arbitrary shell/filesystem/network tool access simply because a model supports tools. Tool permissions are explicit capabilities and policy.
