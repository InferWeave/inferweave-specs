"""Offline spec 63 oracle: the upstream-role Hello, acknowledgement, catalog and refused frames and
the request-meta traffic class. No network, key store, admission or routing implementation.

The JSON Schemas under schemas/v1/requests/link-upstream-*.json carry the shapes. This module
carries what a schema cannot: strict decoding (a duplicate member is refused, not last-wins), the
duplicate model id of a catalog, the dialer's same-socket acknowledgement check and the
traffic-class order. Production conformance remains owed (see OPEN_GATES.md)."""
import json
import re
from pathlib import Path

from jsonschema import Draft7Validator, RefResolver

from link_http_json import strict_json

ROOT = Path(__file__).resolve().parents[1]
STORE = {}
for _path in (ROOT / 'schemas/v1').rglob('*.json'):
    _schema = json.loads(_path.read_text())
    STORE[_schema['$id']] = _schema

#: frame `kind` -> schema name under schemas/v1/requests/
KIND_SCHEMA = {
    'hello': 'link-upstream-hello',
    'upstream_ack': 'link-upstream-hello-ack',
    'upstream_catalog': 'link-upstream-catalog',
    'upstream_catalog_request': 'link-upstream-catalog-request',
    'refused': 'link-upstream-refused',
    'request': 'link-http-request',
}
FEATURES = {'iw.link-upstream/1', 'iw.link-http-json/1'}
REFUSALS_REVERSIBLE = {'rate_limited', 'concurrency_limited', 'token_budget_exceeded', 'backend_unavailable'}
#: private is the more restrictive class; an unrecognised value reads as private.
CLASS_ORDER = {'private': 0, 'shareable': 1}


def validate(name, value):
    schema = STORE[f'https://inferweave.dev/schemas/v1/requests/{name}.json']
    Draft7Validator(schema, resolver=RefResolver.from_schema(schema, store=STORE)).validate(value)


def semantic_errors(frame):
    """Rules a schema cannot express; call only on a schema-valid frame."""
    errors = []
    if frame.get('kind') == 'upstream_catalog':
        ids = [entry['model_id'] for entry in frame['models']]
        if len(ids) != len(set(ids)):
            errors.append('catalog lists a model id twice')
    return errors


def decode_frame(raw):
    """Strictly decode one frame's JSON text and validate it against the schema its kind names.
    Raises on a duplicate member, a non-finite number, an unknown kind, a schema or a semantic error."""
    frame = strict_json(raw)
    if not isinstance(frame, dict) or frame.get('kind') not in KIND_SCHEMA:
        raise ValueError('unknown frame kind')
    validate(KIND_SCHEMA[frame['kind']], frame)
    errors = semantic_errors(frame)
    if errors:
        raise ValueError('; '.join(errors))
    return frame


def effective_class(declared, ceiling):
    """The more restrictive of the dialer's declared class and the key's ceiling. An undeclared,
    absent or unrecognised declared class is private; the ceiling is the operator's and is trusted."""
    declared = declared if declared in CLASS_ORDER else 'private'
    return min(declared, ceiling, key=lambda name: CLASS_ORDER[name])


def dialer_accepts_ack(hello, ack):
    """May the dialer enable upstream on this acknowledgement? The ack was read from the socket that sent
    the hello. Both frames must be schema-valid, the incarnation id must echo, only the asked-for role is
    granted (and never serve), and no feature beyond those offered is negotiated."""
    try:
        validate('link-upstream-hello', hello)
        validate('link-upstream-hello-ack', ack)
    except Exception:
        return False
    return (ack['link_incarnation_id'] == hello['link_incarnation_id']
            and ack['granted_roles'] == ['upstream']
            and 'upstream' in hello['link_roles']
            and set(ack['negotiated_features']) <= set(hello['native_link_features']))


def request_with_class(declared):
    """A schema-valid spec 59 request frame whose meta carries `declared` (or none when it is absent)."""
    payload = '{"model":"m1","messages":[]}'
    meta = {'http': {'version': 1, 'method': 'POST', 'target': '/v1/chat/completions',
                     'content_type': 'application/json', 'payload_bytes': len(payload.encode())}}
    if declared is not ABSENT:
        meta['traffic_class'] = declared
    return {'kind': 'request', 'request_id': 'up-1', 'payload': payload, 'meta': meta}


ABSENT = object()


def check_vectors(root=ROOT):
    errors = []
    document = json.loads((root / 'conformance/link-upstream-vectors.json').read_text())
    for case in document['wire_cases']:
        try:
            decode_frame(case['wire'])
            refused = False
        except Exception:
            refused = True
        if refused == case['valid']:
            errors.append(f"link upstream wire vector {case['name']} disagrees")
    for case in document['request_class_cases']:
        declared = case['declared'] if 'declared' in case else ABSENT
        try:
            validate('link-http-request', request_with_class(declared))
            refused = False
        except Exception:
            refused = True
        if refused == case['valid']:
            errors.append(f"link upstream request-class vector {case['name']} disagrees")
    for case in document['effective_class_cases']:
        got = effective_class(case.get('declared'), case['ceiling'])
        if got != case['effective']:
            errors.append(f"link upstream class vector {case['name']} gives {got}")
    for case in document['ack_pairing_cases']:
        if dialer_accepts_ack(case['hello'], case['ack']) != case['accepted']:
            errors.append(f"link upstream ack pairing vector {case['name']} disagrees")
    for case in document['refusal_cases']:
        if (case['code'] in REFUSALS_REVERSIBLE) != case['reversible']:
            errors.append(f"link upstream refusal vector {case['name']} disagrees")
    return errors
