#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SCOPE="project"
DRY_RUN=0
AGENT="auto"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --scope) SCOPE="$2"; shift 2 ;;
    --agent) AGENT="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

export TOKEN_ECONOMY_ROOT="$ROOT"

echo "[1/4] doctor"
"$ROOT/te" doctor

echo "[2/4] hooks"
"$ROOT/te" hooks doctor

echo "[3/4] wiki index"
if [ "$DRY_RUN" = "1" ]; then
  echo "dry-run: would run ./te wiki index"
else
  "$ROOT/te" wiki index
fi

echo "[4/4] adapter"
if [ "$DRY_RUN" = "1" ]; then
  echo "dry-run: would run ./te start --agent $AGENT --scope $SCOPE"
else
  "$ROOT/te" start --agent "$AGENT" --scope "$SCOPE"
fi

echo "Install check complete."

