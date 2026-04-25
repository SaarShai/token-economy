# Manual import full-summ

Import a full project summary into a target working folder that will use Token Economy as local scaffolding. Treat this folder as the active workspace, not the Token Economy source repository.

Inputs:
- Full summary file: the uploaded file
- New target folder: current working directory

Bootstrap Token Economy runtime files in the current folder:
1. Clear only the current folder, including hidden files and `.git`.
   `find . -mindepth 1 -maxdepth 1 -exec rm -rf {} +`
2. Retrieve only the downstream runtime/framework files:
   ```bash
   git clone --depth 1 --filter=blob:none --sparse https://github.com/SaarShai/token-economy.git .
   git sparse-checkout set --no-cone \
     '/.gitignore' '/AGENTS.md' '/CLAUDE.md' '/GEMINI.md' '/INSTALL.sh' \
     '/L0_rules.md' '/L1_index.md' '/LICENSE' '/index.md' '/models.yaml' \
     '/schema.md' '/stable/INSTALL.sh' '/start.md' '/te' '/token-economy.yaml' \
     '/token_economy/*' '/adapters/*' '/hooks/*' '/hooks/output-filter/*' \
     '/projects/compound-compression-pipeline/*' \
     '/projects/context-keeper/*' '/projects/semdiff/*' \
     '/prompts/*.md' '/prompts/subagents/*' \
     '/skills/caveman-ultra/*' '/skills/context-refresh/*' \
     '/skills/personal-assistant/*' '/skills/plan-first-execute/*' \
     '/skills/subagent-orchestrator/*' '/skills/verification-before-completion/*' \
     '/skills/wiki-retrieve/*' '/skills/wiki-write/*' '/templates/*'
   rm -rf .git
   git init
   ```
3. Do not delete anything outside the current folder.
4. Run:
   `./INSTALL.sh --dry-run`
   `./INSTALL.sh --scope project --agent auto`
   `./stable/INSTALL.sh`
   `./te doctor`
   `./te hooks doctor`
   The MCP install step is required, not optional: install ComCom, semdiff, and context-keeper when those files are present.

Load only:
- `start.md`
- `token-economy.yaml`
- `L0_rules.md`
- `L1_index.md`
- `schema.md`
- the uploaded file

After setup, define the active project only from the uploaded summary and the user's current instructions. Keep operating in this working folder.

Use the uploaded file as the migration source of truth. It may contain raw secrets. Keep the uploaded file, `.env`, raw secret files, credentials, and any copied secret material out of the wiki and local config.

Rebuild the wiki directly in repo-local markdown:
- Put source summaries and imported source evidence under `raw/`.
- Put active project state under `projects/`.
- Put verified durable facts under `L2_facts/`.
- Put reusable workflows and runbooks under `L3_sops/`.
- Put decisions into decision/project pages.
- Put durable Q&A into `queries/`.
- Put cold stale material into `L4_archive/` only when it is useful as warning/history.
- Create or update `README.md` for the imported target project from the uploaded summary.
- Update `index.md`, `L1_index.md`, and `log.md`.

Adapt to Token Economy:
- Convert existing wiki links/naming into repo-local markdown wikilinks such as `[[projects/example/README]]`.
- Preserve provenance from the full summary in every material page.
- Split large notes into focused pages only when that improves retrieval.
- Keep startup context lean; do not move broad target-project details into `start.md`, `L0_rules.md`, or `L1_index.md`.
- Import raw secrets into local config/env files only as appropriate for the project. Keep secret files local and out of the wiki.
- Preserve working commands, exact paths, setup steps, and known failure fixes.
- Discard context rot listed in the summary unless it is useful as a warning.

Verification:
- Run `./te wiki lint --strict`.
- Run `./te doctor`.
- Run any project-specific smoke checks listed in the uploaded file when they are safe and do not require unavailable external services.
- Confirm no secret files or the uploaded file were written into the wiki or local config files.

Final handoff:
- What was imported.
- What was intentionally discarded.
- Where secrets now live locally.
- Wiki pages created/updated.
- Verification results.
- Remaining gaps and next actions.
