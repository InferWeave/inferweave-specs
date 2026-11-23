#!/usr/bin/env python3
"""Read an already verified export; print counts and hashes, never record contents."""
import collections
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
rows = {path.name: json.loads(path.read_bytes()) for path in root.glob("*.json")}
summary = {
    "file_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sorted(root.glob("*.json"))},
    "rows": {name: len(value) for name, value in sorted(rows.items()) if isinstance(value, list)},
    "task_rows_by_family": dict(sorted(collections.Counter(row["area"] for row in rows["suite_tasks.json"]).items())),
    "speed_rows_cards": dict(sorted(collections.Counter(str(row.get("cards")) for row in rows["speed_rows.json"]).items())),
    "configuration_cards": dict(sorted(collections.Counter(str(row.get("cards")) for row in rows["configurations.json"]).items())),
    "configuration_profile_task_rows": sum(len(profile["tasks"]) for row in rows["configurations.json"] for profile in row["profiles"]),
}
print(json.dumps(summary, indent=2, sort_keys=True))
