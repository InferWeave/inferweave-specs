"""Offline private HTTP boundary model; does not authenticate or persist runtime data."""
from datetime import datetime, timedelta
from decimal import Decimal, DecimalException
import json
from pathlib import Path
import re

import failure_rollups
import request_observations

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / 'contracts/private-observability.json').read_text())


def decode(wire, limit=16777216):
    raw = wire if isinstance(wire, bytes) else wire.encode('utf-8')
    if len(raw) > limit:
        raise ValueError('private observability byte limit exceeded')
    text = raw.decode('utf-8', errors='strict')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result

    def reject(value):
        raise ValueError('nonfinite JSON number')

    try:
        value = failure_rollups.normalize_parent(json.loads(text, object_pairs_hook=pairs,
            parse_int=Decimal, parse_float=Decimal, parse_constant=reject))
        failure_rollups.require_canonical_types(value)
        return value
    except (RecursionError, OverflowError, DecimalException) as error:
        raise ValueError('JSON nesting or numeric limit exceeded') from error


def decode_event(wire):
    return decode(wire, 65536)


def header_errors(headers):
    errors, seen = [], set()
    singletons = set(CONTRACT['authentication']['singleton_headers'])
    singletons.update(('content-length', 'content-type', 'content-encoding', 'transfer-encoding', 'host'))
    for name, value in headers:
        key = name.lower()
        if key in singletons and key in seen:
            errors.append('duplicate security or framing header')
        seen.add(key)
        if key in ('authorization', 'x-inferweave-admin', 'x-inferweave-node') and ',' in value:
            errors.append('comma-combined credential or identity')
    if 'content-length' in seen and 'transfer-encoding' in seen:
        errors.append('ambiguous content-length and transfer-encoding framing')
    if 'authorization' in seen and 'x-inferweave-admin' in seen:
        errors.append('ambiguous credentials')
    if 'x-inferweave-node' in seen and 'x-inferweave-admin' in seen:
        errors.append('ambiguous producer and operator credentials')
    if any(key.startswith('x-inferweave-actor') or key == 'x-inferweave-service' for key in seen):
        errors.append('service actor headers do not authorize this surface')
    return errors


def producer_errors(event, trusted):
    """trusted is supplied by the server, never deserialized from an HTTP request."""
    errors = []
    if trusted.get('authenticated') is not True or trusted.get('registered') is not True:
        errors.append('current authenticated registration required')
    if trusted.get('role') != 'gateway':
        errors.append('gateway role required')
    source = event['source_gateway_id']
    node = trusted.get('node_id')
    bound = bool(node) and (source == node or trusted.get('operator_source_bindings', {}).get(source) == node)
    if not bound or source != trusted.get('source_gateway_id'):
        errors.append('source does not bind authenticated node')
    if len(trusted.get('producer_epochs', [])) > 16:
        errors.append('authorized epoch registry exceeds bound')
    if event['producer_epoch'] not in trusted.get('producer_epochs', []):
        errors.append('producer epoch not authorized')
    if event['lineage']['scope'] == 'trusted' and trusted.get('lineage_authorized') is not True:
        errors.append('trusted lineage lacks independent server authorization')
    return errors


