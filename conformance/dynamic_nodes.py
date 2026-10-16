"""Reference model for specs/64 (dynamic nodes): the deployment id and the rules of an
assignment entry that a JSON Schema cannot express.

The deployment id (section 5 rule 6) is a SHA-256 over one byte string built from the model id,
the profile and its launch block, the artifacts and, for a `serve`, the advert figures. The
layout is the one the reference implementation's `iw_core::dynamic_node::deployment_id` writes;
its three known answers (conformance/dynamic-node-vectors.json) were reproduced here with
`python3 -I` before they were written down.

Stdlib only. `check_vectors(root)` returns a list of error strings; `semantic_errors(fixture,
schema_rel)` returns the rules a valid assignment fixture must also meet.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

U64_MAX = (1 << 64) - 1
MAX_MATRIX_CONCURRENCY = 256
DRAFT_INFIX = "-draft-"
MAX_MINTED_ID_CHARS = 50
MAX_PROFILE_NAME_CHARS = 128


def _s(text: str) -> bytes:
    """S(x): the length of x in bytes as a u64 big-endian integer, then the UTF-8 bytes."""
    raw = text.encode("utf-8")
    return struct.pack(">Q", len(raw)) + raw


def _n(value: int) -> bytes:
    """N(n): n as a u64 big-endian integer (a count, or an advert figure)."""
    return struct.pack(">Q", value)


def deployment_id(model: str, profile: dict, artifacts: list, advert: dict | None) -> str:
    """`dep_` and the lowercase hex SHA-256 of the section 5 rule 6 byte string.

    `profile` is a RuntimeProfile document (JSON); `advert` is the serve entry's advert, or None
    for a `measure`. The artifacts' bytes and sources, the advert's tools and structuredOutput,
    the match rules and the evidence are not hashed.
    """
    launch = profile["launch"]
    out = bytearray()
    out += _s(model) + _s(profile["name"]) + _s(str(profile["version"]))
    out += _s(launch["image"]) + _s(launch.get("digest") or "")
    command = launch.get("command") or []
    out += _n(len(command)) + b"".join(_s(c) for c in command)
    out += _n(len(artifacts)) + b"".join(_s(a["path"]) + _s(a["sha256"]) for a in artifacts)
    env = launch.get("env") or {}
    keys = sorted(env, key=lambda k: k.encode("utf-8"))
    out += _n(len(keys)) + b"".join(_s(k) + _s(env[k]) for k in keys)
    privileges = launch.get("privileges") or []
    out += _n(len(privileges)) + b"".join(_s(p) for p in privileges)
    mounts = launch.get("mounts") or []
    out += _n(len(mounts))
    for mount in mounts:
        out += _s(mount["host"]) + _s(mount["container"])
        out += bytes([1 if mount.get("readOnly", True) else 0])
    shm = launch.get("shmSize")
    out += _n(0) if shm is None else _n(1) + _s(shm)
    out += _s(launch["engine"]) + _s(launch["backend"]) + _s(launch["label"])
    if advert is None:
        out += bytes([0])
    else:
        out += bytes([1])
        for member in ("slots", "contextSupported", "maxContextTokens", "kvBytesPerToken"):
            out += _n(advert[member])
    return "dep_" + hashlib.sha256(bytes(out)).hexdigest()


def artifact_set_errors(artifacts: list) -> list:
    """Whether the artifacts can sit side by side in one directory and have their sizes added."""
    errors = []
    for i, first in enumerate(artifacts):
        for second in artifacts[i + 1:]:
            x, y = first["path"], second["path"]
            if x == y:
                errors.append(f"artifact {x!r} is listed twice")
                continue
            for outer, inner in ((x, y), (y, x)):
                if inner.startswith(outer):
                    rest = inner[len(outer):]
                    if rest.startswith("/"):
                        errors.append(f"artifacts {outer!r} and {inner!r} collide: a file and a directory")
                    if rest in (".part", ".sha256"):
                        errors.append(
                            f"artifacts {outer!r} and {inner!r} collide: {inner!r} is the .part or "
                            f".sha256 file the node keeps beside {outer!r}"
                        )
    if sum(a["bytes"] for a in artifacts) > U64_MAX:
        errors.append("the artifacts' sizes add up to more than 2^64 bytes")
    return errors


def matrix_errors(matrix: dict) -> list:
    """The MeasureMatrix rules the schema cannot express (the rest are schema bounds)."""
    errors = []
    floor = 10 * (matrix["maxTokens"] + 16)
    for context in matrix["contexts"]:
        if context < floor:
            errors.append(f"matrix.contexts {context} is below {floor} = 10 * (maxTokens + 16)")
    return errors


def assignment_errors(entry: dict) -> list:
    """The rules of a `serve` or `measure` entry beyond its schema; [] for a `stop`."""
    kind = entry.get("kind")
    if kind not in ("serve", "measure"):
        return []
    errors = []
    profile = entry["profile"] if kind == "serve" else entry["candidate"]
    advert = entry["advert"] if kind == "serve" else None
    artifacts = entry["artifacts"]
    if len(entry["gpuIds"]) != profile["match"]["gpu"]["count"]:
        errors.append("gpuIds does not name as many cards as the profile's match.gpu.count")
    errors.extend(artifact_set_errors(artifacts))
    if kind == "serve":
        if advert["maxContextTokens"] > advert["contextSupported"]:
            errors.append("advert.maxContextTokens is above contextSupported")
        if advert["slots"] > 0xFFFFFFFF:
            errors.append("advert.slots is above 4294967295")
    else:
        errors.extend(matrix_errors(entry["matrix"]))
    derived = deployment_id(entry["model"], profile, artifacts, advert)
    if entry["deployment"] != derived:
        errors.append(f"deployment {entry['deployment']} is not derived from the payload ({derived})")
    return errors


def semantic_errors(fixture, schema_rel: str) -> list:
    """Extra checks for a fixture that passed its schema."""
    if schema_rel == "requests/node-assignment.json":
        return assignment_errors(fixture)
    if schema_rel == "requests/node-register-response.json":
        errors = []
        for index, entry in enumerate(fixture.get("assignments") or []):
            errors.extend(f"assignments[{index}]: {e}" for e in assignment_errors(entry))
        return errors
    if schema_rel == "requests/node-provisioning-status.json":
        return []
    return []


def _apply(base: dict, change: dict) -> tuple:
    """The (model, profile, artifacts, advert) of `base` with `change` laid over it.

    `change` may carry `model`, `name`, `version`, `profile` (top-level members of the profile
    document replaced, for members that are not hashed: `match`, `evidence`, `quality`),
    `launch` (members replaced one by one), `artifacts` (replaced whole) and `advert` (members
    replaced one by one; `null` is no advert, which is what a `measure` hashes).
    """
    profile = json.loads(json.dumps(base["profile"]))
    profile.update(change.get("profile", {}))
    profile["name"] = change.get("name", profile["name"])
    profile["version"] = change.get("version", profile["version"])
    profile["launch"].update(change.get("launch", {}))
    artifacts = json.loads(json.dumps(change.get("artifacts", base["artifacts"])))
    if "advert" in change and change["advert"] is None:
        advert = None
    else:
        advert = {**base["advert"], **change.get("advert", {})}
    return change.get("model", base["model"]), profile, artifacts, advert


def check_vectors(root: Path) -> list:
    """Recompute the known answers and the must-differ relations of
    conformance/dynamic-node-vectors.json."""
    doc = json.loads((root / "conformance" / "dynamic-node-vectors.json").read_text())
    errors = []
    base = doc["base"]
    for case in doc["knownAnswers"]:
        got = deployment_id(*_apply(base, case["change"]))
        if got != case["expect"]:
            errors.append(f"dynamic-node vector {case['id']}: expected {case['expect']}, got {got}")
    seen = {deployment_id(*_apply(base, {}))}
    for case in doc["mustDiffer"]:
        got = deployment_id(*_apply(base, case["change"]))
        if got in seen:
            errors.append(f"dynamic-node vector {case['id']}: id equals one already produced ({got})")
        seen.add(got)
    unchanged = deployment_id(*_apply(base, {}))
    for case in doc["mustEqual"]:
        got = deployment_id(*_apply(base, case["change"]))
        if got != unchanged:
            errors.append(f"dynamic-node vector {case['id']}: a member that is not hashed moved the id")
    for case in doc["mustDifferPairs"]:
        first = deployment_id(*_apply(base, case["a"]))
        second = deployment_id(*_apply(base, case["b"]))
        if first == second:
            errors.append(f"dynamic-node vector {case['id']}: the two inputs hash alike ({first})")
    return errors
