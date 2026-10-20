"""Offline managed-node contract oracle. No runtime, cryptographic or hardware proof.

Case context represents independently authenticated owner state, never request fields.
The executable example validates the unchanged assignment schema before applying the
managed extension's bounds, ownership and publication predicates.
"""
import json
import math
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft7Validator, validators
import dynamic_nodes

CAPABILITIES = {'iw.dynamic-node/1', 'iw.node-reconcile/1'}
MAX_BYTES = 65536
MAX_REPORT_AGE_MS = 300000
CHECKS = {'artifact_integrity', 'device_isolation', 'runtime_attestation',
          'context_envelope', 'correctness', 'cancellation_reuse',
          'watchdog_recovery', 'authorized_admission'}
INTEGER = Draft7Validator.TYPE_CHECKER.redefine('integer', lambda _, value: type(value) is int)
StrictValidator = validators.extend(Draft7Validator, type_checker=INTEGER)


def decode(wire, maximum=MAX_BYTES):
    raw = wire.encode('utf-8') if isinstance(wire, str) else wire
    if len(raw) > maximum:
        raise ValueError('malformed')

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('malformed')
            result[key] = value
        return result

    def nonfinite(_):
        raise ValueError('malformed')

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('malformed')
        return result

    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=unique,
                          parse_constant=nonfinite, parse_float=finite_float)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('malformed') from error


@lru_cache(maxsize=16)
def validator(root, relative):
    import inspect
    store = {}
    for path in (root / 'schemas/v1').rglob('*.json'):
        document = json.loads(path.read_text())
        store[document['$id']] = document
    document = json.loads((root / relative).read_text())
    if 'registry' in inspect.signature(StrictValidator).parameters:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT7
        registry = Registry()
        for uri, item in store.items():
            registry = registry.with_resource(uri, Resource.from_contents(item, default_specification=DRAFT7))
        return StrictValidator(document, registry=registry)
    from jsonschema import RefResolver
    def no_network(uri):
        raise ValueError('unknown schema: ' + uri)
    resolver = RefResolver(document['$id'], document, store=store,
                           handlers={'https': no_network, 'http': no_network})
    return StrictValidator(document, resolver=resolver)


