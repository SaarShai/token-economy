#!/usr/bin/env bash
set -euo pipefail

# Wires auto-handoff's UserPromptSubmit hook into repo-local .claude/.
# Mirrors skills/context-keeper/tools/install.sh (idempotent JSON merge).
# This ACTIVATES the live auto-spawn hook — review SKILL.md safety rails first.

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
  shift
fi
if [ "${1:-}" != "" ] && [ "${1:-}" != "--project" ]; then
  echo "auto-handoff installs project-locally only. Use --project, --dry-run, or no flag." >&2
  exit 2
fi

TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_SRC="$(cd "$TOOLS_DIR/.." && pwd)"
REPO="$(cd "$TOOLS_DIR/../../.." && pwd)"
CLAUDE_DIR="$REPO/.claude"
SKILL_DIR="$CLAUDE_DIR/skills"
SETTINGS="$CLAUDE_DIR/settings.json"
HOOK_CMD="bash ./.claude/skills/auto-handoff/tools/hook.sh"

merge_settings() {
  python3 - "$SETTINGS" "$HOOK_CMD" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_cmd = sys.argv[2]
settings_path.parent.mkdir(parents=True, exist_ok=True)
if settings_path.exists():
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
else:
    data = {}

hooks = data.setdefault("hooks", {})
rules = hooks.setdefault("UserPromptSubmit", [])
target = {"matcher": "*", "hooks": [{"type": "command", "command": hook_cmd}]}
for rule in rules:
    if rule.get("matcher") != "*":
        continue
    existing = rule.get("hooks", [])
    if any(item.get("type") == "command" and item.get("command") == hook_cmd for item in existing):
        break
else:
    rules.append(target)

settings_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

if [ "$DRY_RUN" = "1" ]; then
  echo "dry-run: would symlink $SKILL_SRC → $SKILL_DIR/auto-handoff"
  echo "dry-run: would add UserPromptSubmit hook to $SETTINGS → $HOOK_CMD"
  echo "dry-run: no files changed."
  exit 0
fi

mkdir -p "$SKILL_DIR"
chmod +x "$TOOLS_DIR/hook.sh"
ln -sfn "$SKILL_SRC" "$SKILL_DIR/auto-handoff"
merge_settings

echo "Installed auto-handoff into repo-local .claude (UserPromptSubmit hook is now LIVE)."
echo "Disable any time: remove the hook line from .claude/settings.json, or export AUTO_HANDOFF_DISABLE=1."
