"""Reference model for the spec 47 node-join contract (hardware registration + enrollment).

Dependency-free on purpose (the CI installs only jsonschema and pyyaml):

- `proof_transcript` builds the exact bytes a tokenless-enrollment proof signs.
- `ed25519_*` is the RFC 8032 section 6 reference algorithm in plain Python, used only to
  recompute and re-verify the known-answer vectors; it is NOT constant-time and must never be
  used to protect a secret.
- `register_decision` applies the spec 47 registration rules that do not depend on a gateway's
  baseline validation (the `hardware` field, hardware-only registration, `assignments`).

The vectors in conformance/node-join-vectors.json are run against a real gateway over HTTP by
its own test suite; this module proves they are self-consistent and that the known answers are
reproducible from the seed.
"""
import hashlib
import json
import re
import struct

PROOF_DOMAIN = "iw-proof-enrollment-v1"
MAX_HARDWARE_BYTES = 65536
I64_MIN, I64_MAX = -(2**63), 2**63 - 1


# --- transcript -----------------------------------------------------------------------------
def _field(b):
    return struct.pack(">I", len(b)) + b


def _optional(v):
    return b"\x00" if v is None else b"\x01" + _field(v.encode("utf-8"))


def proof_transcript(challenge_id, nonce, claim):
    """spec 47 section 5.4; mirrors iw_core::signature::proof_transcript."""
    if not 0 <= nonce < 2**64:
        raise ValueError("nonce must be an unsigned 64-bit integer")
    return (
        _field(PROOF_DOMAIN.encode())
        + _field(challenge_id.encode("utf-8"))
        + struct.pack(">Q", nonce)
        + _field(claim["role"].encode("utf-8"))
        + _optional(claim.get("model"))
        + _optional(claim.get("contextClass"))
        + _optional(claim.get("resourceClaim"))
    )


# --- Ed25519 (RFC 8032 reference) ----------------------------------------------------------
_P = 2**255 - 19
_D = -121665 * pow(121666, -1, _P) % _P
_Q = 2**252 + 27742317777372353535851937790883648493


def _recover_x(y, sign):
    x2 = (y * y - 1) * pow(_D * y * y + 1, -1, _P) % _P
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P:
        x = x * pow(2, (_P - 1) // 4, _P) % _P
    if x & 1 != sign:
        x = _P - x
    return x


_BY = 4 * pow(5, -1, _P) % _P
_BX = _recover_x(_BY, 0)
_B = (_BX, _BY, 1, _BX * _BY % _P)


def _add(a, b):
    A = (a[1] - a[0]) * (b[1] - b[0]) % _P
    B = (a[1] + a[0]) * (b[1] + b[0]) % _P
    C = 2 * a[3] * b[3] * _D % _P
    D = 2 * a[2] * b[2] % _P
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _P, G * H % _P, F * G % _P, E * H % _P)


def _mul(s, pt):
    r = (0, 1, 1, 0)
    while s:
        if s & 1:
            r = _add(r, pt)
        pt = _add(pt, pt)
        s >>= 1
    return r


def _enc(pt):
    zi = pow(pt[2], -1, _P)
    x, y = pt[0] * zi % _P, pt[1] * zi % _P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _dec(b):
    y = int.from_bytes(b, "little")
    sign, y = y >> 255, y & ((1 << 255) - 1)
    x = _recover_x(y, sign)
    return (x, y, 1, x * y % _P)


def _expand(seed):
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def ed25519_public(seed):
    return _enc(_mul(_expand(seed)[0], _B))


def ed25519_sign(seed, msg):
    a, prefix = _expand(seed)
    pub = _enc(_mul(a, _B))
    r = int.from_bytes(hashlib.sha512(prefix + msg).digest(), "little") % _Q
    big_r = _enc(_mul(r, _B))
    k = int.from_bytes(hashlib.sha512(big_r + pub + msg).digest(), "little") % _Q
    return big_r + int.to_bytes((r + k * a) % _Q, 32, "little")


def ed25519_verify(pub, msg, sig):
    if len(pub) != 32 or len(sig) != 64:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= _Q:
        return False
    k = int.from_bytes(hashlib.sha512(sig[:32] + pub + msg).digest(), "little") % _Q
    left = _mul(s, _B)
    right = _add(_dec(sig[:32]), _mul(k, _dec(pub)))
    return (left[0] * right[2] - right[0] * left[2]) % _P == 0 and (
        left[1] * right[2] - right[1] * left[2]
    ) % _P == 0


