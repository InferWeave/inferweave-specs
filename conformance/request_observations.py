"""Executable internal observation examples; runtime/persistence proof remains owed."""
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import json

from observability_capacity import decode as strict_decode

MAX_INTEGER = 9007199254740991
PHASE_SEMANTICS = json.loads((Path(__file__).resolve().parents[1] / "contracts/request-observation.json").read_text())["phase_semantics"]


def decode(wire):
    if len(wire if isinstance(wire, bytes) else wire.encode('utf-8')) > 65536:
        raise ValueError('observation exceeds 64 KiB')
    return strict_decode(wire)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def attribution_errors(attrs):
    if attrs['gpu_resource_ids'] is not None and attrs['gpu_count'] is not None and len(attrs['gpu_resource_ids']) != attrs['gpu_count']:
        return ['GPU count disagrees with the exact attributed resource set']
    return []


def event_errors(event):
    errors = []
    lineage = event['lineage']
    kind = event['observation_kind']
    if lineage['scope'] == 'trusted':
        if not lineage['logical_request_id'] or not lineage['ingress_gateway_id']:
            errors.append('trusted lineage needs ingress owner and logical request identity')
        if kind == 'ingress_terminal' and lineage['ingress_gateway_id'] != event['source_gateway_id']:
            errors.append('only the ingress owner emits its terminal ingress outcome')
        if kind in ('attempt_terminal', 'hop_terminal') and not lineage['attempt_id']:
            errors.append('attempt or hop requires its own attempt identity')
        if kind == 'hop_terminal' and not lineage['hop_id']:
            errors.append('forward hop requires hop identity')
    elif any(lineage[key] is not None for key in ('logical_request_id', 'ingress_gateway_id', 'parent_attempt_id', 'parent_hop_id')):
        errors.append('unlinked lineage cannot claim global request ownership or parentage')
    if (event['dataset'] == 'controlled') != (event['benchmark_sample_id'] is not None):
        errors.append('controlled data requires a benchmark sample identity, other datasets forbid it')
    result = event['outcome']
    status, completion = result['status'], result['completion']
    if status == 'success' and (completion != 'protocol_success' or result['reason_code'] != 'none'):
        errors.append('success needs protocol completion and no failure reason')
    if completion == 'protocol_success' and status != 'success':
        errors.append('protocol success conflicts with terminal status')
    if status == 'success' and result['http_status'] is not None and not 200 <= result['http_status'] < 300:
        errors.append('HTTP error cannot establish request success')
    expected = {'cancelled': 'cancelled', 'rejected': 'pre_execution_rejected', 'unknown': 'unobserved'}
    if status in expected and completion != expected[status]:
        errors.append('terminal status and completion evidence disagree')
    if status != 'success' and result['reason_code'] == 'none':
        errors.append('non-success needs a finite reason or explicit unknown')
    if status == 'service_failure' and completion not in ('protocol_failure', 'unobserved'):
        errors.append('service failure needs failed or unobserved protocol completion')
    errors.extend(attribution_errors(event['attribution']))
    ids, phases = set(), set()
    parents = {}
    for span in event['timings']:
        if span['span_id'] in ids or span['phase'] in phases:
            errors.append('duplicate timing span or phase')
        ids.add(span['span_id'])
        phases.add(span['phase'])
        parents[span['span_id']] = span['parent_span_id']
        if span['semantics'] != PHASE_SEMANTICS[span['phase']]:
            errors.append('timing semantics differs from frozen phase definition')
        quantity = span['measurement']
        if 'value' in quantity:
            if span['clock'] == 'unknown':
                errors.append('known timing requires a monotonic clock domain')
            if span['phase'] in ('engine_prefill', 'engine_decode', 'engine_execution'):
                if quantity['source'] != 'engine_reported' or span['clock'] != 'producer_monotonic' or span['semantics'] != 'interval' or quantity['basis'] != 'measured':
                    errors.append('engine timing requires actual engine monotonic interval evidence')
            if quantity['source'] == 'http_first_token_proxy' and (span['phase'] != 'first_useful_output' or span['semantics'] != 'offset_from_start'):
                errors.append('HTTP first-token proxy cannot claim another phase')
            if quantity['source'] not in ('local_monotonic', 'engine_reported', 'http_first_token_proxy'):
                errors.append('timing has non-timing provenance')
        current, visited = span['span_id'], set()
        while current is not None and current in parents:
            if current in visited:
                errors.append('cyclic timing parents')
                break
            visited.add(current)
            current = parents[current]
    if any(parent is not None and parent not in ids for parent in parents.values()):
        errors.append('timing parent is outside this event')
    for quantity in event['tokens'].values():
        if 'value' in quantity and quantity['source'] not in ('runtime_usage', 'tokenizer', 'configuration'):
            errors.append('token count has non-token provenance')
    for subset, total in [('cached_input', 'input_total'), ('decode_output_tokens', 'output_total')]:
        left, right = event['tokens'][subset].get('value'), event['tokens'][total].get('value')
        if left is not None and right is not None and left > right:
            errors.append('token subset exceeds its reported total')
    return errors


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def rollup_errors(row, contract):
    errors = []
    start, end = timestamp(row['window_start']), timestamp(row['window_end'])
    interval = timedelta(seconds=row['resolution_seconds'])
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    milliseconds = row['resolution_seconds'] * 1000
    if end - start != interval or (start - epoch) % interval != timedelta(0):
        errors.append('rollup window is not the declared UTC grid interval')
    if any(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', row[key]) is None for key in ('window_start', 'window_end')):
        errors.append('rollup boundaries require canonical whole-second UTC timestamps')
    errors.extend(attribution_errors(row['attribution']))
    if timestamp(row['as_of']) < end:
        errors.append('rollup as_of precedes its window end')
    counts = row['counts']
    if sum(counts[k] for k in contract['statuses']) != counts['total']:
        errors.append('terminal outcome counts do not conserve total')
    expected_ratios = {
        'success_share': {'numerator': counts['success'], 'denominator': counts['total'] - counts['unknown']},
        'service_failure_rate': {'numerator': counts['service_failure'], 'denominator': counts['success'] + counts['service_failure']},
    }
    if row['ratios'] != expected_ratios:
        errors.append('ratio numerator/denominator differs from frozen outcome policy')
    metric_keys, eligibility = set(), {}
    for metric in row['metrics']:
        key = (metric['metric'], metric['basis'], metric['source'])
        if key in metric_keys:
            errors.append('duplicate metric provenance cohort')
        metric_keys.add(key)
        eligibility[metric['metric']] = eligibility.get(metric['metric'], 0) + metric['eligible_count']
        unit = 'milliseconds' if metric['metric'].endswith('_ms') else 'tokens'
        if metric['unit'] != unit:
            errors.append('metric unit disagrees with definition')
        bounds = contract['histograms'][unit]
        histogram = metric['histogram']
        if histogram['bounds'] != bounds or len(histogram['counts']) != len(bounds) + 1:
            errors.append('histogram boundaries differ from frozen version')
            continue
        if sum(histogram['counts']) != metric['known_count']:
            errors.append('histogram counts differ from known samples')
        if metric['eligible_count'] != metric['known_count'] + metric['missing_count'] + metric['unsupported_count']:
            errors.append('metric eligible count loses missing or unsupported samples')
        if metric['basis'] in ('unknown', 'unsupported') and metric['known_count']:
            errors.append('unknown or unsupported basis has known samples')
        lower = [0] + [x + 1 for x in bounds]
        upper = bounds + [MAX_INTEGER]
        if not sum(n * b for n, b in zip(histogram['counts'], lower)) <= metric['sum'] <= sum(n * b for n, b in zip(histogram['counts'], upper)):
            errors.append('sum is inconsistent with histogram intervals')
        if metric['known_count']:
            allowed = ('runtime_usage', 'tokenizer', 'configuration') if unit == 'tokens' else ('local_monotonic', 'engine_reported', 'http_first_token_proxy')
            if metric['source'] not in allowed:
                errors.append('known metric has incompatible measurement source')
            if metric['source'] == 'http_first_token_proxy' and metric['metric'] != 'first_useful_output_ms':
                errors.append('proxy timing used as another rollup phase')
        if metric['metric'] in ('engine_prefill_ms', 'engine_decode_ms', 'engine_execution_ms') and metric['known_count'] and (metric['source'] != 'engine_reported' or metric['basis'] != 'measured'):
            errors.append('engine rollup contains non-engine timing')
    if any(value != counts['total'] for value in eligibility.values()):
        errors.append('metric provenance rows do not partition terminal observations')
    coverage = row['coverage']
    if coverage['covered_ms'] + coverage['unknown_ms'] != milliseconds:
        errors.append('coverage does not partition the window')
    if coverage['accepted_events'] != counts['total']:
        errors.append('accepted coverage count differs from rollup total')
    if coverage['expected_events'] is not None and coverage['expected_events'] < coverage['accepted_events']:
        errors.append('expected event count is below accepted count')
    if coverage['status'] == 'complete':
        if coverage['unknown_ms'] or coverage['expected_events'] != counts['total'] or any(coverage[k] != 0 for k in ('dropped_events', 'write_failures', 'replay_conflicts', 'late_events_rejected')):
            errors.append('complete coverage lacks loss-free expected-event evidence')
    return errors


def deduplicate(events):
    seen, terminal_keys, duplicates = {}, {}, 0
    for event in events:
        key = tuple(event[k] for k in ('source_gateway_id', 'producer_epoch', 'event_id'))
        if key in seen:
            if canonical(seen[key]) != canonical(event):
                raise ValueError('conflicting replay identity')
            duplicates += 1
        else:
            if event['lineage']['scope'] == 'trusted' and event['sampling'] == 'all_terminal':
                field = {'ingress_terminal': 'logical_request_id', 'attempt_terminal': 'attempt_id', 'hop_terminal': 'hop_id'}[event['observation_kind']]
                terminal_key = (event['observation_kind'], event['source_gateway_id'], event['lineage'][field])
                if terminal_key in terminal_keys:
                    raise ValueError('second event identity for the same terminal fact')
                terminal_keys[terminal_key] = key
            seen[key] = event
    return list(seen.values()), duplicates


def merge_metrics(left, right):
    for key in ('metric', 'unit', 'basis', 'source'):
        if left[key] != right[key]:
            raise ValueError('incompatible metric provenance')
    if left['histogram']['version'] != right['histogram']['version'] or left['histogram']['bounds'] != right['histogram']['bounds']:
        raise ValueError('incompatible histogram')
    result = copy.deepcopy(left)
    for key in ('eligible_count', 'known_count', 'missing_count', 'unsupported_count', 'sum'):
        result[key] += right[key]
        if result[key] > MAX_INTEGER:
            raise ValueError('integer overflow')
    result['histogram']['counts'] = [a + b for a, b in zip(left['histogram']['counts'], right['histogram']['counts'])]
    if any(n > MAX_INTEGER for n in result['histogram']['counts']):
        raise ValueError('histogram overflow')
    return result


def require_mergeable(left, right):
    for key in ('source_gateway_id', 'producer_epoch', 'metric_definition_version', 'dataset', 'observation_kind', 'lineage_scope', 'attribution'):
        if left[key] != right[key]:
            raise ValueError('incompatible rollup dimensions')
    if left['coverage']['counter_epoch'] != right['coverage']['counter_epoch']:
        raise ValueError('counter reset boundary')
    if not (timestamp(left['window_end']) <= timestamp(right['window_start']) or timestamp(right['window_end']) <= timestamp(left['window_start'])):
        raise ValueError('overlapping rollup windows')


def replace_rollups(rows):
    stored = {}
    for row in rows:
        key = tuple(row[k] for k in ('source_gateway_id', 'producer_epoch', 'rollup_id'))
        prior = stored.get(key)
        if prior:
            if row['revision'] < prior['revision']:
                continue
            if row['revision'] == prior['revision']:
                if canonical(row) != canonical(prior):
                    raise ValueError('conflicting rollup revision')
                continue
            if row['coverage']['counter_epoch'] != prior['coverage']['counter_epoch']:
                raise ValueError('rollup revision changes counter epoch')
            for field in ('window_start', 'window_end', 'resolution_seconds', 'dataset', 'observation_kind', 'lineage_scope', 'attribution', 'metric_definition_version'):
                if row[field] != prior[field]:
                    raise ValueError('rollup revision changes its immutable dimensions')
            if timestamp(row['as_of']) < timestamp(prior['as_of']):
                raise ValueError('rollup revision moves as_of backwards')
            if prior['sealed']:
                raise ValueError('cannot revise sealed rollup')
        stored[key] = row
    return list(stored.values())


def contract_errors(root):
    from jsonschema import Draft7Validator, FormatChecker, RefResolver
    contract = json.loads((root / 'contracts/request-observation.json').read_text())
    schemas = {key: json.loads((root / contract[key]).read_text()) for key in ('event_schema', 'rollup_schema')}
    store = {schema['$id']: schema for schema in schemas.values()}
    errors = []
    event = schemas['event_schema']
    pairs = [('datasets', event['properties']['dataset']['enum']), ('observation_kinds', event['properties']['observation_kind']['enum']), ('lineage_scopes', event['properties']['lineage']['properties']['scope']['enum']), ('statuses', event['properties']['outcome']['properties']['status']['enum']), ('basis', event['definitions']['quantity']['properties']['basis']['enum']), ('measurement_sources', event['definitions']['quantity']['properties']['source']['enum']), ('phases', event['properties']['timings']['items']['properties']['phase']['enum']), ('token_fields', list(event['properties']['tokens']['properties']))]
    for name, values in pairs:
        if contract[name] != values:
            errors.append('request observation vocabulary drift: ' + name)
    if schemas['rollup_schema']['properties']['metrics']['items']['properties']['metric']['enum'] != contract['metric_names']:
        errors.append('request observation metric names drifted')
    if contract['phase_semantics'] != PHASE_SEMANTICS or set(PHASE_SEMANTICS) != set(contract['phases']):
        errors.append('phase semantics vocabulary drift')
    schema_semantics = {rule['if']['properties']['phase']['const']: rule['then']['properties']['semantics']['const'] for rule in event['properties']['timings']['items']['allOf']}
    if schema_semantics != PHASE_SEMANTICS:
        errors.append('phase semantics schema drift')
    codes = ['none', 'unknown']
    for source in contract['reason_code_sources']:
        codes.extend(c for c in json.loads((root / source['path']).read_text())[source['key']] if c not in codes)
    if event['properties']['outcome']['properties']['reason_code']['enum'] != codes:
        errors.append('request observation failure codes drifted from canonical vocabularies')
    validators = {}
    for key, schema in schemas.items():
        Draft7Validator.check_schema(schema)
        validators[key] = Draft7Validator(schema, resolver=RefResolver(base_uri=schema['$id'], referrer=schema, store=store), format_checker=FormatChecker())
    for kind in ('valid', 'invalid'):
        for path in (root / 'fixtures' / kind).glob('request-observation*.json'):
            if path.stem.startswith('request-observation-failure-rollup'):
                continue
            try:
                value = decode(path.read_bytes())
                is_rollup = path.stem.startswith('request-observation-rollup')
                failures = list(validators['rollup_schema' if is_rollup else 'event_schema'].iter_errors(value))
                if not failures:
                    failures = rollup_errors(value, contract) if is_rollup else event_errors(value)
            except (ValueError, UnicodeDecodeError) as error:
                failures = [str(error)]
            if bool(failures) != (kind == 'invalid'):
                errors.append(str(path.relative_to(root)) + ': unexpected validation result')
    vectors = json.loads((root / 'conformance/request-observation-vectors.json').read_text())
    for value in vectors['events'] + [vectors['conflicting_replay']]:
        errors.extend(str(e.message) for e in validators['event_schema'].iter_errors(value))
        errors.extend(event_errors(value))
    unique, duplicates = deduplicate(vectors['events'])
    counted = [e for e in unique if e['sampling'] == 'all_terminal']
    actual = {'unique_events': len(unique), 'duplicates': duplicates,
              'trusted_ingress_success': sum(e['observation_kind'] == 'ingress_terminal' and e['lineage']['scope'] == 'trusted' and e['outcome']['status'] == 'success' for e in counted),
              'attempt_service_failure': sum(e['observation_kind'] == 'attempt_terminal' and e['outcome']['status'] == 'service_failure' for e in counted),
              'attempt_success': sum(e['observation_kind'] == 'attempt_terminal' and e['outcome']['status'] == 'success' for e in counted),
              'hops': sum(e['observation_kind'] == 'hop_terminal' for e in counted)}
    if actual != vectors['expected']:
        errors.append('request observation replay/lineage vectors disagree')
    try:
        deduplicate(vectors['events'] + [vectors['conflicting_replay']])
        errors.append('conflicting event replay was accepted')
    except ValueError:
        pass
    if sum(r['counts']['total'] for r in replace_rollups(vectors['rollups'])) != vectors['expected_rollup_total_after_replay']:
        errors.append('rollup replay added counts twice')
    import failure_rollups
    errors.extend(failure_rollups.contract_errors(root))
    return errors