def valid(root, member, name):
    try:
        raw = json.dumps(member, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
        decode(raw)
        return not list(validator(root, 'schemas/v1/node-reconcile/' + name + '.json').iter_errors(member))
    except (ValueError, TypeError):
        return False


def durable_claims(status):
    """Stable claim content; health samples do not alter durable generation."""
    return sorted([{
        **{key: record[key] for key in ('assignmentId', 'deployment', 'phase', 'recovery')},
        'gpuIds': sorted(record['gpuIds']),
        'watchdogGeneration': record['watchdog']['generation'],
        'attestation': record.get('attestation'),
    } for record in status['records']], key=lambda claim: claim['assignmentId'])


def evaluate(root, case):
    """Return errors, executable assignment ids and publishable deployments.

    Structural/ownership errors reject this managed batch before executor translation.
    A valid hold can remain executable while qualification/publication is blocked.
    This is a decision oracle, not a runtime executor or an HTTP server.
    """
    facts, status, control, context = (case[key] for key in ('facts', 'status', 'control', 'context'))
    assignments = case['assignments']
    reasons = []
    result = {'reasons': reasons, 'execute': [], 'ready': []}

    def note(reason):
        if reason not in reasons:
            reasons.append(reason)

    for name, member in [('facts', facts), ('status', status), ('control', control)]:
        if not valid(root, member, name):
            note('malformed')
    if not isinstance(assignments, list) or len(assignments) > 8:
        note('malformed')
    else:
        for assignment in assignments:
            if list(validator(root, 'schemas/v1/requests/node-assignment.json').iter_errors(assignment)):
                note('malformed')
            elif dynamic_nodes.assignment_errors(assignment):
                note('assignment_mismatch')
    if reasons:
        return result
    if not CAPABILITIES.issubset(context['offered']) or not CAPABILITIES.issubset(context['accepted']):
        note('capability_missing')
    if not context['enrolled']:
        note('enrollment_required')
    if not context['ownerAuthenticated'] or control['ownerEpoch'] != context['ownerEpoch']:
        note('owner_untrusted')
    if control['policyId'] != context['policyId']:
        note('scope_denied')
    if any(a['kind'] != 'stop' and a['deployment'] not in context['allowedDeployments'] for a in assignments):
        note('scope_denied')
    if reasons:
        return result

    previous_generation = context.get('previousGeneration')
    if previous_generation is not None:
        if (status['generation'] < previous_generation or
                status['generation'] == previous_generation and
                durable_claims(status) != context['previousClaims']):
            note('assignment_mismatch')
    if reasons:
        return result

    cards = {}
    serials = set()
    for gpu in facts['gpus']:
        if gpu['gpuId'] in cards or gpu['serial'] in serials:
            note('duplicate_gpu')
        cards[gpu['gpuId']] = gpu
        serials.add(gpu['serial'])
        if 'computeCapability' in gpu and gpu['vendor'] != 'nvidia':
            note('incompatible_group')

    def claims(records, id_key):
        seen_ids, deployments, claimed_gpus = set(), set(), set()
        for record in records:
            if record[id_key] in seen_ids:
                note('duplicate_assignment')
            seen_ids.add(record[id_key])
            if record.get('kind') == 'stop' or record.get('phase') in ('stopped', 'failed'):
                continue
            if record['deployment'] in deployments:
                note('duplicate_deployment')
            deployments.add(record['deployment'])
            group = record['gpuIds']
            if len(set(group)) != len(group):
                note('duplicate_gpu')
            if claimed_gpus.intersection(group):
                note('gpu_overlap')
            claimed_gpus.update(group)
            if not set(group).issubset(cards):
                note('gpu_unknown')
                continue
            if len({(cards[g]['vendor'], cards[g]['model']) for g in group}) != 1:
                note('incompatible_group')
            if any(cards[g]['busy'] for g in group):
                note('gpu_busy')
    claims(assignments, 'id')
    claims(status['records'], 'assignmentId')
    desired = {a['id']: a for a in assignments if a['kind'] != 'stop'}
    held = {r['assignmentId']: r for r in status['records'] if r['phase'] not in ('stopped', 'failed')}
    for assignment in desired.values():
        # One identity namespace covers previously held and newly desired assignments.
        for previous in held.values():
            if assignment['id'] != previous['assignmentId']:
                if assignment['deployment'] == previous['deployment']:
                    note('duplicate_deployment')
                if set(assignment['gpuIds']).intersection(previous['gpuIds']):
                    note('gpu_overlap')
            elif (assignment['deployment'] != previous['deployment'] or
                  set(assignment['gpuIds']) != set(previous['gpuIds'])):
                note('assignment_mismatch')
        group = [cards[g] for g in assignment['gpuIds'] if g in cards]
        profile = assignment.get('profile', assignment.get('candidate'))
        match = profile['match']
        if any(g['vendor'] != match['gpu']['vendor'] or g['model'] not in match['gpu']['model'] or
               g['vramMib'] < match['gpu']['vramMibMin'] for g in group):
            note('profile_mismatch')
        if (facts['host']['ramGib'] < match['host']['ramGibMin'] or
                any(g['pcieGen'] < match['host']['pcieGenMin'] for g in group)):
            note('profile_mismatch')
    if reasons:
        return result
    blocked = set()
    # Terminal observations release occupancy, not their persisted rescue budget.
    for record in status['records']:
        if record['phase'] == 'quarantined' or record['watchdog']['state'] == 'quarantined':
            blocked.add(record['assignmentId'])
            note('quarantined')
        if record['recovery']['attempts'] >= record['recovery']['limit']:
            blocked.add(record['assignmentId'])
            note('recovery_exhausted')
    result['execute'] = [a['id'] for a in assignments if a['kind'] == 'stop' or a['id'] not in blocked]

    if context['reportAgeMs'] >= MAX_REPORT_AGE_MS or context['reportAgeMs'] < 0:
        note('status_stale')
    binding = ('nodeId', 'ownerEpoch', 'policyId', 'scopeId', 'assignmentId',
               'deployment', 'gpuIds', 'environmentFingerprint')
    permit_ids = set()
    for permit in control['permits']:
        current = next((p for p in context['permits'] if p['permit']['permitId'] == permit['permitId']), None)
        record = held.get(permit['assignmentId'])
        if (permit['permitId'] in permit_ids or current is None or current['permit'] != permit or
                current['usedRequests'] >= permit['maxRequests'] or
                not permit['issuedAt'] <= context['now'] < permit['expiresAt'] or
                permit['expiresAt'] - permit['issuedAt'] > 300 or
                permit['nodeId'] != context['nodeId'] or permit['ownerEpoch'] != context['ownerEpoch'] or
                permit['policyId'] != control['policyId'] or permit['scopeId'] not in context['qualificationScopes'] or
                record is None or record['deployment'] != permit['deployment'] or
                set(record['gpuIds']) != set(permit['gpuIds']) or
                record.get('attestation', {}).get('environmentFingerprint') != permit['environmentFingerprint'] or
                record['phase'] != 'qualifying' or record['watchdog']['state'] != 'active' or
                record['recovery']['attempts'] >= record['recovery']['limit']):
            note('permit_denied')
        permit_ids.add(permit['permitId'])

    grant_ids = set()
    for grant in control['qualifications']:
        if grant['assignmentId'] in grant_ids:
            note('duplicate_assignment')
        grant_ids.add(grant['assignmentId'])
        record = held.get(grant['assignmentId'])
        evidence = next((e for e in context['evidence'] if e['evidenceId'] == grant['evidenceId']), None)
        if evidence is None or any(evidence.get(k) != grant[k] for k in binding):
            note('qualification_missing')
        elif (not CHECKS.issubset(evidence['checks']) or
                evidence['authorizationProbeId'] != grant['authorizationProbeId'] or
                evidence['watchdogGeneration'] != grant['watchdogGeneration']):
            note('qualification_missing')
        if (grant['validUntil'] <= context['now'] or
                evidence is not None and (evidence['validUntil'] <= context['now'] or grant['validUntil'] > evidence['validUntil'])):
            note('qualification_stale')
        if (grant['nodeId'] != context['nodeId'] or grant['ownerEpoch'] != context['ownerEpoch'] or
                grant['policyId'] != control['policyId'] or grant['scopeId'] not in context['servingScopes']):
            note('scope_denied')
        if record is None:
            note('assignment_mismatch')
            continue
        if record['deployment'] != grant['deployment'] or set(record['gpuIds']) != set(grant['gpuIds']):
            note('assignment_mismatch')
        if record['phase'] == 'quarantined' or record['watchdog']['state'] == 'quarantined':
            note('quarantined')
        elif record['phase'] != 'serving' or record['health'] != 'healthy':
            note('requalification_required')
        if record['watchdog']['state'] != 'active' or record['watchdog']['generation'] != grant['watchdogGeneration']:
            note('watchdog_inactive')
        if record['recovery']['attempts'] >= record['recovery']['limit']:
            note('recovery_exhausted')
        attested = record.get('attestation')
        if attested is None:
            note('attestation_missing')
        elif (attested['environmentFingerprint'] != grant['environmentFingerprint'] or
                evidence is not None and (attested['imageDigest'] != evidence['imageDigest'] or
                                          attested['effectiveConfigDigest'] != evidence['effectiveConfigDigest'])):
            note('fingerprint_mismatch')
        assignment = desired.get(grant['assignmentId'])
        if assignment is not None:
            profile = assignment.get('profile', assignment.get('candidate'))
            if attested is not None and profile['launch'].get('digest') != attested['imageDigest']:
                note('fingerprint_mismatch')
    if not reasons:
        result['ready'] = sorted({g['deployment'] for g in control['qualifications']})
    return result


def contract_errors(root):
    contract = json.loads((root / 'contracts/node-reconcile.json').read_text())
    errors = []
    status = json.loads((root / 'schemas/v1/node-reconcile/status.json').read_text())
    record = status['properties']['records']['items']['properties']
    if contract['status_phase'] != record['phase']['enum']:
        errors.append('node reconciliation phase vocabulary drift')
    if contract['reason_codes'] != record['reason']['enum']:
        errors.append('node reconciliation reason vocabulary drift')
    if set(contract['required_checks']) != CHECKS or set(contract['required_capabilities']) != CAPABILITIES:
        errors.append('node reconciliation gate vocabulary drift')
    control = json.loads((root / 'schemas/v1/node-reconcile/control.json').read_text())
    permit = json.loads((root / 'schemas/v1/node-reconcile/permit.json').read_text())
    embedded = control['properties']['permits']['items']
    if embedded != {k: v for k, v in permit.items() if not k.startswith('$') and k != 'title'}:
        errors.append('node reconciliation permit schema drift')
    for path in (root / 'schemas/v1/node-reconcile').glob('*.json'):
        Draft7Validator.check_schema(json.loads(path.read_text()))
    vectors = json.loads((root / 'conformance/node-reconcile-vectors.json').read_text())
    declared = set()
    for vector in vectors['cases']:
        path = root / vector['path']
        declared.add(path)
        try:
            case = decode(path.read_bytes(), maximum=1048576)
            actual = evaluate(root, case)
        except (ValueError, KeyError, TypeError):
            actual = {'reasons': ['malformed'], 'execute': [], 'ready': []}
        if (set(actual['reasons']) != set(vector['reasons']) or len(actual['ready']) != vector['readyCount'] or
                len(actual['execute']) != vector['executeCount']):
            errors.append(vector['id'] + ': unexpected decision ' + json.dumps(actual))
    found = set((root / 'fixtures/node-reconcile').glob('*/*.json'))
    if found != declared:
        errors.append('node reconciliation fixture manifest differs from files')
    return errors


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    failures = contract_errors(root)
    for failure in failures:
        print('FAIL node reconciliation:', failure)
    if not failures:
        print('PASS node reconciliation contract and fixture oracle; live runtime/host proof: NOT RUN')
    raise SystemExit(bool(failures))
