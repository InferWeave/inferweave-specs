"""Offline spec57 transport classifier; not an HTTP parser or authorizer."""
import json
import re
from pathlib import Path

TOKEN = r"[A-Za-z0-9!#$%&'*+.^_`|~\-]+"
PARAMETER = re.compile(r' *(' + TOKEN + r') *= *("(?:[ !#-\[\]-~]|\\["\\])*"|' + TOKEN + r') *(?:;|$)')
OPTIONAL_FIELDS = {'session_id', 'timeout_ms', 'capabilities', 'min_context',
                   'prefer_family', 'queue', 'tenant_selector', 'idempotency_key'}
CORRELATION = 'x-inferweave-request-id'


def text(value, maximum, empty=False):
    return (isinstance(value, str) and (empty or bool(value))
            and len(value) <= maximum and value == value.strip()
            and all(ord(c) >= 32 and not 127 <= ord(c) <= 159
                    and not 0xD800 <= ord(c) <= 0xDFFF for c in value))


def accepts_mime(raw, target):
    if not text(raw, 1024) or not raw.isascii():
        return False
    kind, _, tail = raw.partition(';')
    kind = kind.rstrip(' ').lower()
    if kind != 'application/json' and not (kind == 'multipart/form-data'
                                          and target == '/v1/audio/transcriptions'):
        return False
    parameters = {}
    while tail:
        match = PARAMETER.match(tail)
        if match is None:
            return False
        name, value = match.groups()
        name = name.lower()
        if '*' in name or name in parameters:
            return False
        if value.startswith('"'):
            value = re.sub(r'\\(["\\])', r'\1', value[1:-1])
        parameters[name] = value
        tail = tail[match.end():]
    if kind == 'multipart/form-data':
        boundary = parameters.get('boundary', '')
        return (1 <= len(boundary) <= 70 and not boundary.endswith(' ')
                and re.fullmatch(r"[A-Za-z0-9'()+_,./:=? \-]+", boundary) is not None)
    return True


def accepts_headers(case, bound_headers):
    """Validate the fixture's additions to an otherwise valid signed request."""
    optional = {bound_headers[field].lower() for field in OPTIONAL_FIELDS}
    allowed = {name.lower() for name in bound_headers.values()}
    allowed.update({CORRELATION, 'inferweave-inference-assertion'})
    seen = set()
    for name, value in case['headers']:
        lower = name.lower()
        if (re.fullmatch(r'[A-Za-z0-9-]+', name) is None or lower in seen
                or not text(value, 8192, lower in optional)):
            return False
        if lower == CORRELATION and len(value.encode('utf-8')) > 8192:
            return False
        if lower.startswith(('inferweave-', 'x-inferweave-')) and lower not in allowed:
            return False
        seen.add(lower)
    return set(case['empty_fields']) <= OPTIONAL_FIELDS


def check_vectors(root):
    root = Path(root)
    vectors = json.loads((root/'conformance/alias-inference-transport-vectors.json').read_text())
    contract = json.loads((root/'contracts/protocol-v1/alias-execution.json').read_text())
    errors = []
    if vectors.get('schema_version') != 1:
        errors.append('unsupported inference transport fixture version')
    for case in vectors['mime_cases']:
        if accepts_mime(case['content_type'], case['target']) != case['accepted']:
            errors.append(case['id'] + ': MIME classification mismatch')
    for case in vectors['header_cases']:
        if accepts_headers(case, contract['bound_headers']) != case['accepted']:
            errors.append(case['id'] + ': header classification mismatch')
    return errors
