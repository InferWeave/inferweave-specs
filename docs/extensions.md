# InferWeave Protocol v1 — extensions

All protocol objects may contain an `extensions` object keyed by `organization-or-vendor`:

```json
{ "extensions": { "metabolomics-us": { "cost_center": "lab-ai", "deployment": "production" } } }
```

## Rules

- Core readers MUST ignore unknown extension namespaces.
- Extension namespaces are organization/vendor-scoped; never use a peer's namespace.
- Extensions are advisory metadata, not protocol-visible behavior. If a capability must be
  understood by other peers, it belongs in the protocol (a new feature/field), not an extension.
- Organization-specific metadata (cost centers, deployment labels, analytics tags) is the
  intended use.

## Relation to feature negotiation

A behavior that some peers support and others do not should be a negotiated feature, not an
implicit extension. Extensions are for metadata that does not change protocol semantics.
