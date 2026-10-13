"""Offline signature transcript/transport reference. Never use fixture secrets in production.

Reuses the existing dependency-free Ed25519 fixture algorithm, not a production verifier,
request authenticator, grant store or replay database. Actual security acceptance remains owed.
"""
import base64
import json
import struct
from pathlib import Path
import node_join

DOMAIN = b'inferweave.edge-alias-delegation/v1\x00'
FIELDS = ('edge_id', 'key_id', 'audience', 'idp_issuer', 'subject', 'issued_at_unix_ms',
          'expires_at_unix_ms', 'nonce', 'method', 'request_target', 'body_sha256',
          'if_match', 'if_none_match', 'idempotency_key', 'alias_level', 'deadline_unix_ms')
INTEGER_FIELDS = {'issued_at_unix_ms', 'expires_at_unix_ms', 'deadline_unix_ms'}


def b64url(data):
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def decode_base64(value):
    if not isinstance(value, str) or not value or '=' in value:
        raise ValueError('noncanonical base64url')
    try:
        raw = base64.b64decode(value + '=' * ((-len(value)) % 4), altchars=b'-_', validate=True)
    except Exception as error:
        raise ValueError('invalid base64url') from error
    if b64url(raw) != value:
        raise ValueError('noncanonical base64url')
    return raw


def transcript(claim):
    if type(claim.get('version')) is not int or claim['version'] != 1:
        raise ValueError('unsupported envelope version')
    result = bytearray(DOMAIN)
    for field in FIELDS:
        value = claim[field]
        if field in INTEGER_FIELDS:
            if type(value) is not int or not 1 <= value <= 9007199254740991:
                raise ValueError('noncanonical integer')
            value = str(value)
        if not isinstance(value, str):
            raise ValueError('field must be text')
        encoded = value.encode('utf-8')
        result.extend(struct.pack('>I', len(encoded)))
        result.extend(encoded)
    return bytes(result)


def _unique_members(pairs):
    value = {}
    for key, entry in pairs:
        if key in value:
            raise ValueError('duplicate JSON member')
        value[key] = entry
    return value


def decode_header(header):
    if len(header) > 8192:
        raise ValueError('assertion too large')
    value = json.loads(decode_base64(header).decode('utf-8'), object_pairs_hook=_unique_members)
    if not isinstance(value, dict) or set(value) != set(FIELDS) | {'version', 'signature'}:
        raise ValueError('unexpected assertion fields')
    transcript(value)
    if len(decode_base64(value['signature'])) != 64 or len(decode_base64(value['nonce'])) != 16:
        raise ValueError('wrong cryptographic field size')
    return value


def check_vectors(root):
    doc = json.loads((Path(root) / 'conformance/alias-edge-delegation-vectors.json').read_text())
    if doc['domain_hex'] != DOMAIN.hex() or doc['fields'] != list(FIELDS):
        return ['edge delegation transcript definition drift']
    errors = []
    for case in doc['known_answers']:
        seed = bytes.fromhex(case['test_seed_hex'])
        claim = case['envelope']
        wire = transcript(claim)
        public = node_join.ed25519_public(seed)
        signature = node_join.ed25519_sign(seed, wire)
        if public.hex() != case['public_key_hex'] or wire.hex() != case['transcript_hex']:
            errors.append(case['id'] + ': transcript/public key mismatch')
        if b64url(signature) != claim['signature']:
            errors.append(case['id'] + ': signature mismatch')
        if not node_join.ed25519_verify(public, wire, signature):
            errors.append(case['id'] + ': signature verification failed')
        if decode_header(case['header']) != claim:
            errors.append(case['id'] + ': header mismatch')
    return errors