def utc(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
        raise ValueError('canonical whole-second UTC required')
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def query_errors(pairs, kind):
    errors, query = [], {}
    allowed = {'start', 'end', 'limit', 'cursor', *CONTRACT['filters'], *CONTRACT['selector_filters']}
    if kind == 'rollups':
        allowed.add('resolution_seconds')
    for name, value in pairs:
        if name not in allowed or name in query:
            errors.append('unknown or duplicate scalar parameter')
        query[name] = value
    if sum(len(str(k).encode()) + len(str(v).encode()) + 2 for k, v in pairs) > 8192:
        errors.append('query exceeds bound')
    try:
        start, end = utc(query['start']), utc(query['end'])
        bound = 604800 if kind == 'diagnostics' else 7776000
        if not timedelta(0) < end - start <= timedelta(seconds=bound):
            errors.append('window exceeds bound or is empty')
    except (KeyError, ValueError):
        errors.append('invalid time window')
    limit = query.get('limit', '25')
    if not re.fullmatch(r'[0-9]{1,3}', limit) or not 1 <= int(limit) <= 100:
        errors.append('invalid limit')
    if kind == 'rollups' and query.get('resolution_seconds') not in ('300', '3600', '86400'):
        errors.append('invalid resolution')
    for name in CONTRACT['filters']:
        if name in query and not re.fullmatch(r'[\x21-\x7e]{1,128}', query[name]):
            errors.append('invalid exact filter')
    for name, values in CONTRACT['selector_filters'].items():
        if name in query and query[name] not in values:
            errors.append('invalid enum selector')
    if 'cursor' in query and not 1 <= len(query['cursor'].encode()) <= 1024:
        errors.append('invalid cursor')
    return errors


def cursor_errors(claims, operator, endpoint, query, now, snapshot_live):
    """Claims are verified server cursor state; this model does not mint/authenticate tokens."""
    errors = []
    if claims.get('operator') != operator or claims.get('endpoint') != endpoint or claims.get('query') != query:
        errors.append('cursor binding mismatch')
    try:
        if utc(now) >= utc(claims['expires_at']) or not snapshot_live:
            errors.append('cursor expired or snapshot invalidated')
    except (KeyError, ValueError):
        errors.append('invalid cursor expiry')
    if not claims.get('snapshot_id') or not claims.get('last_sort_key'):
        errors.append('cursor lacks snapshot or position')
    return errors


def page_errors(page, kind, root=ROOT):
    """Call only after schema validation, including all nested DTO schemas."""
    errors = []
    pairs = [(k, str(v)) for k, v in page['query'].items() if v is not None]
    errors.extend(query_errors(pairs, kind))
    try:
        age = utc(page['expires_at']) - utc(page['as_of'])
        if not timedelta(0) < age <= timedelta(seconds=300):
            errors.append('snapshot lifetime exceeds bound')
    except ValueError:
        errors.append('invalid snapshot time')
    if len(page['items']) > page['query']['limit']:
        errors.append('page exceeds selected limit')
    if page['query_health']['status'] == 'available' and page['query_health']['reason'] != 'none':
        errors.append('available query cannot report a degradation reason')
    if page['query_health']['status'] != 'available' and page['query_health']['reason'] == 'none':
        errors.append('degraded query needs reason')
    if page['query_health']['status'] == 'unavailable' and (page['items'] or page['next_cursor'] is not None):
        errors.append('unavailable query cannot return rows or continuation')
    contract = json.loads((root / 'contracts/request-observation.json').read_text())
    identities = set()
    previous_sort_key = None
    for item in page['items']:
        row = item['parent'] if kind == 'rollups' else item
        key = tuple(row[k] for k in ('source_gateway_id', 'producer_epoch', 'rollup_id' if kind == 'rollups' else 'event_id'))
        if key in identities:
            errors.append('duplicate row identity')
        identities.add(key)
        if kind == 'rollups':
            errors.extend(request_observations.rollup_errors(row, contract))
            if row['resolution_seconds'] != page['query']['resolution_seconds']:
                errors.append('wrong resolution')
            if item['failure'] is not None:
                errors.extend(failure_rollups.pair_errors(item['failure'], row, root))
            elif item['failure_availability'] != 'unavailable':
                errors.append('missing failure companion is unavailable')
            if item['failure'] is None and page['query_health']['status'] == 'available':
                errors.append('unavailable companion must degrade query health')
        else:
            errors.extend(request_observations.event_errors(row))
        for field in CONTRACT['filters']:
            expected = page['query'][field]
            if expected is None:
                continue
            actual = row['source_gateway_id'] if field == 'source_gateway_id' else row['attribution'].get(field)
            if field == 'gpu_resource_id':
                if expected not in (row['attribution']['gpu_resource_ids'] or []):
                    errors.append('row outside exact GPU filter')
            elif actual != expected:
                errors.append('row outside exact filter')
        for field in CONTRACT['selector_filters']:
            expected = page['query'][field]
            actual = row['lineage']['scope'] if field == 'lineage_scope' and kind == 'diagnostics' else row[field]
            if expected is not None and actual != expected:
                errors.append('row outside exact enum selector')
        try:
            start, end = utc(page['query']['start']), utc(page['query']['end'])
            row_start = request_observations.timestamp(row['window_start'] if kind == 'rollups' else row['observed_at'])
            row_end = request_observations.timestamp(row['window_end']) if kind == 'rollups' else row_start
            sort_key = (row_start, *key)
            if previous_sort_key is not None and sort_key <= previous_sort_key:
                errors.append('rows are not in strict canonical order')
            previous_sort_key = sort_key
            as_of = utc(page['as_of'])
            retention = timedelta(days=7 if kind == 'diagnostics' else 90)
            if not as_of - retention < row_end <= as_of:
                errors.append('row is expired or future at the server snapshot')
            if row_start < start or row_start >= end or row_end > end:
                errors.append('row outside requested window')
        except ValueError:
            errors.append('invalid row time')
        if len(json.dumps(row, separators=(',', ':'), ensure_ascii=False).encode()) > 65536:
            errors.append('nested row exceeds frozen bound')
    return errors


def contract_errors(root):
    errors = []
    contract_path = root / 'contracts/private-observability.json'
    if not contract_path.is_file():
        return ['private observability contract missing']
    contract = json.loads(contract_path.read_text())
    expected = {'defaults': {'enabled':False}, 'limits':CONTRACT['limits'],
                'retention':CONTRACT['retention'], 'authentication':CONTRACT['authentication'],
                'routes':CONTRACT['routes'], 'error_statuses':CONTRACT['error_statuses']}
    # Literal guards remain effective even when the loaded contract itself changes.
    if contract.get('limits', {}).get('event_bytes') != 65536 or contract.get('defaults', {}).get('enabled') is not False:
        errors.append('event bound or default-off invariant changed')
    if contract.get('retention', {}).get('diagnostic_days') != 7 or contract.get('retention', {}).get('aggregate_days') != 90:
        errors.append('retention invariant changed')
    if contract.get('authentication', {}).get('ingest_role') != 'gateway':
        errors.append('producer authority changed')
    for key, value in expected.items():
        if contract.get(key) != value:
            errors.append('private contract drift: ' + key)
    if errors:
        return errors
    required = ['openapi/private-observability.yaml', 'openapi/private-observability.md',
                'decisions/2026-10-20-private-observability-http.md',
                *['schemas/v1/observability/'+kind+'.json' for kind in ('ingest-result','error','rollups','diagnostics')]]
    for path in required:
        if not (root / path).is_file():
            errors.append('missing ' + path)
    if errors:
        return errors
    prose = (root / 'openapi/private-observability.md').read_text()
    table_codes = {code: int(status) for status, code in re.findall(r'\| (\d{3}) \| ([A-Z_]+) \|', prose)}
    if table_codes != contract['error_statuses']:
        errors.append('documented error status vocabulary drift')
    request_contract = json.loads((root / 'contracts/request-observation.json').read_text())
    selectors = {field: request_contract[key] for field, key in
                 [('dataset', 'datasets'), ('observation_kind', 'observation_kinds'), ('lineage_scope', 'lineage_scopes')]}
    if contract.get('selector_filters') != selectors:
        errors.append('selector vocabulary differs from frozen request contract')
    import yaml
    api = yaml.safe_load((root / contract['openapi']).read_text())
    expected_routes = set(contract['routes'].values())
    if set(api['paths']) != expected_routes:
        errors.append('OpenAPI route drift')
    for kind, path in contract['routes'].items():
        method = 'post' if kind == 'ingest' else 'get'
        operation = api['paths'].get(path, {}).get(method, {})
        auth = [{'NodeBearer':[], 'NodeIdentity':[]}] if kind == 'ingest' else [{'AdminHeader':[]}, {'AdminBearer':[]}]
        if operation.get('security') != auth:
            errors.append('OpenAPI auth drift')
        if kind != 'ingest':
            parameters = {item['name']: item for item in operation.get('parameters', [])}
            for field, values in selectors.items():
                if parameters.get(field, {}).get('schema', {}).get('enum') != values:
                    errors.append('OpenAPI selector vocabulary drift')
            schema = json.loads((root / ('schemas/v1/observability/' + kind + '.json')).read_text())
            query_schema = schema['properties']['query']
            for field, values in selectors.items():
                if field not in query_schema['required'] or query_schema['properties'].get(field) != {'anyOf': [{'enum': values}, {'type': 'null'}]}:
                    errors.append('normalized query selector vocabulary drift')
        for code in contract['error_statuses'].values():
            if str(code) not in operation.get('responses', {}):
                errors.append('OpenAPI status missing')
        for response in operation.get('responses', {}).values():
            if response.get('headers', {}).get('Cache-Control', {}).get('schema', {}).get('const') != 'private, no-store':
                errors.append('private cache policy missing')
    def refs(value):
        if isinstance(value, dict):
            ref = value.get('$ref')
            if ref and ref.startswith('../') and not (root / 'openapi' / ref).is_file():
                errors.append('unresolved OpenAPI ref: ' + ref)
            for item in value.values():
                refs(item)
        elif isinstance(value, list):
            for item in value:
                refs(item)
    refs(api)
    return errors
