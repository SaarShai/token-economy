#!/usr/bin/env bash
set -euo pipefail

ROOT="${TOKEN_ECONOMY_ROOT:-$(pwd)}"
TRANSCRIPT="${1:-}"

if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  "$ROOT/te" context checkpoint --handoff-template --transcript "$TRANSCRIPT"
else
  "$ROOT/te" context checkpoint --handoff-template
fi

