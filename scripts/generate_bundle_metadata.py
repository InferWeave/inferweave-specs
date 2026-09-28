#!/usr/bin/env python3
"""Regenerate the deterministic bundle inventory and content digests."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"BUNDLE_INDEX.md", "checksums.json"}
IGNORED_PARTS = {".git", ".superpowers", "__pycache__"}


def bundle_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not (IGNORED_PARTS & set(path.parts))
        and path.relative_to(ROOT).as_posix() not in EXCLUDED
    )


def main() -> None:
    files = bundle_files()
    checksums = {
        path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in files
    }
    (ROOT / "checksums.json").write_text(json.dumps(checksums, indent=2) + "\n")

    manifest = json.loads((ROOT / "bundle-manifest.json").read_text())
    features = json.loads((ROOT / "contracts/feature-registry.json").read_text())["features"]
    tasks = json.loads((ROOT / "contracts/canonical-task-graph.json").read_text())["tasks"]
    specs = list((ROOT / "specs").glob("*.md"))
    total_tokens = sum((len(path.read_bytes()) + 3) // 4 for path in files)

    lines = [
        "# InferWeave Specs Repository Index",
        "",
        f"Version: **{manifest['version']}**",
        f"Specifications: **{len(specs)}**",
        f"Tracked features: **{len(features)}**",
        f"Canonical tasks: **{len(tasks)}**",
        "Deployment: **Docker Compose persistent / Apptainer Slurm**",
        "GPU watchdog/rescue: **required**",
        "",
        "## Start",
        "- `README.md`",
        "- `AGENTS.md`",
        "- `START_HERE.md`",
        "- `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`",
        "- `contracts/canonical-task-graph.json`",
        "",
        "## Files",
        "",
        "Digest and approximate token cost at four characters per token, so a context pack can be budgeted before it is assembled. "
        f"Whole bundle: **~{total_tokens:,} tokens**.",
        "",
    ]
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        tokens = (len(path.read_bytes()) + 3) // 4
        lines.append(f"- `{relative}` — `{checksums[relative][:12]}` — ~{tokens:,}t")
    (ROOT / "BUNDLE_INDEX.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
