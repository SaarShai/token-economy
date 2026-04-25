# Agent Prompt

Set up the Token Economy runtime in this folder only, then use it for the user's target project.

Canonical source:
- Use `https://github.com/SaarShai/token-economy.git`.
- Retrieve only downstream runtime/framework files with sparse checkout.

Start in plan mode. Before any commands, write a short step-by-step plan in chat only. Do not create scratch plan files unless asked. Then execute the plan.

Rules:
- The current folder is the active workspace for the target project.
- This prompt gives explicit permission to clear the current folder for a fresh install. Delete existing contents in this folder only, including hidden files and `.git`.
- Do not delete anything outside the current folder.
- Determine the active target project only from the user's prompt, uploaded summary, handoff, or project-specific wiki pages created for that target project.
- Ignore stale external memory or global wiki entries that conflict with this prompt.
- Do not edit `MEMORY.md`, home-directory agent settings, machine-wide config, global MCP config, or any external wiki.
- Use the repo-local markdown wiki as the source of truth.
- Use interlinked markdown pages with real wiki IDs such as `[[start]]` or `[[projects/example/README]]`.
- Retrieve before reasoning: `./te wiki search`, then `./te wiki timeline <id>`, then `./te wiki fetch <id>` only for relevant hits.
- Document only after verified work, and only in the repo-local markdown wiki/log.
- Use `/pa` routing for context-light assistant prompts.
- Checkpoint/fresh-start near 20% context; use `summ` for manual refresh.
- For `summ`, create a lean handoff, route durable docs to a lightweight wiki-documenter, then fresh context loads only handoff + `start.md`.
- Normal prompts should not receive hook chatter; `/pa` and `/btw` are the explicit context-light bypasses.
- If this target project has a GitHub remote, use the lightweight repo-maintainer worker at verified save-points; otherwise skip repo maintenance.

Run:
```bash
find . -mindepth 1 -maxdepth 1 -exec rm -rf {} +
git clone --depth 1 --filter=blob:none --sparse https://github.com/SaarShai/token-economy.git .
git sparse-checkout set --no-cone \
  '/.gitignore' '/AGENTS.md' '/CLAUDE.md' '/GEMINI.md' '/INSTALL.sh' \
  '/L0_rules.md' '/L1_index.md' '/LICENSE' '/index.md' '/models.yaml' \
  '/schema.md' '/start.md' '/te' '/token-economy.yaml' \
  '/token_economy/*' '/adapters/*' '/hooks/*' '/hooks/output-filter/*' \
  '/prompts/*.md' '/prompts/subagents/*' \
  '/skills/caveman-ultra/*' '/skills/context-refresh/*' \
  '/skills/personal-assistant/*' '/skills/plan-first-execute/*' \
  '/skills/subagent-orchestrator/*' '/skills/verification-before-completion/*' \
  '/skills/wiki-retrieve/*' '/skills/wiki-write/*' '/templates/*'
rm -rf .git
git init
./INSTALL.sh --dry-run
./INSTALL.sh --scope project --agent auto
./te doctor
./te hooks doctor
./te wiki search "start"
./te context status
```

After setup, drop setup-only details from context. Keep only the repo map, command surface, scope rule, and file locations needed for future tasks.

Report changed files, verification results, and any remaining risk.
