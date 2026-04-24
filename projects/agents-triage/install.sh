#!/bin/bash
# agents-triage installer. Project-local only.

set -e
if [ "${1:-}" != "" ] && [ "${1:-}" != "--project" ]; then
    echo "agents-triage installs project-locally only. Use --project or no flag." >&2
    exit 2
fi

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL_SRC="$REPO/projects/agents-triage"

SKILL_DIR="$REPO/.claude/skills"
AGENT_DIR="$REPO/.claude/agents"
SETTINGS="$REPO/.claude/settings.json"
mkdir -p "$SKILL_DIR" "$AGENT_DIR"

echo "[1/3] symlinking skill → $SKILL_DIR/agents-triage"
ln -sfn "$SKILL_SRC" "$SKILL_DIR/agents-triage"

echo "[2/3] copying agent definitions → $AGENT_DIR/"
for a in wiki-note quick-fix local-ollama research-lite; do
    cp -f "$SKILL_SRC/agents/$a.md" "$AGENT_DIR/$a.md"
done

echo "[3/3] hook wiring ($SETTINGS)"
chmod +x "$SKILL_SRC/hook.sh" "$SKILL_SRC/classify.py"
cat <<EOF

To activate, add to $SETTINGS under hooks.UserPromptSubmit (chain if one exists):
{
  "matcher": "*",
  "hooks": [
    {"type":"command","command":"bash $SKILL_SRC/hook.sh"}
  ]
}

Override per-prompt: include "NO TRIAGE" anywhere in your message.

Env:
  AGENTS_TRIAGE_NO_OLLAMA=1     disable Ollama fallback (regex-only)
  AGENTS_TRIAGE_LOG=/path/log   log every classification

Test the classifier:
  python3 $SKILL_SRC/classify.py "add a note to the wiki about X"
EOF
