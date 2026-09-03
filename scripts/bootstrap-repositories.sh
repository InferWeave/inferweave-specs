#!/usr/bin/env bash
set -euo pipefail

OWNER="InferWeave"
REPO="inferweave"
ROOT="${HOME}/src/InferWeave"
CREATE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner) OWNER="$2"; shift 2;;
    --repo) REPO="$2"; shift 2;;
    --root) ROOT="$2"; shift 2;;
    --create-missing) CREATE=1; shift;;
    *) echo "unknown argument: $1" >&2; exit 2;;
  esac
done

command -v gh >/dev/null || { echo "gh is required" >&2; exit 1; }

mkdir -p "$ROOT"
cd "$ROOT"

if [[ -d "$REPO/.git" ]]; then
  echo "repository already present: $ROOT/$REPO"
  echo "Existing contents are historical and not authoritative under the clean-slate spec."
  exit 0
fi

if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  gh repo clone "$OWNER/$REPO" "$REPO"
elif [[ "$CREATE" == "1" ]]; then
  gh repo create "$OWNER/$REPO" --private --clone
else
  echo "missing: $OWNER/$REPO"
  echo "rerun with --create-missing to create it"
fi
