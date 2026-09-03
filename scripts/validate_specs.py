#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict, deque
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

features = json.loads((ROOT/"contracts/feature-registry.json").read_text())["features"]
graph = json.loads((ROOT/"contracts/canonical-task-graph.json").read_text())
tasks = graph["tasks"]

fids = [f["id"] for f in features]
tids = [t["id"] for t in tasks]

if len(fids) != len(set(fids)):
    errors.append("duplicate feature IDs")
if len(tids) != len(set(tids)):
    errors.append("duplicate task IDs")

task_ids = set(tids)
for t in tasks:
    for d in t.get("depends_on", []):
        if d not in task_ids:
            errors.append(f"{t['id']}: missing dependency {d}")
    for s in t.get("specs", []):
        if not (ROOT/f"specs/{s}.md").exists():
            errors.append(f"{t['id']}: missing spec specs/{s}.md")

# DAG
indeg = {tid: 0 for tid in task_ids}
adj = defaultdict(list)
for t in tasks:
    for d in t.get("depends_on", []):
        adj[d].append(t["id"])
        indeg[t["id"]] += 1
q = deque([x for x,n in indeg.items() if n == 0])
seen = 0
while q:
    x=q.popleft()
    seen += 1
    for y in adj[x]:
        indeg[y] -= 1
        if indeg[y] == 0:
            q.append(y)
if seen != len(tasks):
    errors.append("canonical task graph contains cycle")

# Feature mappings
for f in features:
    ct = f.get("canonical_tasks", [])
    if not ct:
        errors.append(f"{f['id']}: no canonical task")
    for tid in ct:
        if tid not in task_ids:
            errors.append(f"{f['id']}: maps to missing task {tid}")

# Deployment substrate guardrails
bad_patterns = {
    r"Podman/Podman Compose": "Podman production guidance",
    r"Quadlet": "Quadlet production guidance",
    r"Bootstrap `inferweave` Go": "stale Go bootstrap guidance",
}
for p in ROOT.rglob("*"):
    if not p.is_file() or p.suffix not in {".md",".json",".yaml",".yml",".sh"}:
        continue
    rel = p.relative_to(ROOT)
    if str(rel) == "scripts/validate_specs.py":
        continue
    text = p.read_text(errors="ignore")
    for pat,label in bad_patterns.items():
        if re.search(pat,text,re.I):
            errors.append(f"{rel}: {label}")

# Required watchdog/container artifacts
for rel in [
    "specs/36_GPU_WATCHDOG_RESCUE.md",
    "specs/37_CONTAINER_DEPLOYMENT_STANDARD.md",
    "AGENTS.md",
    "README.md",
]:
    if not (ROOT/rel).exists():
        errors.append(f"missing {rel}")

if errors:
    print("SPEC VALIDATION FAILED")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print(f"OK: {len(features)} features, {len(tasks)} canonical tasks, DAG valid")
