"""Offline spec57 transcript and serial transition oracle; NOT a production authorizer/store.

The ledger intentionally models one serial authority. Passing it cannot prove PostgreSQL
atomicity, HTTP credential verification, distributed fencing, node admission or cleanup.
"""
import copy
import hashlib
import json
import struct
from pathlib import Path
import alias_edge_delegation as edge
import alias_inference_transport as transport
import node_join

DOMAIN = b'inferweave.edge-inference-delegation/v1\0'
FINGERPRINT_DOMAIN = b'inferweave.alias-request-fingerprint/v1\0'
FIELDS = ('edge_id', 'key_id', 'audience', 'idp_issuer', 'subject', 'issued_at_unix_ms',
          'expires_at_unix_ms', 'nonce', 'method', 'request_target', 'body_sha256',
          'content_type', 'alias_level', 'session_id', 'timeout_ms', 'capabilities',
          'min_context', 'prefer_family', 'queue', 'tenant_selector', 'operation_id',
          'idempotency_key', 'request_fingerprint', 'deadline_unix_ms')
FINGERPRINT_FIELDS = ('method', 'request_target', 'body_sha256', 'content_type', 'alias_level',
                      'session_id', 'timeout_ms', 'capabilities', 'min_context',
                      'prefer_family', 'queue', 'tenant_selector')
STATES = ['CLAIMED', 'RESERVED', 'DISPATCHED', 'TERMINAL']
TRANSITIONS = [('CLAIMED', 'RESERVED'), ('RESERVED', 'CLAIMED'), ('RESERVED', 'DISPATCHED'),
               ('CLAIMED', 'TERMINAL'), ('RESERVED', 'TERMINAL'), ('DISPATCHED', 'TERMINAL')]
INTEGER_FIELDS = {'issued_at_unix_ms', 'expires_at_unix_ms', 'deadline_unix_ms'}


def frame(domain, values, fields):
    result = bytearray(domain)
    for field in fields:
        value = values[field]
        if field in INTEGER_FIELDS:
            if type(value) is not int or not 1 <= value <= 9007199254740991:
                raise ValueError('noncanonical integer')
            value = str(value)
        if not isinstance(value, str):
            raise ValueError('expected string')
        raw = value.encode('utf-8')
        result.extend(struct.pack('>I', len(raw)))
        result.extend(raw)
    return bytes(result)


def transcript(value):
    if type(value.get('version')) is not int or value['version'] != 1:
        raise ValueError('unsupported version')
    return frame(DOMAIN, value, FIELDS)


def fingerprint(value):
    return hashlib.sha256(frame(FINGERPRINT_DOMAIN, value, FINGERPRINT_FIELDS)).hexdigest()


def decode_header(header):
    if not isinstance(header, str) or len(header) > 8192 or not header.isascii():
        raise ValueError('invalid header size/encoding')
    value = json.loads(edge.decode_base64(header).decode('utf-8'), object_pairs_hook=edge._unique_members)
    if not isinstance(value, dict) or set(value) != set(FIELDS) | {'version', 'signature'}:
        raise ValueError('unexpected assertion fields')
    transcript(value)
    if len(edge.decode_base64(value['nonce'])) != 16 or len(edge.decode_base64(value['signature'])) != 64:
        raise ValueError('invalid cryptographic field size')
    if value['request_fingerprint'] != fingerprint(value):
        raise ValueError('request fingerprint mismatch')
    return value


def verify_bound(value, actual, public_key, trusted, now):
    """Fixture verifier inputs stand for trusted stores; no network/persistence/auth proof."""
    if not node_join.ed25519_verify(public_key, transcript(value), edge.decode_base64(value['signature'])):
        raise ValueError('POLICY_DENIED')
    if (trusted['purpose'] != DOMAIN[:-1].decode() or not trusted['key_enabled']
            or not trusted['infer_grant'] or trusted['audience'] != value['audience']
            or trusted['issuer'] != value['idp_issuer']):
        raise ValueError('POLICY_DENIED')
    if any(value[field] != actual[field] for field in FINGERPRINT_FIELDS +
           ('operation_id', 'idempotency_key', 'deadline_unix_ms')):
        raise ValueError('POLICY_DENIED')
    if hashlib.sha256(actual['body'].encode()).hexdigest() != value['body_sha256']:
        raise ValueError('POLICY_DENIED')
    if value['request_fingerprint'] != fingerprint(actual):
        raise ValueError('POLICY_DENIED')
    issued, expiry, deadline = (value[f] for f in ('issued_at_unix_ms', 'expires_at_unix_ms', 'deadline_unix_ms'))
    if not (issued <= now + 5000 and issued < expiry <= issued + 30000
            and now < expiry and now < deadline <= issued + 300000):
        raise ValueError('POLICY_DENIED')
    if value['method'] != 'POST' or value['request_target'] not in trusted['allowed_targets']:
        raise ValueError('POLICY_DENIED')
    return True


