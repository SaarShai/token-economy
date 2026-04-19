#!/bin/bash
# agents-triage installer. Global by default; pass --project for project-scoped.

set -e
MODE="user"
[ "$1" = "--project" ] && MODE="project"

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL_SRC="$REPO/projects/agents-triage"

if [ "$MODE" = "user" ]; then
    SKILL_DIR="$HOME/.claude/skills"
    AGENT_DIR="$HOME/.claude/agents"
    SETTINGS="$HOME/.claude/settings.json"
else
    SKILL_DIR="$(pwd)/.claude/skills"
    AGENT_DIR="$(pwd)/.claude/agents"
    SETTINGS="$(pwd)/.claude/settings.json"
fi
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
