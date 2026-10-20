"""Read-only capacity contract checks; no admission or runtime proof is implied."""
import json
from pathlib import Path


def decode(wire):
    """Reject duplicate object keys recursively before any capacity schema check."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON object key: ' + key)
            result[key] = value
        return result
    return json.loads(wire, object_pairs_hook=unique_object)


def pool_errors(nodes):
    errors = []
    pools = {}
    for node in nodes:
        for offer in node['serving_offers']:
            pool = offer['capacity_pool_id']
            authority = (node['owner_gateway_id'], offer['owner_epoch'])
            if pool in pools and pools[pool] != authority:
                errors.append('capacity pool binds mixed owners or epochs')
            pools[pool] = authority
    return errors


def semantic_errors(snapshot):
    errors = []
    if snapshot['status'] == 'fresh' and snapshot['received_age_ms'] >= snapshot['validity_ms']:
        errors.append('fresh snapshot has exhausted its validity')
    cpu = snapshot['cpu']
    value = lambda name: cpu[name].get('value')
    budget, reserve, available = map(value, ['owner_budget_millicores', 'reserved_millicores', 'available_millicores'])
    affinity, quota = map(value, ['affinity_logical_cpus', 'quota_millicores'])
    if budget is not None:
        if affinity is not None and budget > affinity * 1000:
            errors.append('owner CPU budget exceeds affinity')
        if quota is not None and budget > quota:
            errors.append('owner CPU budget exceeds quota')
    if available is not None:
        unlimited = cpu['quota_millicores']['basis'] == 'unsupported' and cpu['quota_millicores']['source'] == 'cgroup_unlimited'
        if None in (budget, reserve, affinity) or (quota is None and not unlimited):
            errors.append('available CPU requires known entitlement and reserves')
        elif available != max(0, budget - reserve):
            errors.append('available CPU differs from owner budget minus held reserves')
    seen = set()
    for offer in snapshot['serving_offers']:
        if offer['offer_id'] in seen:
            errors.append('duplicate offer_id')
        seen.add(offer['offer_id'])
        if offer['max_output_tokens'] > offer['requested_context_tokens']:
            errors.append('output allowance exceeds total context')
        if offer['status'] == 'fresh' and offer['valid_for_ms'] <= 0:
            errors.append('fresh offer requires positive validity')
        if offer['valid_for_ms'] > max(0, snapshot['validity_ms'] - snapshot['received_age_ms']):
            errors.append('offer outlives its snapshot')
        if offer['additional_requests']['basis'] != offer['basis']:
            errors.append('offer basis disagrees with its request estimate')
        if offer['additional_requests'].get('value', 0) > 0 and offer['exclusion_reasons']:
            errors.append('excluded offer advertises positive additional requests')
    errors.extend(pool_errors([snapshot]))
    return errors


def contract_errors(root):
    from jsonschema import Draft7Validator, FormatChecker, RefResolver
    schema_path = root / 'schemas/v1/resources/observability-capacity.json'
    schema = json.loads(schema_path.read_text())
    contract = json.loads((root / 'contracts/observability-capacity.json').read_text())
    errors = []
    pairs = [('basis', schema['definitions']['quantity']['properties']['basis']['enum']),
             ('status', schema['properties']['status']['enum']),
             ('exclusion_reasons', schema['properties']['serving_offers']['items']['properties']['exclusion_reasons']['items']['enum'])]
    for name, values in pairs:
        if contract[name] != values:
            errors.append('observability vocabulary drift: ' + name)
    Draft7Validator.check_schema(schema)
    store = {}
    for path in (root / "schemas/v1").rglob("*.json"):
        item = json.loads(path.read_text())
        store[item["$id"]] = item
    fleet_schema = json.loads((root / contract["fleet_schema"]).read_text())
    for field in ("lineage_fields", "timing_fields"):
        prose = (root / "specs/09_OBSERVABILITY_RECEIPTS.md").read_text()
        for name in contract[field]:
            if name not in prose:
                errors.append("observability metadata vocabulary absent from spec: " + name)
    def validator(document):
        selected = fleet_schema if document.get("schema") == "iw.observability.capacity.fleet/1" else schema
        return Draft7Validator(selected, resolver=RefResolver(base_uri=selected["$id"], referrer=selected, store=store), format_checker=FormatChecker())
    for kind in ('valid', 'invalid'):
        paths = list((root / 'fixtures' / kind).glob('observability-capacity-*.json'))
        if not paths:
            errors.append('missing observability capacity ' + kind + ' fixtures')
        for path in paths:
            try:
                fixture = decode(path.read_bytes())
                failures = list(validator(fixture).iter_errors(fixture))
                if not failures:
                    failures.extend(fleet_errors(fixture) if fixture.get("schema") == "iw.observability.capacity.fleet/1" else semantic_errors(fixture))
            except (ValueError, UnicodeDecodeError) as error:
                failures = [str(error)]
            if bool(failures) != (kind == 'invalid'):
                errors.append(str(path.relative_to(root)) + ': unexpected validation result')
    return errors


def fleet_errors(fleet):
    errors = []
    if fleet['node_count'] < len(fleet['nodes']):
        errors.append('fleet node count is smaller than this page')
    seen = set()
    for node in fleet['nodes']:
        key = node['node_id']
        if key in seen:
            errors.append('duplicate node identity in fleet')
        seen.add(key)
        errors.extend(semantic_errors(node))
    errors.extend(pool_errors(fleet['nodes']))
    return errors
