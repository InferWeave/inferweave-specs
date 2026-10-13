#!/usr/bin/env python3
"""Reproduce public spec57 test vectors. Fixture seeds are NOT deployment credentials."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'conformance'))
import alias_execution as execution
import alias_edge_delegation as edge
import node_join


def generate(root=ROOT):
    def write(path,value):
        (root/path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    contract=json.loads((ROOT/'contracts/protocol-v1/alias-execution.json').read_text())
    body='{"model":"alias:coding-fast","messages":[{"role":"user","content":"fixture only"}]}'
    value={'version':1,'edge_id':'edge-a','key_id':'inference-key-a','audience':'claim-authority-a',
           'idp_issuer':'https://identity.example.invalid/','subject':'fixture-user',
           'issued_at_unix_ms':1800000000000,'expires_at_unix_ms':1800000020000,
           'nonce':edge.b64url(bytes(range(16))),'method':'POST','request_target':'/v1/chat',
           'body_sha256':hashlib.sha256(body.encode()).hexdigest(),'content_type':'application/json',
           'alias_level':'2','session_id':'session-fixture','timeout_ms':'12000',
           'capabilities':'tools','min_context':'32768','prefer_family':'qwen','queue':'true',
           'tenant_selector':'fixture-tenant','operation_id':edge.b64url(bytes(range(16,32))),
           'idempotency_key':'fixture-operation','deadline_unix_ms':1800000012000}
    known=[]
    for i,(name,subject,edge_id) in enumerate([('ascii','fixture-user','edge-a'),('unicode','fixture-用户','edge-a'),('second-parent','fixture-user','edge-b')]):
        v=copy.deepcopy(value);v.update(subject=subject,edge_id=edge_id,nonce=edge.b64url(bytes([i+1])*16))
        v['request_fingerprint']=execution.fingerprint(v)
        seed=bytes(range(32));wire=execution.transcript(v)
        v['signature']=edge.b64url(node_join.ed25519_sign(seed,wire))
        actual={f:v[f] for f in execution.FINGERPRINT_FIELDS+('operation_id','idempotency_key','deadline_unix_ms')};actual['body']=body
        known.append({'id':name,'test_seed_hex':seed.hex(),'public_key_hex':node_join.ed25519_public(seed).hex(),'transcript_hex':wire.hex(),'envelope':v,'header':edge.b64url(json.dumps(v,separators=(',',':'),ensure_ascii=False).encode()),'actual_request':actual,'now':1800000001000,'trusted':{'purpose':execution.DOMAIN[:-1].decode(),'key_enabled':True,'infer_grant':True,'audience':v['audience'],'issuer':v['idp_issuer'],'allowed_targets':contract['allowed_targets']}})
    hostile=[]
    for f in execution.FIELDS:
        old=known[0]['envelope'][f]
        hostile.append({'id':'tampered-'+f,'surface':'envelope','field':f,'replacement':old+1 if type(old) is int else old+'x'})
    for f in execution.FINGERPRINT_FIELDS+('operation_id','idempotency_key','deadline_unix_ms','body'):
        old=known[0]['actual_request'][f]
        hostile.append({'id':'actual-'+f,'surface':'actual','field':f,'replacement':old+1 if type(old) is int else old+'x'})
    for f,replacement in [('purpose',edge.DOMAIN[:-1].decode()),('key_enabled',False),('infer_grant',False),('audience','foreign'),('issuer','foreign')]:
        hostile.append({'id':'trust-'+f,'surface':'trusted','field':f,'replacement':replacement})
    hostile.extend([{'id':'expired','surface':'clock','replacement':1800000020000},{'id':'future-clock','surface':'clock','replacement':1799999990000}])
    doc={'schema_version':1,'operational_proof_status':'owed','known_answers':known,'hostile_cases':hostile,'runtime_obligations':['native-personal-key-revocation','raw-tenant-header-is-not-authority','management-purpose-rejected','shared-postgresql-two-parent-concurrency','nonce-replay-across-purposes','reservation-acquire-response-lost','stale-holder-node-fencing','direct-permit-one-use','admission-generation-race','partial-stream-no-replay','ambiguous-dispatch-before-first-byte','deadline-cancel-owner-cleanup','exact-model-precedence','tenant-trace-redaction']}
    write('conformance/alias-execution-vectors.json',doc)
    identity={'tenant_id':'fixture-tenant','principal_id':'principal-fixture','grant_revision':'grant-7','operation_id':value['operation_id'],'request_id':'request-fixture','idempotency_key':'fixture-operation','request_fingerprint':known[0]['envelope']['request_fingerprint'],'deadline_unix_ms':value['deadline_unix_ms']}
    selection={'alias_id':'coding-fast','alias_revision':2,'catalog_revision':'catalog-fixture','routing_policy_version':'fixture-policy-1','model_id':'fixture/model@1','deployment_key':'fixture-deployment','instance_id':'fixture-instance','instance_generation':'fixture-generation','capability_profile_id':'fixture-profile','policy_evidence_id':'fixture-policy','resource_owner_id':'fixture-owner','resource_group_id':'fixture-group','requirement_fingerprint':'a'*64}
    claim={'schema_version':1,'claim_id':'claim-fixture','identity':identity,'state':'RESERVED','holder_id':'holder-a','fencing_token':1,'last_progress_at':1800000001000,'ownership_lease':{'lease_id':'holder-lease','generation':1,'expires_at_unix_ms':1800000010000},'attempt_count':1,'reservation_pending':False,'response_started':False,'selection':selection,'reservation_id':'reservation-fixture','cleanup_pending':False}
    acquire={'action':'acquire','as':'first','holder':'parent-a','created':True}
    begin={'action':'begin_reservation','claim':'first','holder':'parent-a','fence':1,'generation':'g1','current_generation':'g1'}
    reserve={'action':'reserve','claim':'first','holder':'parent-a','fence':1,'reservation_id':'reservation-1'}
    dispatch={'action':'dispatch','claim':'first','holder':'parent-a','fence':1}
    def altered(base,**changes): return dict(base,**changes)
    def case(name,steps,state,attempts):
        return {'id':name,'steps':steps,'final_claim':'first','expected_state':state,'expected_attempt_count':attempts}
    doc['claim_cases']=[
        case('two-parents-same-operation',[acquire,{'action':'acquire','as':'duplicate','holder':'parent-b','created':False,'same_as':'first'},begin,reserve,altered(begin,claim='duplicate',holder='parent-b',expected_error='LEASE_CONFLICT')],'RESERVED',1),
        case('two-parents-same-idempotency-key',[acquire,{'action':'acquire','as':'duplicate','holder':'parent-b','identity_changes':{'operation_id':edge.b64url(bytes([77])*16)},'created':False,'same_as':'first'}],'CLAIMED',0),
        case('key-reused-for-changed-body',[acquire,{'action':'acquire','as':'duplicate','holder':'parent-b','identity_changes':{'request_fingerprint':'b'*64},'expected_error':'IDEMPOTENCY_CONFLICT'}],'CLAIMED',0),
        case('lost-reservation-response-prevents-takeover',[acquire,begin,{'action':'takeover','claim':'first','holder':'parent-a','fence':1,'new_holder':'parent-b','expired':True,'expected_error':'LEASE_CONFLICT'},altered(begin,expected_error='EXECUTION_IN_PROGRESS')],'CLAIMED',1),
        case('reservation-progress-survives-holder-expiry',[acquire,begin,reserve,{'action':'takeover','claim':'first','holder':'parent-a','fence':1,'new_holder':'parent-b','expired':True,'expected_error':'LEASE_CONFLICT'}],'RESERVED',1),
        case('takeover-fences-old-holder',[acquire,{'action':'takeover','claim':'first','holder':'parent-a','fence':1,'new_holder':'parent-b','expired':True},altered(begin,expected_error='LEASE_CONFLICT'),altered(begin,holder='parent-b',fence=2)],'CLAIMED',1),
        case('generation-race-rejected',[acquire,altered(begin,current_generation='g2',expected_error='INSTANCE_GENERATION_STALE')],'CLAIMED',0),
        case('compatible-fallback-after-owner-release',[acquire,begin,reserve,{'action':'release_before_dispatch','claim':'first','holder':'parent-a','fence':1,'owner_confirmed':True},begin,reserve],'RESERVED',2),
        case('retry-budget-across-fallback',[acquire,altered(begin,budget=1),reserve,{'action':'release_before_dispatch','claim':'first','holder':'parent-a','fence':1,'owner_confirmed':True},altered(begin,budget=1,expected_error='RETRY_BUDGET_EXHAUSTED')],'CLAIMED',1),
        case('ambiguous-send-before-response-never-replays',[acquire,begin,reserve,dispatch,{'action':'release_before_dispatch','claim':'first','holder':'parent-a','fence':1,'owner_confirmed':True,'expected_error':'EXECUTION_OUTCOME_UNKNOWN'},{'action':'terminal','claim':'first','holder':'parent-a','fence':1,'reason':'EXECUTION_OUTCOME_UNKNOWN'},{'action':'acquire','as':'retry','holder':'parent-b','created':False,'same_as':'first'},altered(begin,expected_error='EXECUTION_IN_PROGRESS')],'TERMINAL',1),
        case('partial-stream-never-replays',[acquire,begin,reserve,dispatch,{'action':'mark_response_started','claim':'first','holder':'parent-a','fence':1},{'action':'terminal','claim':'first','holder':'parent-a','fence':1,'reason':'PARTIAL_STREAM_FAILURE'},altered(dispatch,expected_error='EXECUTION_IN_PROGRESS')],'TERMINAL',1),
        case('cancel-requires-owner-confirmed-stop',[acquire,begin,reserve,{'action':'terminal','claim':'first','holder':'parent-a','fence':1,'reason':'CLIENT_CANCELLED','expected_error':'EXECUTION_OUTCOME_UNKNOWN'},{'action':'terminal','claim':'first','holder':'parent-a','fence':1,'reason':'CLIENT_CANCELLED','owner_confirmed':True}],'TERMINAL',1)
    ]
    write('conformance/alias-execution-vectors.json',doc)
    write('fixtures/valid/alias-inference-assertion.json',known[0]['envelope'])
    write('fixtures/valid/alias-execution-identity.json',identity)
    write('fixtures/valid/alias-execution-claim.json',claim)
    for name,mutate in [('missing-reservation',lambda v:v.pop('reservation_id')),('zero-fence',lambda v:v.update(fencing_token=0)),('response-before-dispatch',lambda v:v.update(response_started=True)),('unbounded-attempts',lambda v:v.update(attempt_count=9)),('terminal-without-reason',lambda v:v.update(state='TERMINAL'))]:
        v=copy.deepcopy(claim);mutate(v);write('fixtures/invalid/alias-execution-claim-'+name+'.json',v)
    for name,mutate in [('management-target',lambda v:v.update(request_target='/inferweave/v1/aliases')),('unsigned-tenant-authority',lambda v:v.update(tenant_id='foreign')),('missing-operation',lambda v:v.pop('operation_id'))]:
        v=copy.deepcopy(known[0]['envelope']);mutate(v);write('fixtures/invalid/alias-inference-assertion-'+name+'.json',v)

if __name__=='__main__': generate()
