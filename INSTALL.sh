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

if [ "$SCOPE" != "project" ]; then
  echo "Token Economy installs project-locally only. Use --scope project." >&2
  exit 2
fi

export TOKEN_ECONOMY_ROOT="$ROOT"

echo "[1/7] doctor"
"$ROOT/te" doctor

echo "[2/7] hooks"
"$ROOT/te" hooks doctor

echo "[3/7] wiki index"
if [ "$DRY_RUN" = "1" ]; then
  echo "dry-run: would run ./te wiki index"
else
  "$ROOT/te" wiki index
fi

echo "[4/7] adapter"
if [ "$DRY_RUN" = "1" ]; then
  echo "dry-run: would run ./te start --agent $AGENT --scope $SCOPE"
else
  "$ROOT/te" start --agent "$AGENT" --scope "$SCOPE"
fi

echo "[5/7] agents-triage"
if [ ! -f "$ROOT/projects/agents-triage/install.sh" ]; then
  echo "skip: agents-triage files not present"
elif [ "$DRY_RUN" = "1" ]; then
  echo "dry-run: would run bash projects/agents-triage/install.sh --project"
else
  bash "$ROOT/projects/agents-triage/install.sh" --project
fi

echo "[6/7] context-keeper"
if [ ! -f "$ROOT/projects/context-keeper/install.sh" ]; then
  echo "skip: context-keeper files not present"
elif [ "$DRY_RUN" = "1" ]; then
  echo "dry-run: would run bash projects/context-keeper/install.sh --project"
else
  bash "$ROOT/projects/context-keeper/install.sh" --project
fi

echo "[7/7] semdiff"
if [ ! -f "$ROOT/projects/semdiff/install.sh" ]; then
  echo "skip: semdiff files not present"
elif [ "$DRY_RUN" = "1" ]; then
  echo "dry-run: would run bash projects/semdiff/install.sh --project"
else
  bash "$ROOT/projects/semdiff/install.sh" --project
fi

echo "Install check complete."
