"""Offline level-2 contract checks; not a routing or authorization implementation."""
import json
from pathlib import Path
from datetime import datetime


def _load(root, path):
    return json.loads((root / path).read_text())


def contract_errors(root):
    root = Path(root)
    vocab = _load(root, 'contracts/protocol-v1/dynamic-aliases.json')
    definitions = _load(root, 'schemas/v1/aliases/contract.json')['definitions']
    spec = (root / 'specs/54_DYNAMIC_MODEL_ALIASES.md').read_text()
    errors = []
    for name, values in [('reason', [r['code'] for r in vocab['reason_codes']]),
                         ('event_type', vocab['events']), ('health', vocab['health_states'])]:
        if len(values) != len(set(values)) or definitions[name]['enum'] != values:
            errors.append(f'alias {name} schema/frozen vocabulary drift')
        for value in values:
            if f'`{value}`' not in spec:
                errors.append(f'alias {name} absent from published document: {value}')
    for reason in vocab['reason_codes']:
        row = f"| `{reason['code']}` | {str(reason['retryable']).lower()} | {reason['http_status']} |"
        if row not in spec:
            errors.append(f"alias reason semantics differ from document: {reason['code']}")
    for name, entry in vocab['vocabularies'].items():
        node = {'definitions': definitions}
        for part in entry['schema_path']:
            node = node[part]
        if node['enum'] != entry['values']:
            errors.append(f'alias {name} frozen vocabulary differs from schema')
        for value in entry['values']:
            if f'`{value}`' not in spec:
                errors.append(f'alias {name} missing documented value {value}')
    required_fields = {'model_id', 'instance_id', 'instance_generation', 'deployment_key',
                       'owner_gateway_id', 'resource_group_id', 'capability_profile',
                       'owner_admission_required'}
    if not required_fields <= set(definitions['candidate']['required']):
        errors.append('alias candidate lost required instance-level evidence')
    if not {'instance_generation', 'confidence'} <= set(definitions['capability_profile']['required']):
        errors.append('alias profile lost generation or confidence binding')
    if definitions['resolution']['properties']['admission_reserved'] != {'const': False}:
        errors.append('alias preview may reserve admission')
    if definitions['advertisement']['properties']['allocation_entitlement'] != {'const': False}:
        errors.append('alias advertisement confers entitlement')
    acceptance = _load(root, 'contracts/dynamic-alias-acceptance.json')['acceptance']
    if [a['id'] for a in acceptance] != list(range(1, 30)):
        errors.append('alias acceptance IDs incomplete or duplicate')
    for entry in acceptance:
        if entry['proof_status'] not in {'proven', 'owed'}:
            errors.append('invalid alias acceptance proof status')
        if entry['proof_status'] == 'proven' and not entry['evidence']:
            errors.append(f"alias acceptance {entry['id']} has no evidence")
    # Security transcript is frozen separately and must reproduce known answers.
    import sys
    sys.path.insert(0, str(root / 'conformance'))
    import alias_edge_delegation
    errors.extend(alias_edge_delegation.check_vectors(root))
    return errors


def semantic_errors(document, kind):
    """Checks not expressible as Draft-07 shapes; production must implement these too.

    This deliberately does not resolve aliases, authorize tenants, rank, admit or emulate serving.
    Schema validation runs first. Runtime freshness compares trusted owner time in implementation.
    """
    errors = []
    if kind == 'edge-assertion':
        import alias_edge_delegation
        try:
            alias_edge_delegation.decode_header(alias_edge_delegation.b64url(json.dumps(document).encode()))
        except (ValueError, KeyError, TypeError) as error:
            errors.append(str(error))
    if kind in {'draft-write', 'simulate-request'}:
        errors.extend(semantic_errors(document['definition'], 'definition'))
    if kind == 'detail':
        for field in ['draft', 'published']:
            if field in document:
                errors.extend(semantic_errors(document[field], 'definition'))
    if kind in {'list', 'history'}:
        for item in document['items']:
            if kind == 'list':
                errors.extend(semantic_errors(item, 'detail'))
            else:
                errors.extend(semantic_errors(item['definition'], 'definition'))
    if kind == 'error':
        vocab = _load(Path(__file__).resolve().parents[1], 'contracts/protocol-v1/dynamic-aliases.json')
        retryable = {r['code']: r['retryable'] for r in vocab['reason_codes']}
        if document['retryable'] != retryable[document['code']]:
            errors.append('error retryability disagrees with frozen reason')
    if kind in {'resolution', 'catalog'}:
        candidates = document['candidates'] if kind == 'resolution' else document['items']
        for candidate in candidates:
            if candidate['instance_generation'] != candidate['capability_profile']['instance_generation']:
                errors.append('candidate and profile instance generations disagree')
            profile = candidate['capability_profile']
            if profile.get('max_context_tokens') is not None and profile.get('max_output_tokens', 0) > profile['max_context_tokens']:
                errors.append('profile output ceiling exceeds total context ceiling')
    if kind == 'definition':
        selection = document['selection']
        weights = selection['preferred']
        if not weights or abs(sum(weights.values()) - 1.0) > 1e-6:
            errors.append('preference weights must sum to one')
        if selection['type'] == 'MANAGED' and not selection.get('model_ids_allow'):
            errors.append('managed aliases require concrete allowlist')
        if set(selection.get('model_ids_allow', [])) & set(selection.get('model_ids_deny', [])):
            errors.append('allow and deny lists conflict')
        for value in selection.get('model_ids_allow', []) + selection.get('model_ids_deny', []):
            if value.startswith(('alias:', 'cap:')):
                errors.append('alias indirection forbidden')
    if kind == 'resolution':
        evaluated = datetime.fromisoformat(document['evaluated_at'].replace('Z', '+00:00'))
        expires = datetime.fromisoformat(document['expires_at'].replace('Z', '+00:00'))
        if expires <= evaluated:
            errors.append('preview expiry must follow evaluation')
        ready = [c for c in document['candidates'] if c['eligibility'] == 'ELIGIBLE' and c['state'] == 'READY']
        if document['status'] in {'READY', 'DEGRADED'} and not ready:
            errors.append('ready health needs an eligible ready candidate')
        selected = document.get('selected')
        if selected:
            matches = [c for c in ready if all(c.get(k) == v for k, v in selected.items())]
            if not matches:
                errors.append('selected instance missing or generation disagrees')
            for candidate in matches:
                profile = candidate['capability_profile']
                evidence = [profile['provenance']] + [f['provenance'] for f in profile['features'].values()]
                if any(datetime.fromisoformat(p['expires_at'].replace('Z', '+00:00')) < expires for p in evidence):
                    errors.append('preview outlives selected evidence')
    return errors