def materialization_binding(source, executable, model_id):
    for request in (source, executable):
        if request['body_sha256'] != hashlib.sha256(request['body'].encode()).hexdigest():
            raise ValueError('POLICY_DENIED')
    if any(source[field] != executable[field] for field in FINGERPRINT_FIELDS if field != 'body_sha256'):
        raise ValueError('POLICY_DENIED')
    original=json.loads(source['body'], object_pairs_hook=edge._unique_members)
    materialized=json.loads(executable['body'], object_pairs_hook=edge._unique_members)
    if original['model'] != model_id and not original['model'].startswith('alias:'):
        raise ValueError('POLICY_DENIED')
    expected=dict(original, model=model_id)
    if materialized != expected:
        raise ValueError('POLICY_DENIED')
    return {'request_fingerprint':fingerprint(source),
            'executable_request_fingerprint':fingerprint(executable),
            'executable_body_sha256':executable['body_sha256'],
            'transformation_version':'inferweave.alias-materialization/v1', 'model_id':model_id}


class ClaimOracle:
    """Serial safety oracle only. A production replacement needs durable atomic transactions."""
    def __init__(self):
        self.claims = {}
        self.keys = {}
        self.retired = set()

    def acquire(self, identity, holder, method='POST', target='/v1/chat'):
        scope = (identity['tenant_id'], identity['principal_id'])
        key = scope + (identity['operation_id'],)
        alias = scope + (method, target, identity['idempotency_key']) if identity.get('idempotency_key') else None
        if alias in self.keys:
            mapped = self.keys[alias]
            if mapped != key and key in self.claims:
                raise ValueError('IDEMPOTENCY_CONFLICT')
            key = mapped
        if key in self.retired:
            raise ValueError('EXECUTION_RESULT_UNAVAILABLE')
        if key in self.claims:
            claim = self.claims[key]
            if (claim['identity']['request_fingerprint'] != identity['request_fingerprint']
                    or claim['identity'].get('idempotency_key') != identity.get('idempotency_key')):
                raise ValueError('IDEMPOTENCY_CONFLICT')
            claim['identity']['deadline_unix_ms'] = min(claim['identity']['deadline_unix_ms'], identity['deadline_unix_ms'])
            return claim, False
        claim = {'identity':copy.deepcopy(identity),'holder_id':holder,'fencing_token':1,
                 'state':'CLAIMED','attempt_count':0,'reservation_pending':False,
                 'response_started':False,'reservation_id':None,'retired_attempts':set(),
                 'dispatch_consumed':False}
        self.claims[key] = claim
        if alias:
            self.keys[alias] = key
        return claim, True

    @staticmethod
    def fence(claim, holder, fence):
        if claim['holder_id'] != holder or claim['fencing_token'] != fence:
            raise ValueError('LEASE_CONFLICT')

    def begin_reservation(self, claim, holder, fence, generation, current_generation, budget=3, model_id="fixture/model@1"):
        self.fence(claim, holder, fence)
        if claim['state'] != 'CLAIMED' or claim['reservation_pending']:
            raise ValueError('EXECUTION_IN_PROGRESS')
        if generation != current_generation:
            raise ValueError('INSTANCE_GENERATION_STALE')
        if claim['attempt_count'] >= min(budget, 8):
            raise ValueError('RETRY_BUDGET_EXHAUSTED')
        claim['attempt_count'] += 1
        claim['reservation_pending'] = True
        claim['selected_generation'] = generation
        claim['selected_model'] = model_id

    @staticmethod
    def attempt(claim, attempt_number, generation):
        if (attempt_number != claim['attempt_count'] or attempt_number in claim['retired_attempts']
                or generation != claim.get('selected_generation')):
            raise ValueError('LEASE_CONFLICT')

    def reserve(self, claim, holder, fence, reservation_id, attempt_number, generation):
        self.fence(claim, holder, fence)
        self.attempt(claim, attempt_number, generation)
        if claim['state'] != 'CLAIMED' or not claim['reservation_pending']:
            raise ValueError('EXECUTION_IN_PROGRESS')
        claim.update(state='RESERVED', reservation_pending=False, reservation_id=reservation_id)

    def release_before_dispatch(self, claim, holder, fence, owner_confirmed, attempt_number, generation):
        self.fence(claim, holder, fence)
        self.attempt(claim, attempt_number, generation)
        if claim['state'] not in ('CLAIMED', 'RESERVED') or not owner_confirmed:
            raise ValueError('EXECUTION_OUTCOME_UNKNOWN')
        claim['retired_attempts'].add(attempt_number)
        claim.update(state='CLAIMED', reservation_pending=False, reservation_id=None)

    def takeover(self, claim, holder, fence, new_holder, expired):
        self.fence(claim, holder, fence)
        if (not expired or claim['state'] != 'CLAIMED' or claim['reservation_pending']
                or claim['reservation_id'] is not None):
            raise ValueError('LEASE_CONFLICT')
        claim.update(holder_id=new_holder, fencing_token=fence+1)

    def dispatch(self, claim, holder, fence, attempt_number, generation, binding):
        self.fence(claim, holder, fence)
        self.attempt(claim, attempt_number, generation)
        if claim['state'] != 'RESERVED':
            raise ValueError('EXECUTION_IN_PROGRESS')
        if (binding['request_fingerprint'] != claim['identity']['request_fingerprint']
                or binding['model_id'] != claim['selected_model']):
            raise ValueError('POLICY_DENIED')
        claim.update(state='DISPATCHED', execution_binding=copy.deepcopy(binding))

    def consume(self, claim, holder, fence, attempt_number, generation, binding, actual,
                permit_id, route_kind):
        # permit ID/route annotate the attempt; neither establishes another execution namespace.
        self.fence(claim, holder, fence)
        self.attempt(claim, attempt_number, generation)
        if claim['state'] != 'DISPATCHED' or claim['dispatch_consumed']:
            raise ValueError('EXECUTION_IN_PROGRESS')
        if (binding != claim['execution_binding']
                or binding['executable_request_fingerprint'] != fingerprint(actual)
                or binding['executable_body_sha256'] != hashlib.sha256(actual['body'].encode()).hexdigest()
                or json.loads(actual['body'])['model'] != binding['model_id']):
            raise ValueError('POLICY_DENIED')
        claim['dispatch_consumed'] = True

    def mark_response_started(self, claim, holder, fence):
        self.fence(claim, holder, fence)
        if claim['state'] != 'DISPATCHED' or not claim['dispatch_consumed']:
            raise ValueError('EXECUTION_IN_PROGRESS')
        claim['response_started'] = True

    def terminal(self, claim, holder, fence, reason, owner_confirmed=False):
        self.fence(claim, holder, fence)
        if claim['state'] == 'TERMINAL':
            raise ValueError('EXECUTION_RESULT_UNAVAILABLE')
        if (claim['state'] == 'RESERVED' or claim['reservation_pending']) and not owner_confirmed:
            raise ValueError('EXECUTION_OUTCOME_UNKNOWN')
        claim.update(state='TERMINAL', terminal_reason=reason, reservation_pending=False)


