"""IW-PROMPT-001 closed recording vocabulary/data/document reconciliation."""
import json
import re

GROUPS = {
    "known_loss_reasons": "Known-loss reasons",
    "unknown_outcome_reasons": "Unknown-outcome reasons",
    "health_states": "Health states",
    "sink_results": "Sink results",
}
POLICY_KEYS = {"capacity", "max_bytes", "max_event_bytes", "max_batch_bytes", "batch_size", "flush_ms", "retry_initial_ms", "retry_max_ms", "disk_max_bytes", "disk_scan_limit"}

def valid_policy(policy, ceilings):
    return (all(type(policy.get(k)) is int and policy[k] > 0 for k in POLICY_KEYS)
            and type(policy.get("discard")) is bool
            and policy["max_event_bytes"] <= policy["max_batch_bytes"] <= policy["max_bytes"]
            and policy["retry_initial_ms"] <= policy["retry_max_ms"]
            and policy["capacity"] <= ceilings["capacity"]
            and policy["batch_size"] <= ceilings["batch_size"])

def contract_errors(root):
    prefix = "recording-outcomes-v1: "
    try:
        data = json.loads((root / "contracts/recording-outcomes-v1.json").read_text())
        document = (root / "docs/contracts/recording-outcomes-v1.md").read_text()
    except (OSError, ValueError) as error:
        return [prefix + "missing or invalid canonical data/document: " + type(error).__name__]
    errors = []
    expected_fields = {"schema", "version", "feature_id", "spec", "known_loss_reasons", "unknown_outcome_reasons", "health_states", "sink_results", "metrics", "defaults", "invalid_policy_vectors", "count_ceilings", "entropy_policy"}
    if not isinstance(data, dict) or set(data) != expected_fields:
        return [prefix + "canonical contract must be a closed object"]
    if type(data.get("version")) is not int or data.get("spec") != "specs/22_PROMPT_LEDGER.md":
        errors.append(prefix + "wrong typed version or specification binding")
    if data.get("schema") != "iw.recording-outcomes/1" or data.get("version") != 1 or data.get("feature_id") != "IW-PROMPT-001":
        errors.append(prefix + "wrong version or feature binding")
    for key, heading in GROUPS.items():
        values = data.get(key, [])
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not re.fullmatch(r"[a-z_]+", v) for v in values):
            errors.append(prefix + key + " is not a closed nonempty vocabulary")
            continue
        if len(values) != len(set(values)):
            errors.append(prefix + key + " contains duplicate values")
        section = re.search(r"^## " + re.escape(heading) + r"\n(.*?)(?=^## |\Z)", document, re.M | re.S)
        published = re.findall(r"^\| `([a-z_]+)` \|", section[1] if section else "", re.M)
        for value in values:
            if value not in published:
                errors.append(prefix + value + " not published in " + heading)
        if set(published) != set(values) or len(published) != len(set(published)):
            errors.append(prefix + heading + " disagrees with frozen data")
    metrics = data.get("metrics", {})
    if not isinstance(metrics, dict) or set(metrics) != {"known_loss", "unknown_outcome", "health"}:
        errors.append(prefix + "missing closed metric-family bindings")
    else:
        for name in metrics.values():
            if not isinstance(name, str) or name not in document:
                errors.append(prefix + "metric family not published")
    ceilings = data.get("count_ceilings", {})
    if set(ceilings) != {"capacity", "batch_size"} or any(type(v) is not int or v <= 0 for v in ceilings.values()):
        errors.append(prefix + "invalid fixed count ceilings")
        return errors
    entropy = data.get("entropy_policy", {})
    entropy_numbers = {"queued_objects", "pending_prepare_or_send_objects", "maximum_objects", "raw_entropy_bytes_per_object"}
    entropy_valid = (isinstance(entropy, dict)
                     and set(entropy) == entropy_numbers | {"independent_of_configured_event_capacity"}
                     and all(type(entropy[k]) is int and entropy[k] > 0 for k in entropy_numbers)
                     and entropy.get("independent_of_configured_event_capacity") is True)
    if (not entropy_valid
            or entropy["queued_objects"] + entropy["pending_prepare_or_send_objects"] != entropy["maximum_objects"]
            or entropy["maximum_objects"] != ceilings["capacity"]
            or entropy["pending_prepare_or_send_objects"] != 1
            or entropy["raw_entropy_bytes_per_object"] != 64):
        errors.append(prefix + "invalid fixed entropy reservoir policy")
    defaults = data.get("defaults", {})
    if set(defaults) != POLICY_KEYS | {"discard"} or not valid_policy(defaults, ceilings):
        errors.append(prefix + "invalid default bounded policy")
        return errors
    if any(defaults.get(key) != value for key, value in ceilings.items()):
        errors.append(prefix + "default count must equal canonical ceiling")
    vectors = data.get("invalid_policy_vectors", [])
    if not isinstance(vectors, list) or not vectors:
        errors.append(prefix + "missing invalid policy vectors")
        return errors
    for vector in vectors:
        if not isinstance(vector, dict) or not set(vector) <= set(defaults) or valid_policy({**defaults, **vector}, ceilings):
            errors.append(prefix + "invalid policy vectors contain an accepted or malformed policy")
    merged = [{**defaults, **v} for v in vectors if isinstance(v, dict)]
    merged = [v for v in merged if all(type(v.get(k)) is int for k in ["max_event_bytes", "max_batch_bytes", "max_bytes"])]
    if (not all(any(isinstance(v, dict) and type(v.get(key)) is int and v[key] == 0 for v in vectors) for key in ["max_event_bytes", "max_batch_bytes", "max_bytes"])
            or not any(v["max_event_bytes"] > v["max_batch_bytes"] for v in merged)
            or not any(v["max_batch_bytes"] > v["max_bytes"] for v in merged)):
        errors.append(prefix + "invalid policy vectors omit zero/inconsistent byte bounds")
    return errors
