"""Spec57 offline proof. Real HTTP/DB/node fault-injection gates remain owed."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'conformance'))
import alias_execution as execution
import alias_inference_transport as transport
import alias_edge_delegation as edge
import node_join
import owner_execution_permit as owner


class ExecutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors=json.loads((ROOT/'conformance/alias-execution-vectors.json').read_text())
        cls.identity=json.loads((ROOT/'fixtures/valid/alias-execution-identity.json').read_text())

    def test_owner_envelope_known_answer_and_ordering_vectors(self):
        self.assertEqual([], owner.check_vectors(ROOT))
        vectors=json.loads((ROOT/'conformance/owner-execution-permit-vectors.json').read_text())
        self.assertGreaterEqual(len(vectors['cases']), 28)

    def test_owner_envelope_rejects_oversized_duplicate_and_unknown_fields(self):
        base=json.loads((ROOT/'fixtures/valid/alias-owner-execution-permit.json').read_text())
        wire=json.dumps(base).encode()
        self.assertEqual(base, owner.decode(wire, ROOT))
        invalid=[wire+b' '*owner.MAX_BYTES,
                 (json.dumps(base)[:-1]+',"holder_id":"other"}').encode()]
        for changes in [{'version':2},{'version':True},{'signature':'AA'},
                        {'unbound_endpoint':'http://untrusted.invalid'},
                        {'purpose':'inferweave.edge-inference-delegation/v1'}]:
            invalid.append(json.dumps(dict(base,**changes)).encode())
        nested=copy.deepcopy(base);nested['permit']['execution_binding']['extra']='x'
        invalid.append(json.dumps(nested).encode())
        for raw in invalid:
            with self.assertRaises(ValueError):owner.decode(raw,ROOT)

    def test_owner_signature_binds_every_field_and_purpose(self):
        vectors=json.loads((ROOT/'conformance/owner-execution-permit-vectors.json').read_text())
        fields=json.loads((ROOT/'contracts/protocol-v1/alias-execution.json').read_text())['owner_permit']['transcript_fields']
        base=vectors['known_answer'];original=owner.transcript(base['envelope'],fields)
        for name in fields:
            changed=copy.deepcopy(base['envelope']);target=changed;parts=name.split('.')
            for part in parts[:-1]:target=target[part]
            old=target[parts[-1]];target[parts[-1]]=old+1 if type(old)is int else old+'x'
            wire=owner.transcript(changed,fields)
            self.assertNotEqual(original,wire,name)
            self.assertFalse(node_join.ed25519_verify(bytes.fromhex(base['trusted']['public_key_hex']),
                            wire,edge.decode_base64(base['envelope']['signature'])),name)

    def test_owner_hostile_vectors_detect_removed_authentication(self):
        with patch.object(owner,'verify',lambda *args:None):
            self.assertTrue(owner.check_vectors(ROOT))

    def test_owner_lost_ack_does_not_start_or_reopen_on_restart(self):
        vectors=json.loads((ROOT/'conformance/owner-execution-permit-vectors.json').read_text())
        fields=json.loads((ROOT/'contracts/protocol-v1/alias-execution.json').read_text())['owner_permit']['transcript_fields']
        case=next(c for c in vectors['cases'] if c['id']=='lost-consume-ack-restart')
        self.assertEqual([],owner.run_case(case,vectors['known_answer'],fields,ROOT))
        real=owner.NodeOracle.execute
        def unsafe_ack(self,*args,**kwargs):
            kwargs['ack']='NEWLY_CONSUMED'
            return real(self,*args,**kwargs)
        with patch.object(owner.NodeOracle,'execute',unsafe_ack):
            self.assertTrue(owner.run_case(case,vectors['known_answer'],fields,ROOT))

    def test_all_known_answers_hostile_vectors_and_claim_transitions(self):
        self.assertEqual([],execution.check_vectors(ROOT))
        self.assertGreaterEqual(len(self.vectors['claim_cases']),12)

    def test_shared_transport_vectors_and_removed_control_detection(self):
        vectors=json.loads((ROOT/'conformance/alias-inference-transport-vectors.json').read_text())
        self.assertEqual(36,len(vectors['mime_cases']))
        self.assertEqual(12,len(vectors['header_cases']))
        self.assertEqual([],transport.check_vectors(ROOT))
        with patch.object(transport,'accepts_mime',lambda *args:True):
            self.assertTrue(transport.check_vectors(ROOT))
        with patch.object(transport,'accepts_headers',lambda *args:True):
            self.assertTrue(transport.check_vectors(ROOT))

    def test_correlation_byte_limit_and_unicode_controls(self):
        bound=json.loads((ROOT/'contracts/protocol-v1/alias-execution.json').read_text())['bound_headers']
        for value,expected in [('€'*2730+'ab',True),('€'*2731,False),('a\u0085b',False)]:
            case={'headers':[['x-inferweave-request-id',value]],'empty_fields':[]}
            self.assertEqual(expected,transport.accepts_headers(case,bound))

    def test_equivalent_mime_classification_never_normalizes_signed_bytes(self):
        base=self.vectors['known_answers'][0]['envelope']
        first=dict(base,content_type='application/json; charset=utf-8; note="x"')
        second=dict(base,content_type='Application/JSON; note="x"; CHARSET="utf-8"')
        for request in [first,second]:
            self.assertTrue(transport.accepts_mime(request['content_type'],'/v1/chat'))
        self.assertNotEqual(execution.fingerprint(first),execution.fingerprint(second))
        self.assertNotEqual(execution.transcript(first),execution.transcript(second))
        for correlation in ['first','second']:
            augmented=dict(first,**{'x-inferweave-request-id':correlation})
            self.assertEqual(execution.fingerprint(first),execution.fingerprint(augmented))
            self.assertEqual(execution.transcript(first),execution.transcript(augmented))

    def test_signature_domain_cannot_be_reused_from_management(self):
        v=self.vectors['known_answers'][0]
        wire=execution.transcript(v['envelope'])
        wrong=edge.DOMAIN+wire[len(execution.DOMAIN):]
        signature=node_join.ed25519_sign(bytes.fromhex(v['test_seed_hex']),wrong)
        self.assertFalse(node_join.ed25519_verify(bytes.fromhex(v['public_key_hex']),wire,signature))

    def test_fingerprint_binds_every_accepted_semantic_header(self):
        base=self.vectors['known_answers'][0]['envelope']
        original=execution.fingerprint(base)
        for field in execution.FINGERPRINT_FIELDS:
            changed=dict(base);changed[field]+='x'
            self.assertNotEqual(original,execution.fingerprint(changed),field)
        for field in ['edge_id','nonce','signature','operation_id','deadline_unix_ms']:
            changed=dict(base);changed[field]=changed[field]+1 if type(changed[field]) is int else changed[field]+'x'
            self.assertEqual(original,execution.fingerprint(changed),field)

    def test_header_rejects_duplicate_unknown_fields_padding_and_wrong_fingerprint(self):
        base=self.vectors['known_answers'][0]
        raw=json.dumps(base['envelope'])
        malformed=[base['header']+'=',edge.b64url((raw[:-1]+',"subject":"foreign"}').encode())]
        for mutation in [{'tenant_id':'foreign'},{'version':2},{'version':True},{'nonce':'AA'},
                         {'signature':'AA'},{'request_fingerprint':'0'*64},{'deadline_unix_ms':1.0}]:
            malformed.append(edge.b64url(json.dumps(dict(base['envelope'],**mutation)).encode()))
        for header in malformed:
            with self.assertRaises(ValueError): execution.decode_header(header)

    def test_equal_prompts_without_idempotency_key_are_distinct_work(self):
        oracle=execution.ClaimOracle();a=dict(self.identity);a.pop('idempotency_key')
        b=dict(a,operation_id='another-valid-operation-id')
        first,_=oracle.acquire(a,'a');second,created=oracle.acquire(b,'a')
        self.assertTrue(created);self.assertIsNot(first,second)

    def test_changed_principal_or_tenant_does_not_observe_original(self):
        oracle=execution.ClaimOracle();first,_=oracle.acquire(self.identity,'a')
        for field in ['tenant_id','principal_id']:
            second,created=oracle.acquire(dict(self.identity,**{field:'foreign'}),'b')
            self.assertTrue(created);self.assertIsNot(first,second)

    def test_retry_deadline_never_extends_and_request_id_survives(self):
        oracle=execution.ClaimOracle();first,_=oracle.acquire(self.identity,'a')
        retry=dict(self.identity,request_id='attempt-correlation',deadline_unix_ms=self.identity['deadline_unix_ms']+10000)
        second,created=oracle.acquire(retry,'b')
        self.assertFalse(created);self.assertIs(first,second)
        self.assertEqual(self.identity['request_id'],second['identity']['request_id'])
        self.assertEqual(self.identity['deadline_unix_ms'],second['identity']['deadline_unix_ms'])
        retry['deadline_unix_ms']-=11000;oracle.acquire(retry,'b')
        self.assertEqual(retry['deadline_unix_ms'],first['identity']['deadline_unix_ms'])

    def test_retired_operation_cannot_recreate_work(self):
        oracle=execution.ClaimOracle();claim,_=oracle.acquire(self.identity,'a')
        key=tuple(self.identity[f] for f in ['tenant_id','principal_id','operation_id'])
        oracle.retired.add(key);del oracle.claims[key]
        with self.assertRaisesRegex(ValueError,'EXECUTION_RESULT_UNAVAILABLE'):
            oracle.acquire(self.identity,'b')

    def test_fence_and_ambiguity_cases_detect_removed_controls(self):
        cases={c['id']:c for c in self.vectors['claim_cases']}
        with patch.object(execution.ClaimOracle,'fence',lambda *args:None):
            self.assertIsNotNone(execution.run_claim_case(cases['takeover-fences-old-holder'],self.identity))
        def broken_release(claim,holder,fence,owner_confirmed,**kwargs):
            claim.update(state='CLAIMED',reservation_pending=False,reservation_id=None)
        with patch.object(execution.ClaimOracle,'release_before_dispatch',staticmethod(broken_release)):
            self.assertIsNotNone(execution.run_claim_case(cases['ambiguous-send-before-response-never-replays'],self.identity))

    def test_operation_key_choice_is_immutable_and_conflicting_names_reject(self):
        for original,new_key in [(self.identity,'other-key'),(self.identity,None),
                                 (dict(self.identity,idempotency_key=None),'new-key')]:
            oracle=execution.ClaimOracle();oracle.acquire(original,'a')
            with self.assertRaisesRegex(ValueError,'IDEMPOTENCY_CONFLICT'):
                oracle.acquire(dict(original,idempotency_key=new_key),'b')
        oracle=execution.ClaimOracle();oracle.acquire(self.identity,'a')
        other=dict(self.identity,operation_id='different-operation-identifier',idempotency_key='other-key')
        oracle.acquire(other,'a')
        with self.assertRaisesRegex(ValueError,'IDEMPOTENCY_CONFLICT'):
            oracle.acquire(dict(self.identity,idempotency_key='other-key'),'a')

    def test_materialization_binds_original_and_executable_payload(self):
        case=self.vectors['materialization_cases'][0]
        bound=execution.materialization_binding(case['source'],case['executable'],case['model_id'])
        self.assertNotEqual(bound['request_fingerprint'],bound['executable_request_fingerprint'])
        changed=copy.deepcopy(case['executable'])
        body=json.loads(changed['body']);body['messages'][0]['content']='altered prompt'
        changed['body']=json.dumps(body)
        import hashlib
        changed['body_sha256']=hashlib.sha256(changed['body'].encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,'POLICY_DENIED'):
            execution.materialization_binding(case['source'],changed,case['model_id'])
        with self.assertRaisesRegex(ValueError,'POLICY_DENIED'):
            execution.materialization_binding(case['source'],case['executable'],'wrong-model')

    def test_old_attempt_vector_fails_when_attempt_fence_removed(self):
        cases={c['id']:c for c in self.vectors['claim_cases']}
        with patch.object(execution.ClaimOracle,'attempt',lambda *args:None):
            self.assertIsNotNone(execution.run_claim_case(cases['response-loss-same-owner-fallback-old-attempt-denied'],self.identity))

    def test_frozen_contract_guard_detects_schema_and_vocab_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for part in ['contracts','conformance','schemas','specs','fixtures']:
                shutil.copytree(ROOT/part,root/part)
            path=root/'contracts/protocol-v1/alias-execution.json';base=path.read_text();value=json.loads(base)
            value['claim_states'].append('RETRY');path.write_text(json.dumps(value))
            self.assertTrue(execution.check_vectors(root));path.write_text(base)
            path=root/'schemas/v1/aliases/inference-assertion.json';value=json.loads(path.read_text())
            value['required'].remove('operation_id');path.write_text(json.dumps(value))
            self.assertTrue(execution.check_vectors(root))


if __name__=='__main__': unittest.main()
