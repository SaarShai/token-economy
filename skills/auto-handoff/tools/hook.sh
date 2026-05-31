#!/usr/bin/env bash
# UserPromptSubmit shim for auto-handoff.
# Must never block the turn: swallow any failure and always exit 0.
# stdout from hook.py (the directive) is passed through to Claude Code.
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/hook.py" || true
exit 0
