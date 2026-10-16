"""Offline level-2 contract checks; not a routing or authorization implementation."""
import json
import re
from pathlib import Path
from datetime import datetime


def _load(root, path):
    return json.loads((root / path).read_text())


def contract_errors(root):
    root = Path(root)
    vocab = _load(root, 'contracts/protocol-v1/dynamic-aliases.json')
    definitions = _load(root, 'schemas/v1/aliases/contract.json')['definitions']
    spec = (root / 'specs/54_DYNAMIC_MODEL_ALIASES.md').read_text()
    documents = {}
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
        # A vocabulary is documented in spec 54 unless the entry names the document that owns it.
        owner = entry.get('document')
        text = spec if owner is None else documents.setdefault(owner, (root / owner).read_text())
        for value in entry['values']:
            if f'`{value}`' not in text:
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
    if [a['id'] for a in acceptance] != list(range(1, 36)):
        errors.append('alias acceptance IDs incomplete or duplicate')
    for entry in acceptance:
        if entry['proof_status'] not in {'proven', 'owed'}:
            errors.append('invalid alias acceptance proof status')
        if entry['proof_status'] == 'proven' and not entry['evidence']:
            errors.append(f"alias acceptance {entry['id']} has no evidence")
    errors.extend(precision_table_errors(root, definitions))
    # Security transcript is frozen separately and must reproduce known answers.
    import sys
    sys.path.insert(0, str(root / 'conformance'))
    import alias_edge_delegation
    errors.extend(alias_edge_delegation.check_vectors(root))
    return errors


def precision_table(root=None):
    """Version number -> {token: class} from schemas/v1/aliases/precision-classes.json."""
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    table = _load(root, 'schemas/v1/aliases/precision-classes.json')
    return {v['version']: {t: band for band, tokens in v['classes'].items() for t in tokens}
            for v in table['versions']}


def precision_table_errors(root, definitions):
    """Spec 61 required test 6: the table is additive and a token never changes class."""
    errors = []
    raw = _load(root, 'schemas/v1/aliases/precision-classes.json')['versions']
    bands = definitions['precision_band']['enum']
    if [v['version'] for v in raw] != list(range(1, len(raw) + 1)):
        errors.append('precision table versions must be consecutive from 1')
    for version in raw:
        if list(version['classes']) != bands:
            errors.append('precision table classes drift from the band vocabulary')
        flat = [t for tokens in version['classes'].values() for t in tokens]
        if len(flat) != len(set(flat)):
            errors.append(f"precision table v{version['version']} places a token in two classes")
        if any(not re.fullmatch(r'[a-z0-9._]{1,32}', t) for t in flat):
            errors.append(f"precision table v{version['version']} holds a token outside the alphabet")
        if 'awq' in flat:
            errors.append('awq names a method, not a width, and is never classified')
    tables = precision_table(root)
    for older, newer in zip(sorted(tables), sorted(tables)[1:]):
        for token, band in tables[older].items():
            if tables[newer].get(token) != band:
                errors.append(f'precision token {token} was dropped or moved between v{older} and v{newer}')
    return errors


def adhoc_errors(document, tables):
    """Spec 61 conflict rules for an ad-hoc selection, evaluated against its pinned table."""
    errors = []
    selection = document['selection']
    required = selection['required']
    pin = selection.get('precision_table_version')
    members = [m for m in ('min_precision_class', 'quantization_allow', 'quantization_deny') if m in required]
    if pin is not None:
        if pin not in tables:
            errors.append('precision table version is not held')
        if not members:
            errors.append('precision table pin beside no precision member')
    table = tables.get(pin if pin is not None else max(tables), {})
    order = ['very_low', 'low', 'medium', 'high', 'full']
    allow = required.get('quantization_allow')
    deny = set(required.get('quantization_deny', []))
    if allow is not None:
        remaining = [t for t in allow if t not in deny]
        if not remaining:
            errors.append('allow set is empty after removing the deny set')
        minimum = required.get('min_precision_class')
        if minimum and remaining and not any(
                table.get(t) and order.index(table[t]) >= order.index(minimum) for t in remaining):
            errors.append('no allowed token can meet the minimum precision class')
    request_required = document.get('request_context', {}).get('required', {})
    if request_required.get('quantization_allow') is not None and not [
            t for t in request_required['quantization_allow'] if t not in set(request_required.get('quantization_deny', []))]:
        errors.append('request allow set is empty after removing the deny set')
    return errors


def tree_errors(document):
    """The four-level tree and the flat list never disagree (spec 61 Resolution tree)."""
    errors = []
    tree = document['resolution_tree']['selection']
    if tree['adhoc'] is not True or document.get('alias') is not None or document['adhoc'] is not True:
        errors.append('ad-hoc response must report adhoc true and alias null')
    nodes = {(m['model_id'], i['instance_id']): i for m in tree['models'] for i in m['instances']}
    counted = tree['instances_omitted']
    for candidate in document['candidates']:
        key = (candidate['model_id'], candidate['instance_id'])
        node = nodes.get(key)
        if node is None:
            if counted <= 0 and tree['models_omitted'] <= 0:
                errors.append('candidate missing from the tree and not counted as omitted')
            continue
        counted_local = (node['state'], node['eligibility'], node['reasons'])
        if counted_local != (candidate['state'], candidate['eligibility'], candidate['reasons']):
            errors.append('tree instance contradicts the flat candidate list')
    if (tree['models_omitted'] or tree['instances_omitted']) and not document['truncated']:
        errors.append('a truncated tree must set truncated')
    for scope in [tree] + tree['models']:
        if scope['unmet_omitted'] and not scope['unmet_truncated']:
            errors.append('omitted unmet entries must set unmet_truncated')
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
    if kind in {'draft-write', 'simulate-request'} and 'definition' in document:
        errors.extend(semantic_errors(document['definition'], 'definition'))
    if kind in {'resolve-request', 'simulate-request'} and 'selection' in document:
        errors.extend(adhoc_errors(document, precision_table()))
    if kind == 'adhoc-resolution':
        errors.extend(tree_errors(document))
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
    if kind in {'resolution', 'catalog', 'adhoc-resolution'}:
        candidates = document['items'] if kind == 'catalog' else document['candidates']
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
    if kind in {'resolution', 'adhoc-resolution'}:
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