def check_known_answers(kat):
    """Recompute every known answer from the seed; return a list of error strings."""
    errors = []
    seed = bytes.fromhex(kat["seedHex"])
    if ed25519_public(seed).hex() != kat["publicKeyHex"]:
        errors.append("publicKeyHex does not derive from seedHex")
    for case in kat["cases"]:
        cid = case["id"]
        nonce = case["nonce"]
        if not isinstance(nonce, int) or isinstance(nonce, bool):
            errors.append(f"{cid}: nonce must be a JSON integer")
            continue
        transcript = proof_transcript(case["challengeId"], nonce, case["claim"])
        if transcript.hex() != case["transcriptHex"]:
            errors.append(f"{cid}: transcriptHex drifted")
        sig = ed25519_sign(seed, transcript)
        if sig.hex() != case["signatureHex"]:
            errors.append(f"{cid}: signatureHex drifted")
        if not ed25519_verify(bytes.fromhex(kat["publicKeyHex"]), transcript, bytes.fromhex(case["signatureHex"])):
            errors.append(f"{cid}: signature does not verify")
        for mutation, (a, n, c) in {
            "challenge id": (case["challengeId"] + "0", nonce, case["claim"]),
            "nonce": (case["challengeId"], nonce ^ 1, case["claim"]),
            "role": (case["challengeId"], nonce, dict(case["claim"], role=case["claim"]["role"] + "x")),
        }.items():
            if ed25519_verify(bytes.fromhex(kat["publicKeyHex"]), proof_transcript(a, n, c), bytes.fromhex(case["signatureHex"])):
                errors.append(f"{cid}: signature still verifies after changing {mutation}")
    return errors


def challenge_decision(request):
    """spec 47 section 5.2: tokenless enrollment grants only the role `node`."""
    if request.get("role") == "node":
        return {"status": 200, "claimRole": "node"}
    return {"status": 400, "errorCode": "bad_request"}


def trust_decision(case):
    """spec 47 section 6.1: what a credential may do, by how it was earned."""
    if case.get("proofAttempt"):
        if case["credentialOrigin"] == "code":
            return {"status": 403, "errorCode": "forbidden", "operatorCredentialStillWorks": True}
        return {"status": 401, "errorCode": "control_auth_failed"}
    body = {"endpoint": "", "models": [], "deployment": ""}
    body.update(case.get("register", {}))
    hw_only = is_hardware_only(body)
    if case["credentialOrigin"] == "proof" and not hw_only:
        return {"status": 403, "errorCode": "forbidden", "nodeAdmitted": False}
    return {"status": 200, "hardwareOnly": hw_only, "routable": (not hw_only) and bool(body["models"])}


def derived_node_id(public_key_hex):
    """spec 47 section 5.2: node_ + first 16 lowercase hex of SHA-256 of the raw public key."""
    return "node_" + hashlib.sha256(bytes.fromhex(public_key_hex)).hexdigest()[:16]


def id_decision(case):
    """Tokenless /key accepts only the derived id; operator enrollment takes any id."""
    if case["path"] == "/v1/node/enroll":
        return {"status": 200}
    if case["request"]["nodeId"] == derived_node_id(case["request"]["publicKey"]):
        return {"status": 200}
    return {"status": 400, "errorCode": "bad_request"}


CHALLENGE_TTL = 900


REGISTER_BODY_CAP = 256 * 1024
ENROLLMENT_BODY_CAP = 16 * 1024


def size_decision(case):
    """spec 47 section 6.6: oversize bodies are refused before parsing (400 or 413)."""
    cap = REGISTER_BODY_CAP if case["route"] == "/v1/node/register" else ENROLLMENT_BODY_CAP
    return {"statusIn": [400, 413]} if case["bodyBytes"] > cap else {"statusIn": [200]}


