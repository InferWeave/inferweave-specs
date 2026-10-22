"""Executable additive failure-companion contract; no storage/runtime proof."""
import hashlib
import json
from decimal import Decimal

import request_observations as observations


MAX_INTEGER = observations.MAX_INTEGER


def checked_sum(values):
    total = 0
    for value in values:
        if type(value) is not int or not 0 <= value <= MAX_INTEGER - total:
            raise ValueError('nonnegative safe integer addition overflow or invalid operand')
        total += value
    return total


def require_canonical_types(value):
    if isinstance(value, dict):
        for key, item in value.items():
            require_canonical_types(key)
            require_canonical_types(item)
    elif isinstance(value, list):
        for item in value:
            require_canonical_types(item)
    elif isinstance(value, str):
        try:
            value.encode('utf-8')
        except UnicodeEncodeError as error:
            raise ValueError('unpaired Unicode surrogate') from error
    elif type(value) is int:
        checked_sum([value])
    elif value is not None and type(value) is not bool:
        raise ValueError('canonical wire permits only safe integer JSON numbers')


def bounded_utf8(wire):
    raw = wire if isinstance(wire, bytes) else wire.encode('utf-8')
    if len(raw) > 65536:
        raise ValueError('observation exceeds 64 KiB')
    return raw.decode('utf-8', errors='strict')


def decode(wire):
    value = observations.decode(bounded_utf8(wire))
    require_canonical_types(value)
    return value


