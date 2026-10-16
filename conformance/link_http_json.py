"""Offline spec59 oracle. No network, backend, admission or routing implementation."""
import json
import re
from pathlib import Path

from jsonschema import Draft7Validator, RefResolver

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / 'contracts/protocol-v1/link-http-json.json').read_text())
CAPABILITY = CONTRACT['capability']
STORE = {}
for path in (ROOT / 'schemas/v1').rglob('*.json'):
    schema = json.loads(path.read_text())
    STORE[schema['$id']] = schema


def validate(name, value):
    schema = STORE[f'https://inferweave.dev/schemas/v1/requests/{name}.json']
    Draft7Validator(schema, resolver=RefResolver.from_schema(schema, store=STORE)).validate(value)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    def constant(_):
        raise ValueError('nonfinite')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    # Reject decoded escaped surrogates, including nested keys/values.
    json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
    return value


def mime_valid(value, response=False):
    media = r'(?:application/json|text/event-stream)' if response else r'application/json'
    return isinstance(value, str) and bool(re.fullmatch(
        media + r'(?:[ \t]*;[ \t]*charset[ \t]*=[ \t]*(?:utf-8|"utf-8"))?', value,
        re.ASCII | re.IGNORECASE))


def request_valid(frame, max_request_bytes=None):
    validate('link-http-request', frame)
    http = frame['meta']['http']
    body = frame['payload'].encode('utf-8')
    limit = CONTRACT['default_max_request_bytes'] if max_request_bytes is None else max_request_bytes
    if not (0 < len(body) <= limit) or len(body) != http['payload_bytes']:
        raise ValueError('payload length')
    if not mime_valid(http['content_type']) or not isinstance(strict_json(body), dict):
        raise ValueError('JSON MIME/object required')
    return body


def bound_for_dispatch(registration, hello, ack, current_link, local_features):
    """Atomic binding predicate; callers must synchronize selection/check/enqueue."""
    try:
        validate("link-hello", hello)
        validate("link-hello-ack", ack)
    except Exception:
        return False
    return bool(registration and ack and current_link
        and registration.get('fresh') and registration.get('credential_valid')
        and current_link.get('live') and current_link.get('current')
        and ack.get('binding_status') == 'bound'
        and ack.get('kind') == 'hello_ack' and ack.get('native_link_version') == 1
        and hello.get('native_link_version') == 1
        and registration.get('connection_id') == hello.get('registration_connection_id')
        == ack.get('registration_connection_id') == current_link.get('registration_connection_id')
        and hello.get('link_incarnation_id') == ack.get('link_incarnation_id')
        == current_link.get('incarnation_id')
        and all(CAPABILITY in features for features in (
            registration.get('capabilities', []), hello.get('native_link_features', []),
            ack.get('negotiated_features', []), local_features)))


class Response:
    """One-request bounded stream validator; returns bytes and never accumulates a body."""
    def __init__(self, request_id):
        self.request_id = request_id
        self.sequence = 0
        self.head = None
        self.terminal = False
        self.outcome = None
        self.failure = None

    def disconnected(self, cancelled=False):
        if not self.terminal:
            self.terminal = True
            self.failure = "CLIENT_CANCELLED" if cancelled else "BACKEND_STREAM_FAILED"
            self.outcome = "cancelled" if cancelled else "partial_failure" if self.head else 502

    def accept(self, raw):
        try:
            if self.terminal:
                raise ValueError('frame after terminal')
            if len(raw.encode('utf-8')) > CONTRACT['max_frame_json_bytes']:
                raise ValueError('frame limit')
            frame = strict_json(raw)
            if frame.get('request_id') != self.request_id:
                raise ValueError('request identity')
            if frame.get('kind') == 'token':
                validate('link-http-token', frame)
                if frame['seq'] != self.sequence:
                    raise ValueError('sequence')
                if self.sequence == 0:
                    if frame['payload'] != '' or 'response_head' not in frame:
                        raise ValueError('head before body')
                    head = frame['response_head']
                    if not mime_valid(head['content_type'], response=True):
                        raise ValueError('response MIME')
                    headers = head.get('headers', {})
                    correlation = headers.get('x-inferweave-request-id')
                    if correlation is not None and (
                        not isinstance(correlation, str)
                        or re.fullmatch(r'[!-~]{1,256}', correlation) is None
                    ):
                        raise ValueError('request-id header')
                    retry_after = headers.get('retry-after')
                    if retry_after is not None and (
                        not isinstance(retry_after, str)
                        or re.fullmatch(r'(0|[1-9][0-9]{0,9})', retry_after) is None
                        or head['status'] not in (429, 503)
                    ):
                        raise ValueError('retry-after header/status')
                    self.head = head
                elif any(key in frame for key in ('response_head', 'queue_ms', 'queue_hops')):
                    raise ValueError('repeated head')
                elif self.head['status'] == 204 and frame['payload']:
                    raise ValueError('204 body')
                self.sequence += 1
                return frame['payload'].encode('utf-8')
            validate('link-http-end', frame)
            if 'failure' not in frame and self.head is None:
                raise ValueError('missing head')
            self.terminal = True
            if 'failure' in frame:
                self.failure = frame['failure']['code']
                self.outcome = ('partial_failure' if self.head is not None else
                    'cancelled' if self.failure == 'CLIENT_CANCELLED' else
                    504 if self.failure == 'BACKEND_TIMEOUT' else 502)
            else:
                self.outcome = 'complete'
            return b''
        except Exception:
            self.terminal = True
            self.failure = 'INVALID_UPSTREAM_RESPONSE'
            self.outcome = 'partial_failure' if self.head is not None else 502
            raise


def dispatch_mode(target, bound):
    if target not in CONTRACT['targets']:
        return 'FEATURE_UNSUPPORTED'
    if bound:
        return 'http'
    return 'legacy_chat' if target == '/v1/chat/completions' else 'FEATURE_UNSUPPORTED'


def check_vectors(root=ROOT):
    errors = []
    for case in json.loads((root / 'conformance/link-http-json-vectors.json').read_text())['cases']:
        response = Response('r1')
        failed = False
        try:
            for frame in case['frames']:
                response.accept(json.dumps(frame))
        except Exception:
            failed = True
        if failed != case['invalid'] or response.outcome != case['outcome']:
            errors.append(f"link HTTP vector {case['name']} disagrees")
    for case in json.loads((root / 'conformance/link-http-json-vectors.json').read_text())['request_cases']:
        if request_decision(case['request'], case['bound']) != case['expected']:
            errors.append(f"link HTTP request vector {case['name']} disagrees")
    return errors


def request_decision(frame, bound):
    """Preserve existing legacy completions stream rejection before transport dispatch."""
    try:
        request_valid(frame)
    except Exception:
        return {'dispatch_allowed': False, 'refused': 'invalid_http_request'}
    if (frame['meta']['http']['target'] not in CONTRACT['streaming_targets']
            and strict_json(frame['payload']).get('stream') is True):
        return {'dispatch_allowed': False, 'status': 400, 'code': 'stream_unsupported'}
    mode = dispatch_mode(frame['meta']['http']['target'], bound)
    if mode == 'FEATURE_UNSUPPORTED':
        return {'dispatch_allowed': False, 'status': 503, 'code': mode}
    return {'dispatch_allowed': True, 'mode': mode}