class _Gateway:
    """A minimal state model of spec 47 sections 3.1, 5.2, 6.1 to 6.4 and 6.7."""

    def __init__(self):
        self.creds = {}      # (node, cred) -> origin
        self.owner = {}      # node -> {"origin", "cred"}
        self.known = set()
        self.reg = {}        # node -> {"cred","conn","hardware"}
        self.conns = 0
        self.pending = {}   # node -> {id, expires}
        self.clock = 0
        self.n = 0
        self.saved_ch = {}
        self.keyed = set()

    @staticmethod
    def _derived(node):
        return node.startswith("$derived:") or bool(re.fullmatch(r"node_[0-9a-f]{16}", node))

    def run(self, step):
        op, node = step["op"], step.get("node")
        if op == "advance":
            self.clock += step["seconds"]
            return {}
        if op == "key":
            if not self._derived(node):
                return {"status": 400, "errorCode": "bad_request"}
            self.keyed.add(node)
            return {"status": 200}
        if op == "telemetry":
            r = self.reg.get(node)
            own = self.owner.get(node, {})
            if r is None or r["conn"] != self.saved.get(step["conn"]):
                return {"status": 401}
            if r["hardwareOnly"] or own.get("origin") == "proof":
                return {"status": 403, "errorCode": "forbidden"}
            return {"status": 200}
        if op == "known":
            self.known.add(node)
            return {}
        if op == "challenge":
            if step.get("role") != "node":
                return {"status": 400, "errorCode": "bad_request"}
            if node in self.known or self.owner.get(node, {}).get("origin") == "operator":
                return {"status": 403, "errorCode": "forbidden"}
            if not self._derived(node):
                return {"status": 400, "errorCode": "bad_request"}
            cur = self.pending.get(node)
            if cur is None or cur["expires"] <= self.clock:  # idempotent until expiry
                self.n += 1
                cur = self.pending[node] = {"id": f"ch{self.n}", "expires": self.clock + CHALLENGE_TTL}
            if step.get("saveAs"):
                self.saved_ch[step["saveAs"]] = cur["id"]
            out = {"status": 200}
            if "sameAs" in step["expect"] and step["expect"]["sameAs"]:
                out["sameAs"] = step["expect"]["sameAs"] if cur["id"] == self.saved_ch[step["expect"]["sameAs"]] else None
            if "differsFrom" in step["expect"]:
                out["sameAs"] = None if cur["id"] != self.saved_ch[step["expect"]["differsFrom"]] else step["expect"]["differsFrom"]
                out["differsFrom"] = step["expect"]["differsFrom"]
            return out
        if op in ("proof", "proof_enroll"):
            if op == "proof_enroll":
                if not self._derived(node):
                    return {"status": 400, "errorCode": "bad_request"}
                r = self.run(dict(step, op="challenge", role="node"))
                if r["status"] != 200:
                    return r
            if node in self.known or self.owner.get(node, {}).get("origin") == "operator":
                return {"status": 403, "errorCode": "forbidden"}
            if node in self.owner:
                return {"status": 401, "errorCode": "control_auth_failed"}
            self.owner[node] = {"origin": "proof", "cred": step.get("cred", "proof1")}
            return {"status": 200}
        if op == "operator_enroll":
            if step["code"] != "valid":
                return {"status": 401}
            self.reg.pop(node, None)  # promotion drops registration, connection, hardware, links
            self.owner[node] = {"origin": "operator", "cred": step["cred"]}
            return {"status": 200}
        if op == "register":
            own = self.owner.get(node)
            if not own or own["cred"] != step["cred"]:
                return {"status": 401}
            if own["origin"] == "proof" and step.get("endpoint"):
                return {"status": 403, "errorCode": "forbidden"}
            self.conns += 1
            self.reg[node] = {"cred": step["cred"], "conn": f"c{self.conns}",
                              "hardware": bool(step.get("hardware")),
                              "hardwareOnly": not step.get("endpoint")}
            if step.get("saveConn"):
                self.saved = getattr(self, "saved", {})
                self.saved[step["saveConn"]] = self.reg[node]["conn"]
            return {"status": 200}
        if op == "heartbeat":
            r = self.reg.get(node)
            return {"status": 200 if r and r["conn"] == getattr(self, "saved", {}).get(step["conn"]) else 401}
        if op == "listing":
            return {"hardwarePresent": bool(self.reg.get(node, {}).get("hardware"))}
        raise ValueError(op)


def lifecycle_decisions(case):
    gw = _Gateway()
    return [gw.run(s) for s in case["steps"]]


# --- hardware field and hardware-only registration ------------------------------------------
class _Float(float):
    """Marks a JSON number written with a fraction or exponent (not an integer)."""


def parse_json(text):
    return json.loads(text, parse_float=lambda s: _Float(s))


def _compact_len(value):
    return len(json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def check_hardware(value):
    """Return None when `value` is acceptable, else an error string. spec 47 section 3.1."""
    if not isinstance(value, dict):
        return "hardware must be a JSON object"
    version = value.get("version")
    if isinstance(version, bool) or not isinstance(version, int) or not I64_MIN <= version <= I64_MAX:
        return "hardware.version must be an integer"
    if _compact_len(value) > MAX_HARDWARE_BYTES:
        return f"hardware exceeds {MAX_HARDWARE_BYTES} bytes"
    return None


def is_hardware_only(body):
    return body.get("models") == [] and body.get("endpoint") == "" and body.get("deployment") == ""


def build_hardware(case):
    """Materialise the `hardware` value of a vector case: (present, value)."""
    if "hardwareGen" in case:
        gen = case["hardwareGen"]
        value = dict(gen["base"])
        notes = list(value.get("notes", []))
        value["notes"] = notes
        pad_to = gen["padCompactBytesTo"]
        # grow the single pad note until the compact serialisation is exactly pad_to bytes
        notes.append("")
        need = pad_to - _compact_len(value)
        if need < 0:
            raise ValueError("base hardware already larger than the requested size")
        notes[-1] = "x" * need
        assert _compact_len(value) == pad_to
        return True, value
    if "hardwareJson" in case:
        return True, parse_json(case["hardwareJson"])
    if "hardware" in case:
        return True, case["hardware"]
    return False, None


def register_decision(baseline, case):
    """Apply spec 47 sections 3 and 4 to one vector case; return the expected observable."""
    body = dict(baseline)
    body.update(case.get("request", {}))
    present, hardware = build_hardware(case)
    if present and hardware is not None:  # JSON null is treated as absent (spec 47 section 3.1)
        error = check_hardware(hardware)
        if error:
            return {"status": 400, "errorCode": "bad_request"}
    hw_only = is_hardware_only(body)
    return {
        "status": 200,
        "hardwareOnly": hw_only,
        "routable": (not hw_only) and bool(body.get("models")),
        "assignments": [],
        "connectionId": "any-non-empty-string",
        "hardwareStored": bool(present and hardware is not None),
    }
