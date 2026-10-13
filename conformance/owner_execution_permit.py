"""Offline spec57 node ordering oracle; no real persistence, network or backend execution."""
import copy
import hashlib
import json
import struct
from pathlib import Path

from jsonschema import Draft7Validator, RefResolver
import alias_edge_delegation as edge
import node_join

PURPOSE = 'inferweave.owner-execution-permit/v1'
CAPABILITY = 'iw.owner-execution-permit/1'
MAX_BYTES = 16384


def field(value, name):
    for part in name.split('.'):
        value = value[part]
    return value


def transcript(value, fields):
    if type(value.get('version')) is not int or value['version'] != 1 or value['purpose'] != PURPOSE:
        raise ValueError('POLICY_DENIED')
    if type(value['permit'].get('schema_version')) is not int or value['permit']['schema_version'] != 1:
        raise ValueError('POLICY_DENIED')
    result = bytearray(PURPOSE.encode() + b'\0')
    for name in fields:
        item = field(value, name)
        if type(item) is int and 1 <= item <= 9007199254740991:
            item = str(item)
        if not isinstance(item, str):
            raise ValueError('POLICY_DENIED')
        encoded = item.encode('utf-8')
        result.extend(struct.pack('>I', len(encoded)))
        result.extend(encoded)
    return bytes(result)


def decode(raw, root):
    if len(raw) > MAX_BYTES:
        raise ValueError('POLICY_DENIED')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=edge._unique_members)
    schema_path = root / 'schemas/v1/aliases/owner-execution-permit.json'
    schema = json.loads(schema_path.read_text())
    store = {}
    for path in schema_path.parent.glob("*.json"):
        item = json.loads(path.read_text())
        store[item["$id"]] = item
    resolver = RefResolver(schema["$id"], schema, store=store,
                           handlers={"https": lambda uri: (_ for _ in ()).throw(ValueError("unknown schema"))})
    if list(Draft7Validator(schema, resolver=resolver).iter_errors(value)):
        raise ValueError('POLICY_DENIED')
    if len(edge.decode_base64(value['signature'])) != 64:
        raise ValueError('POLICY_DENIED')
    return value


def verify(value, actual, trusted, current, fields, now):
    import alias_execution as execution
    if (trusted['purpose'] != PURPOSE or not trusted['key_enabled']
            or value['issuer'] != trusted['issuer'] or value['key_id'] != trusted['key_id']
            or value['audience'] != trusted['node_id']
            or value['claim_authority_id'] != trusted['claim_authority_id']
            or value['owner_incarnation'] != current['owner_incarnation']
            or value['holder_id'] != current['holder_id']):
        raise ValueError('POLICY_DENIED')
    if not node_join.ed25519_verify(bytes.fromhex(trusted['public_key_hex']), transcript(value, fields),
                                   edge.decode_base64(value['signature'])):
        raise ValueError('POLICY_DENIED')
    permit, selection = value['permit'], value['selection']
    if (permit != current['permit'] or selection != current['selection']
            or value['issuer'] != permit['resource_owner_id'] or current['state'] != 'DISPATCHED'
            or not current['reservation_valid'] or current['retired']):
        raise ValueError('LEASE_CONFLICT')
    for name in ['instance_id', 'instance_generation', 'resource_owner_id']:
        if permit[name] != selection[name]:
            raise ValueError('POLICY_DENIED')
    if selection['model_id'] != permit['execution_binding']['model_id']:
        raise ValueError('POLICY_DENIED')
    if (current['runtime_generation'] != permit['instance_generation']
            or current['runtime_instance'] != permit['instance_id'] or not current['runtime_ready']):
        raise ValueError('INSTANCE_GENERATION_STALE')
    issued, expiry = value['issued_at_unix_ms'], value['expires_at_unix_ms']
    if not (issued <= now + 5000 and issued < expiry <= issued + 30000
            and now < expiry <= permit['deadline_unix_ms']):
        raise ValueError('POLICY_DENIED')
    binding = permit['execution_binding']
    if (binding['executable_request_fingerprint'] != execution.fingerprint(actual)
            or binding['executable_body_sha256'] != hashlib.sha256(actual['body'].encode()).hexdigest()
            or json.loads(actual['body'])['model'] != binding['model_id']):
        raise ValueError('POLICY_DENIED')


