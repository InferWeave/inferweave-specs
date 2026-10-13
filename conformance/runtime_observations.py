"""Offline spec56 shape/order reference checks; never runtime or admission proof."""
import json
from pathlib import Path
from jsonschema import Draft7Validator, RefResolver


def semantic_errors(report):
    errors = []
    if not 0 < report['expires_at_ms'] - report['observed_at_ms'] <= 60000:
        errors.append('invalid report TTL')
    identities = set()
    for item in report['instances']:
        obs = item['observation']
        if obs['instance_id'] in identities:
            errors.append('duplicate instance identity')
        identities.add(obs['instance_id'])
        if obs['source_epoch'] != report['source_epoch']:
            errors.append('item epoch differs from report')
        if obs['sequence'] > report['sequence']:
            errors.append('item sequence newer than snapshot')
        if obs['observed_at_ms'] > report['observed_at_ms']:
            errors.append('item observation newer than snapshot')
        if not 0 < obs['expires_at_ms'] - obs['observed_at_ms'] <= 60000:
            errors.append('invalid item TTL')
    return errors


def disposition(report, context):
    """Reference for fixed-clock hostile vectors, without real credentials or storage."""
    errors = semantic_errors(report)
    now = context['now_ms']
    if report['source_id'] != context['authenticated_node_id']:
        errors.append('source identity mismatch')
    if report['source_epoch'] != context['registered_epoch']:
        errors.append('epoch is not current registered epoch')
    if not context['current_connection'] or not context['negotiated']:
        errors.append('unbound connection or unnegotiated capability')
    if not report['observed_at_ms'] <= now < report['expires_at_ms']:
        errors.append('report not fresh')
    previous = context.get('previous_report')
    if previous is not None and previous['source_epoch'] == report['source_epoch']:
        if report['sequence'] < previous['sequence']:
            errors.append('sequence regression')
        if report['sequence'] == previous['sequence'] and report != previous:
            errors.append('conflicting duplicate')
    if errors:
        return {'accepted': False, 'producer_ready': []}
    tombstoned = {tuple(identity) for identity in context.get('tombstoned', [])}
    ready = []
    for item in report['instances']:
        obs = item['observation']
        if (obs['instance_id'], obs['generation']) in tombstoned and obs['lifecycle'] == 'READY':
            return {'accepted': False, 'producer_ready': []}
        if (obs['generation'] and obs['lifecycle'] == 'READY' and obs['health'] == 'HEALTHY'
                and obs['observed_at_ms'] <= now < obs['expires_at_ms']):
            ready.append(obs['instance_id'])
    return {'accepted': True, 'producer_ready': ready}


def check_vectors(root):
    root = Path(root)
    schema_path = root / 'schemas/v1/requests/runtime-observation-report.json'
    schema = json.loads(schema_path.read_text())
    store = {}
    for path in (root / 'schemas/v1').rglob('*.json'):
        document = json.loads(path.read_text())
        if '$id' in document:
            store[document['$id']] = document
    validator = Draft7Validator(schema, resolver=RefResolver.from_schema(schema, store=store))
    vectors = json.loads((root / 'conformance/runtime-observation-vectors.json').read_text())
    errors = []
    if not vectors['vectors']:
        return ['runtime observation vectors empty']
    for case in vectors['vectors']:
        report = case['report']
        actual = ({'accepted': False, 'producer_ready': []} if list(validator.iter_errors(report))
                  else disposition(report, case['context']))
        if actual != case['expected']:
            errors.append(f"runtime observation {case['id']}: {actual} != {case['expected']}")
    return errors
