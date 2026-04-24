#!/usr/bin/env bash
set -euo pipefail

ROOT="${TOKEN_ECONOMY_ROOT:-$(pwd)}"
RAW="$(cat)"
PROMPT="$(printf '%s' "$RAW" | python3 -c '
import json, sys
raw = sys.stdin.read()
try:
    data = json.loads(raw)
    if isinstance(data, dict):
        print(data.get("prompt") or data.get("user_prompt") or data.get("message") or raw)
    else:
        print(raw)
except Exception:
    print(raw)
')"

if [[ "$PROMPT" =~ ^[[:space:]]*/(pa|btw)([[:space:]]|:|$) ]]; then
  "$ROOT/te" pa --directive "$PROMPT"
else
  "$ROOT/te" delegate classify "$PROMPT"
fi
