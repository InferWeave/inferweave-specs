"""Golden and hostile offline transport contract checks; production proof remains owed."""
import copy
import json
import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

from conformance.link_http_json import (
    CONTRACT, CAPABILITY, Response, bound_for_dispatch, request_valid, validate, dispatch_mode, request_decision,
)
from conformance.runtime_protocol import negotiate_native_link

ROOT = Path(__file__).resolve().parents[2]


class LinkHttpContract(unittest.TestCase):
    def request(self, payload=' {"model":"exact@rev","prompt":"é"}\n'):
        return {'kind':'request','request_id':'r1','payload':payload,'meta':{'http':{
            'version':1,'method':'POST','target':'/v1/completions',
            'content_type':'application/json','payload_bytes':len(payload.encode())}}}

    def test_golden_hostile_streams(self):
        cases=json.loads((ROOT/'conformance/link-http-json-vectors.json').read_text())['cases']
        self.assertGreaterEqual(len(cases), 25)
        for case in cases:
            with self.subTest(case=case['name']):
                response=Response('r1')
                chunks=[]
                def run():
                    for frame in case['frames']:
                        chunks.append(response.accept(json.dumps(frame)))
                if case['invalid']:
                    with self.assertRaises(Exception): run()
                else:
                    run()
                    expected=''.join(f.get('payload','') for f in case['frames']).encode()
                    self.assertEqual(b''.join(chunks),expected)
                self.assertEqual(response.outcome,case['outcome'])
                self.assertTrue(response.terminal)

    def test_allowed_headers_reject_control_bytes_in_schema_and_oracle(self):
        cases=json.loads((ROOT/'conformance/link-http-json-vectors.json').read_text())['cases']
        for case in cases:
            if not case['name'].startswith(('x-inferweave-request-id_', 'retry-after_')):
                continue
            frame=case['frames'][0]
            with self.subTest(case=case['name'], guard='schema'):
                with self.assertRaises(Exception):
                    validate('link-http-response-head',frame['response_head'])
            # Independently exercise semantic validation: schema removal must not
            # permit committing an HTTP head with an injected header value.
            with self.subTest(case=case['name'], guard='semantic'):
                response=Response('r1')
                with patch('conformance.link_http_json.validate',return_value=None):
                    with self.assertRaises(Exception):response.accept(json.dumps(frame))
                self.assertIsNone(response.head)
                self.assertEqual(response.outcome,502)

    def test_request_exact_utf8_bytes_and_mime(self):
        for target in CONTRACT['targets']:
            frame=self.request();frame['meta']['http']['target']=target
            frame['meta']['http']['content_type']='Application/JSON;\tcharset="UTF-8"'
            self.assertEqual(request_valid(frame),frame['payload'].encode())

    def test_forbidden_request_modes_and_targets(self):
        for key,value in [('target','https://evil/v1/completions'),('target','/v1/completions?x=1'),
                          ('target','/v1/%63ompletions'),('method','GET'),('version',2),
                          ('payload_bytes',1),('content_type','text/plain'),('endpoint','/v1/completions')]:
            frame=self.request();frame['meta']['http'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(Exception): request_valid(frame)
        for key in ('native','ownerExecutionPermit','executable'):
            frame=self.request();frame['meta'][key]={}
            with self.subTest(key=key),self.assertRaises(Exception):request_valid(frame)

    def test_malformed_json_and_resource_limits(self):
        for payload in ('[]','{"a":1,"a":2}','{"x":{"a":1,"a":2}}','{"x":NaN}','{"x":1e999}','{"x":"\\ud800"}','{}{}'):
            with self.subTest(payload=payload),self.assertRaises(Exception):request_valid(self.request(payload))
        frame=self.request()
        with self.assertRaises(Exception):request_valid(frame,max_request_bytes=len(frame['payload'].encode())-1)
        self.assertEqual(request_valid(frame,max_request_bytes=len(frame['payload'].encode())),frame['payload'].encode())

    def test_existing_32mib_default_not_narrowed(self):
        self.assertEqual(CONTRACT['default_max_request_bytes'],32<<20)
        frame=self.request(json.dumps({'prompt':'a'*(17<<20)}))
        self.assertEqual(len(request_valid(frame)),len(frame['payload']))

    def test_control_duplicate_keys_and_frame_limit(self):
        for raw in ('{"kind":"end","kind":"token","request_id":"r1"}',
                    json.dumps({'kind':'token','request_id':'r1','seq':0,'payload':'x'*(1<<20)})):
            with self.assertRaises(Exception):Response('r1').accept(raw)

    def binding(self):
        registration={'connection_id':'c-0123456789abcdef','fresh':True,'credential_valid':True,'capabilities':[CAPABILITY]}
        hello={'kind':'hello','node_id':'node','role':'node','credential':'fixture',
               'native_link_version':1,'registration_connection_id':registration['connection_id'],
               'link_incarnation_id':'unique-socket-0001','native_link_features':[CAPABILITY]}
        ack=negotiate_native_link(registration,hello,[CAPABILITY])
        link={'registration_connection_id':registration['connection_id'],'incarnation_id':hello['link_incarnation_id'],'live':True,'current':True}
        return registration,hello,ack,link,[CAPABILITY]

    def test_http_only_handshake_and_binding(self):
        args=self.binding()
        validate('link-hello',args[1]);validate('link-hello-ack',args[2])
        self.assertTrue(bound_for_dispatch(*args))
        self.assertEqual(args[2]['negotiated_features'],[CAPABILITY])

    def test_each_binding_source_required_and_revoked(self):
        changes=[(0,'fresh',False),(0,'credential_valid',False),(0,'connection_id','c-2222222222222222'),
                 (0,'capabilities',[]),(1,'registration_connection_id',None),(1,'link_incarnation_id',None),(1,'native_link_features',[]),(2,'negotiated_features',[]),
                 (2,'link_incarnation_id','different-dial-123'),(2,'binding_status','unbound'),
                 (3,'live',False),(3,'current',False),(3,'incarnation_id','new-dial-12345678')]
        for index,key,value in changes:
            args=list(copy.deepcopy(self.binding()));args[index][key]=value
            with self.subTest(index=index,key=key):self.assertFalse(bound_for_dispatch(*args))
        args=list(self.binding());args[4]=[];self.assertFalse(bound_for_dispatch(*args))

    def test_socket_loss_cancellation_and_terminal_rejection(self):
        for cancelled in (False,True):
            for with_head in (False,True):
                response=Response("r1")
                if with_head:
                    response.accept(json.dumps({"kind":"token","request_id":"r1","seq":0,"payload":"",
                        "response_head":{"status":200,"content_type":"text/event-stream"}}))
                response.disconnected(cancelled)
                self.assertEqual(response.outcome,"cancelled" if cancelled else "partial_failure" if with_head else 502)
                with self.assertRaises(Exception):response.accept(json.dumps({"kind":"end","request_id":"r1"}))

    def test_legacy_completions_streaming_contract(self):
        fixtures=json.loads((ROOT/'conformance/link-http-json-vectors.json').read_text())
        for case in fixtures['request_cases']:
            with self.subTest(case=case['name']):
                self.assertEqual(request_decision(case['request'],case['bound']),case['expected'])
                if 'response_case' in case:
                    response_case=next(c for c in fixtures['cases'] if c['name']==case['response_case'])
                    self.assertEqual(response_case['frames'][0]['response_head'],
                                     {'status':200,'content_type':'application/json'})
        # Legacy stream rejection must also happen before old-peer fallback.
        request=fixtures['request_cases'][1]['request']
        self.assertEqual(request_decision(request,False),
                         {'dispatch_allowed':False,'status':400,'code':'stream_unsupported'})

    def test_downgrade_is_explicit_before_dispatch(self):
        self.assertEqual(dispatch_mode("/v1/completions",False),"FEATURE_UNSUPPORTED")
        self.assertEqual(dispatch_mode("/v1/chat/completions",False),"legacy_chat")
        self.assertEqual(dispatch_mode("/v1/completions",True),"http")

    def test_legacy_and_no_common_feature(self):
        registration,hello,*_=self.binding()
        self.assertIsNone(negotiate_native_link(registration,{'kind':'hello'},[CAPABILITY]))
        ack=negotiate_native_link(registration,hello,['iw.link-native-request/1'])
        self.assertEqual(ack['binding_status'],'unbound')
        self.assertEqual(ack['negotiated_features'],[])


if __name__=='__main__':unittest.main()