class NodeOracle:
    """Explicit durable-step model, not an fsync/DB/RPC implementation."""
    def __init__(self, consumed=None):
        self.local = {}
        self.central = consumed if consumed is not None else set()
        self.starts = 0
        self.consume_calls = 0

    def execute(self, envelope, actual, trusted, current, fields, now, *, transport='LINK',
                negotiated=True, intent_synced=True, ack='NEWLY_CONSUMED', spent_synced=True,
                generation_at_start=None):
        # Other transport implementations remain unqualified. Central uniqueness is shared
        # even by independently instantiated node oracles, representing another future path.
        if transport != 'LINK' or not negotiated:
            return 'UNSUPPORTED'
        verify(envelope, actual, trusted, current, fields, now)
        key = (envelope['claim_authority_id'], envelope['permit']['claim_id'])
        if key in self.local:
            return 'RECONCILE'
        if not intent_synced:
            return 'LOCAL_STORAGE_FAILED'
        self.local[key] = 'INTENT'
        self.consume_calls += 1
        if key in self.central:
            return 'ALREADY_CONSUMED'
        self.central.add(key)
        if ack != 'NEWLY_CONSUMED':
            return 'RECONCILE'
        # The current generation is held through this final start boundary in real code.
        if generation_at_start is not None and generation_at_start != current['runtime_generation']:
            return 'INSTANCE_GENERATION_STALE'
        if not spent_synced:
            return 'LOCAL_STORAGE_FAILED'
        self.local[key] = 'SPENT'
        self.starts += 1
        return 'STARTED'


def run_case(case, base, fields, root):
    central = set()
    nodes = {'first': NodeOracle(central)}
    errors = []
    for step in case['steps']:
        node = nodes.setdefault(step.get('node', 'first'), NodeOracle(central))
        # Restart retains the simulated durable local record; all transient state is lost.
        if step.get('restart'):
            old = node
            node = NodeOracle(central)
            node.local = copy.deepcopy(old.local)
            node.starts = old.starts
            node.consume_calls = old.consume_calls
            nodes[step.get('node', 'first')] = node
        data = {key: copy.deepcopy(base[key]) for key in ['envelope', 'actual', 'trusted', 'current']}
        for change in step.get('changes', []):
            target = data[change['surface']]
            parts = change['field'].split('.')
            for part in parts[:-1]: target = target[part]
            target[parts[-1]] = change['value']
        if step.get('resign'):
            data['envelope']['signature'] = edge.b64url(node_join.ed25519_sign(
                bytes.fromhex(base['test_seed_hex']), transcript(data['envelope'], fields)))
        try:
            decode(json.dumps(data['envelope']).encode(), root)
            outcome = node.execute(**data, fields=fields, now=step.get('now', base['now']),
                                   **step.get('options', {}))
        except (ValueError, KeyError, TypeError) as error:
            outcome = str(error)
        if outcome != step['expected']:
            errors.append(f"{case['id']}: expected {step['expected']}, got {outcome}")
    if sum(node.starts for node in nodes.values()) != case['expected_starts']:
        errors.append(case['id'] + ': backend start count mismatch')
    if sum(node.consume_calls for node in nodes.values()) != case['expected_consume_calls']:
        errors.append(case['id'] + ': consume ordering mismatch')
    return errors


def check_vectors(root):
    root = Path(root)
    contract = json.loads((root/'contracts/protocol-v1/alias-execution.json').read_text())['owner_permit']
    vectors = json.loads((root/'conformance/owner-execution-permit-vectors.json').read_text())
    fields = contract['transcript_fields']
    errors = []
    if (contract['purpose'] != PURPOSE or contract['link_capability'] != CAPABILITY
            or contract['maximum_encoded_bytes'] != MAX_BYTES
            or vectors['operational_proof_status'] != 'owed'):
        errors.append('owner permit frozen vocabulary/proof status drift')
    base = vectors['known_answer']
    wire = transcript(base['envelope'], fields)
    if wire.hex() != base['transcript_hex']:
        errors.append('owner permit transcript known answer mismatch')
    if edge.b64url(node_join.ed25519_sign(bytes.fromhex(base['test_seed_hex']), wire)) != base['envelope']['signature']:
        errors.append('owner permit signature known answer mismatch')
    for case in vectors['cases']:
        errors.extend(run_case(case, base, fields, root))
    return errors
