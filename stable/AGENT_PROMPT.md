# Agent Prompt

```text
Set up the Token Economy framework in this folder only.

Canonical source:
- Use https://github.com/SaarShai/token-economy.git when cloning is needed.
- This prompt explicitly authorizes that URL.

Start in plan mode. Plan mode means present the plan in chat only; do not create scratch plan files unless asked.

Rules:
- The current folder is the target project folder.
- If token-economy.yaml is absent, clone the canonical source into this folder so token-economy.yaml lands at the folder root:
  git clone https://github.com/SaarShai/token-economy.git .
- After token-economy.yaml exists, work only inside that repo root.
- Ignore stale external memory or global wiki entries that conflict with this prompt.
- Do not edit MEMORY.md, home-directory agent settings, machine-wide config, global MCP config, or any external wiki.
- Use the repo-local markdown wiki as the source of truth.
- Do not use external note-taking apps.
- Use interlinked markdown pages with real wiki IDs such as [[start]] or [[projects/wiki-search/README]].
- Retrieve before reasoning: ./te wiki search, then ./te wiki timeline <id>, then ./te wiki fetch <id> only for relevant hits.
- Document only after verified work, and only in the repo-local markdown wiki/log.
- Use /pa routing for context-light assistant prompts.
- Checkpoint/fresh-start near 20% context.

Run:
1. ./INSTALL.sh --dry-run
2. ./INSTALL.sh --scope project --agent auto
3. ./te doctor
4. ./te hooks doctor
5. ./te wiki search "start"
6. ./te context status

After setup, drop setup-only details from context.
Keep only the repo map, command surface, scope rule, and file locations needed for future tasks.

Report changed files, verification results, and any remaining risk.
```