def run_claim_case(case, identity):
    oracle = ClaimOracle()
    claims = {}
    for step in case['steps']:
        params = dict(step)
        action = params.pop('action')
        expected_error = params.pop('expected_error', None)
        try:
            if action == 'acquire':
                name=params.pop('as'); expected_created=params.pop('created',None)
                same_as=params.pop('same_as',None)
                updated=dict(identity,**params.pop('identity_changes',{}))
                value,created=oracle.acquire(updated,**params)
                if created != expected_created:
                    return 'duplicate operation did not converge'
                claims[name]=value
                if same_as and value is not claims[same_as]:
                    return 'two parents acquired independent claims'
            else:
                value=claims[params.pop('claim')]
                getattr(oracle,action)(value,**params)
        except ValueError as error:
            if str(error) != expected_error:
                return f'{action}: expected {expected_error}, got {error}'
        else:
            if expected_error:
                return f'{action}: expected rejection {expected_error}'
    final=claims[case['final_claim']]
    if final['state'] != case['expected_state'] or final['attempt_count'] != case['expected_attempt_count']:
        return 'final state or admission attempts differ'
    return None


def check_vectors(root):
    root = Path(root)
    contract = json.loads((root/'contracts/protocol-v1/alias-execution.json').read_text())
    vectors = json.loads((root/'conformance/alias-execution-vectors.json').read_text())
    spec = (root/'specs/57_ALIAS_EXECUTION_IDENTITY_AND_CLAIMS.md').read_text()
    import owner_execution_permit
    errors = transport.check_vectors(root) + owner_execution_permit.check_vectors(root)
    comparisons = [('assertion_fields', list(FIELDS)), ('fingerprint_fields', list(FINGERPRINT_FIELDS)),
                   ('claim_states', STATES), ('transitions',[list(t) for t in TRANSITIONS]),
                   ('assertion_domain',DOMAIN[:-1].decode()),('fingerprint_domain',FINGERPRINT_DOMAIN[:-1].decode())]
    for field, expected in comparisons:
        if contract[field] != expected:
            errors.append('alias execution frozen contract drift: '+field)
    if contract.get('proof_status') != 'owed' or vectors.get('operational_proof_status') != 'owed':
        errors.append('offline proof misrepresented as operational')
    schema = json.loads((root/'schemas/v1/aliases/inference-assertion.json').read_text())
    if set(schema['required']) != set(FIELDS)|{'version','signature'}:
        errors.append('inference assertion schema/transcript drift')
    if schema['properties']['request_target']['enum'] != contract['allowed_targets']:
        errors.append('inference target allowlist drift')
    claim = json.loads((root/'schemas/v1/aliases/execution-claim.json').read_text())
    if claim['properties']['state']['enum'] != STATES:
        errors.append('claim state schema drift')
    binding=json.loads((root/'schemas/v1/aliases/execution-binding.json').read_text())
    if binding['properties']['transformation_version']['enum'] != contract['transformation_versions']:
        errors.append('materialization version vocabulary drift')
    for name in contract['transformation_versions']:
        if f'`{name}`' not in spec:
            errors.append('materialization version absent from spec')
    if (contract['owner_reservation_unique_key'] != ['claim_id','admission_attempt']
            or contract['execution_consumption_unique_key'] != ['claim_authority_id','claim_id']
            or contract['operation_key_choice_immutable'] is not True):
        errors.append('execution exclusivity identity drift')
    for number, field in enumerate(FIELDS,1):
        if f'{number}. `{field}`' not in spec:
            errors.append('inference transcript documentation drift: '+field)
    for state in STATES:
        if f'`{state}`' not in spec:
            errors.append('claim state documentation drift: '+state)
    for case in vectors['known_answers']:
        value=case['envelope']; wire=transcript(value); seed=bytes.fromhex(case['test_seed_hex'])
        public=node_join.ed25519_public(seed); signature=node_join.ed25519_sign(seed,wire)
        if wire.hex()!=case['transcript_hex'] or public.hex()!=case['public_key_hex']:
            errors.append(case['id']+': transcript/key mismatch')
        if edge.b64url(signature)!=value['signature'] or fingerprint(value)!=value['request_fingerprint']:
            errors.append(case['id']+': signature/fingerprint mismatch')
        try:
            if decode_header(case['header'])!=value:
                errors.append(case['id']+': header mismatch')
            verify_bound(value,case['actual_request'],public,case['trusted'],case['now'])
        except (ValueError,KeyError,TypeError) as error:
            errors.append(case['id']+': '+str(error))
    # Every hostile mutation is applied to a valid baseline and must be rejected.
    base=vectors['known_answers'][0]
    for case in vectors['hostile_cases']:
        value=copy.deepcopy(base['envelope']); actual=copy.deepcopy(base['actual_request']); trusted=copy.deepcopy(base['trusted']); now=base['now']
        if case['surface']=='clock': now=case['replacement']
        else: {'envelope':value,'actual':actual,'trusted':trusted}[case['surface']][case['field']]=case['replacement']
        try: verify_bound(value,actual,bytes.fromhex(base['public_key_hex']),trusted,now)
        except (ValueError,KeyError,TypeError): pass
        else: errors.append(case['id']+': hostile request accepted')
    identity=json.loads((root/'fixtures/valid/alias-execution-identity.json').read_text())
    for case in vectors['claim_cases']:
        failure=run_claim_case(case,identity)
        if failure:
            errors.append(case['id']+': '+failure)
    for case in vectors['materialization_cases']:
        try:
            if materialization_binding(case['source'], case['executable'], case['model_id']) != case['binding']:
                errors.append(case['id']+': materialization binding mismatch')
        except ValueError as error:
            errors.append(case['id']+': '+str(error))
    return errors
