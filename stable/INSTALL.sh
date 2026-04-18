#!/bin/bash
# Token Economy — stable install script
# Installs the measured, tested subset: ComCom MCP, semdiff MCP, context-keeper hook.
#
# Usage:
#   ./INSTALL.sh              # MODE A (global — all CC sessions)
#   ./INSTALL.sh --project    # MODE B (project — only this folder)
#
# Requires: python3.10+, pip, brew (macOS) or manual tree-sitter install (Linux).

set -e
MODE="user"
[ "$1" = "--project" ] && MODE="project"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY=${PY:-/opt/homebrew/bin/python3.11}
command -v "$PY" >/dev/null || PY=$(command -v python3)

echo "=== Token Economy stable install (mode=$MODE, py=$PY) ==="

# 1. Python deps
echo "[1/5] pip deps..."
$PY -m pip install --quiet --user mcp tiktoken llmlingua 'tree-sitter<0.22' tree-sitter-languages

# 2. ComCom MCP server
echo "[2/5] registering ComCom MCP..."
claude mcp add comcom --scope $MODE -- $PY "$REPO_ROOT/projects/compound-compression-pipeline/comcom_mcp/server.py"

# 3. semdiff MCP server
echo "[3/5] registering semdiff MCP..."
claude mcp add semdiff --scope $MODE -- $PY "$REPO_ROOT/projects/semdiff/semdiff_mcp/server.py"

# 4. context-keeper skill + hook
echo "[4/5] installing context-keeper skill..."
if [ "$MODE" = "user" ]; then
  SKILL_DIR="$HOME/.claude/skills"
  SETTINGS="$HOME/.claude/settings.json"
else
  SKILL_DIR="$REPO_ROOT/.claude/skills"
  SETTINGS="$REPO_ROOT/.claude/settings.json"
fi
mkdir -p "$SKILL_DIR"
ln -sfn "$REPO_ROOT/projects/context-keeper" "$SKILL_DIR/context-keeper"
echo "  symlinked → $SKILL_DIR/context-keeper"

# 5. Remind user about hook
echo "[5/5] hook wiring (manual — avoid clobbering existing hooks)"
cat <<EOF

To activate context-keeper PreCompact hook, add to $SETTINGS:
{
  "hooks": {
    "PreCompact": [{
      "matcher": "*",
      "hooks": [{"type":"command","command":"bash ${SKILL_DIR}/context-keeper/hook.sh"}]
    }]
  }
}
(If PreCompact hook exists, chain — don't replace.)

=== verify ==="
claude mcp list 2>&1 | grep -E "comcom|semdiff" || echo "(run 'claude mcp list' after CC restart)"
EOF

echo "Install complete. Restart Claude Code to see MCP tools."