def normalize_parent(value):
    """Normalize mathematical integers; wire callers must use decode_parent first."""
    if isinstance(value, dict):
        return {key: normalize_parent(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_parent(item) for item in value]
    if isinstance(value, (float, Decimal)):
        # Check range before int conversion, including enormous exponent spellings.
        if isinstance(value, Decimal) and not value.is_finite():
            raise ValueError('nonfinite parent number')
        if not 0 <= value <= MAX_INTEGER or value != int(value):
            raise ValueError('parent number is not an exact nonnegative safe integer')
        return int(value)
    require_canonical_types(value)
    return value


def decode_parent(wire):
    text = bounded_utf8(wire)
    # Reuse recursive duplicate/nonfinite checks, then preserve exact numeric text.
    # The first parse's binary-float values are never used for canonicalization.
    observations.decode(text)
    return normalize_parent(json.loads(text, parse_int=Decimal, parse_float=Decimal))


def canonical_parent(parent):
    """iw-parent-canonical-json/1: scalar-key order, compact UTF-8, integer numbers."""
    parent = normalize_parent(parent)
    require_canonical_types(parent)
    return json.dumps(parent, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def parent_fingerprint(parent):
    return 'sha256:' + hashlib.sha256(canonical_parent(parent).encode('utf-8')).hexdigest()


def semantic_errors(row, parent, contract):
    errors = []
    reference = row['parent']
    for key in ('source_gateway_id', 'producer_epoch', 'rollup_id', 'revision', 'sealed'):
        if reference[key] != parent[key]:
            errors.append('failure companion parent ' + key + ' mismatch')
    if reference['fingerprint'] != parent_fingerprint(parent):
        errors.append('failure companion canonical parent fingerprint mismatch')
    try:
        checked_sum(parent['counts'][status] for status in contract['statuses'])
        for status in contract['failure_rollup']['statuses']:
            breakdown = row['breakdowns'][status]
            for axis in ('reason_counts', 'layer_counts', 'phase_counts'):
                if checked_sum(breakdown[axis].values()) != parent['counts'][status]:
                    errors.append(status + ' ' + axis + ' does not conserve parent status count')
            table = breakdown['timeout_phase_counts']
            for reason, phases in table.items():
                if checked_sum(phases.values()) != breakdown['reason_counts'][reason]:
                    errors.append(status + ' timeout phase row does not conserve reason count')
            for phase, marginal in breakdown['phase_counts'].items():
                if checked_sum(phases[phase] for phases in table.values()) > marginal:
                    errors.append(status + ' timeout phase column exceeds phase marginal')
    except ValueError as error:
        errors.append(str(error))
    return errors


def pair_errors(row, parent, root):
    """Validate both bounded payloads before checking exact-parent conservation."""
    from jsonschema import Draft7Validator, FormatChecker, RefResolver
    if row is None or parent is None:
        return ['failure companion unavailable: exact parent and companion are required']
    try:
        parent = normalize_parent(parent)
        require_canonical_types(row)
    except ValueError as error:
        return [str(error)]
    contract = json.loads((root / 'contracts/request-observation.json').read_text())
    schemas = {key: json.loads((root / contract[key]).read_text()) for key in ('event_schema', 'rollup_schema', 'failure_rollup_schema')}
    store = {schema['$id']: schema for schema in schemas.values()}
    errors = []
    for key, value in [('rollup_schema', parent), ('failure_rollup_schema', row)]:
        try:
            decode(canonical_parent(value))
        except ValueError as error:
            errors.append(str(error))
            continue
        schema = schemas[key]
        validator = Draft7Validator(schema, resolver=RefResolver(base_uri=schema['$id'], referrer=schema, store=store), format_checker=FormatChecker())
        errors.extend(error.message for error in validator.iter_errors(value))
    if errors:
        return errors
    errors.extend(observations.rollup_errors(parent, contract))
    errors.extend(semantic_errors(row, parent, contract))
    return errors


def count_breakdowns(events, contract):
    """Offline mapping example: traces never contribute to aggregate counts."""
    vocab = contract['failure_rollup']
    result = {status: {
        'reason_counts': dict.fromkeys(vocab['reason_codes'], 0),
        'layer_counts': dict.fromkeys(vocab['layers'], 0),
        'phase_counts': dict.fromkeys(vocab['phases'], 0),
        'timeout_phase_counts': {reason: dict.fromkeys(vocab['phases'], 0) for reason in vocab['timeout_reason_codes']},
    } for status in vocab['statuses']}
    unique, _ = observations.deduplicate(events)
    for event in unique:
        if event['sampling'] != 'all_terminal' or event['outcome']['status'] == 'success':
            continue
        outcome = event['outcome']
        target = result[outcome['status']]
        for axis, field in [('reason_counts', 'reason_code'), ('layer_counts', 'layer'), ('phase_counts', 'phase')]:
            target[axis][outcome[field]] = checked_sum([target[axis][outcome[field]], 1])
        if outcome['reason_code'] in vocab['timeout_reason_codes']:
            phases = target['timeout_phase_counts'][outcome['reason_code']]
            phases[outcome['phase']] = checked_sum([phases[outcome['phase']], 1])
    return result


def contract_errors(root):
    from jsonschema import Draft7Validator
    contract = json.loads((root / 'contracts/request-observation.json').read_text())
    schema = json.loads((root / contract['failure_rollup_schema']).read_text())
    event = json.loads((root / contract['event_schema']).read_text())
    Draft7Validator.check_schema(schema)
    errors = []
    vocab = contract['failure_rollup']
    outcome = event['properties']['outcome']['properties']
    maps = schema['definitions']['breakdown']['properties']
    expected = {'reason_codes': [code for code in outcome['reason_code']['enum'] if code != 'none'],
                'layers': outcome['layer']['enum'], 'phases': outcome['phase']['enum']}
    for name, axis in [('reason_codes', 'reason_counts'), ('layers', 'layer_counts'), ('phases', 'phase_counts')]:
        if vocab[name] != expected[name] or list(maps[axis]['properties']) != expected[name] or maps[axis]['required'] != expected[name]:
            errors.append('failure companion vocabulary drift: ' + name)
    statuses = contract['statuses'][1:]
    if vocab['statuses'] != statuses or list(schema['properties']['breakdowns']['properties']) != statuses:
        errors.append('failure companion status vocabulary drift')
    timeout_reasons = ['DEADLINE_EXCEEDED', 'BACKEND_TIMEOUT', 'inference_idle_timeout', 'inference_request_timeout']
    table = maps['timeout_phase_counts']
    if vocab['timeout_reason_codes'] != timeout_reasons or list(table['properties']) != timeout_reasons or table['required'] != timeout_reasons:
        errors.append('failure companion timeout vocabulary drift')
    for phases in table['properties'].values():
        if list(phases['properties']) != expected['phases'] or phases['required'] != expected['phases']:
            errors.append('failure companion timeout phase vocabulary drift')
    parent = decode_parent((root / 'fixtures/valid/request-observation-rollup-failures.json').read_bytes())
    for kind in ('valid', 'invalid'):
        for path in (root / 'fixtures' / kind).glob('request-observation-failure-rollup*.json'):
            try:
                failures = pair_errors(decode(path.read_bytes()), parent, root)
            except ValueError as error:
                failures = [str(error)]
            if bool(failures) != (kind == 'invalid'):
                errors.append(str(path.relative_to(root)) + ': unexpected failure companion validation result')
    vectors = json.loads((root / 'conformance/request-observation-failure-rollup-vectors.json').read_text())
    row = json.loads((root / 'fixtures/valid/request-observation-failure-rollup.json').read_text())
    if vectors['parent_fingerprint'] != parent_fingerprint(parent):
        errors.append('failure companion fingerprint vector drift')
    if count_breakdowns(vectors['events'], contract) != row['breakdowns']:
        errors.append('failure companion all-terminal/dedup mapping vector drift')
    return errors
