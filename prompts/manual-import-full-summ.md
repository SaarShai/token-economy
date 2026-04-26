# Manual import full-summ

/plan think carefully, step by step, to create a plan to import a full project summary into a target working folder that will use Token Economy as local scaffolding. Treat this folder as the active workspace, not the Token Economy source repository.

Import a full project summary into a target working folder that will use Token Economy as local scaffolding. Treat this folder as the active workspace, not the Token Economy source repository.

Inputs:
- Full summary file: the uploaded file
- New target folder: current working directory

Working rules:
- Set everything you need in this working folder, and nothing you do not need.
- Clone and/or import any file or information from referenced or linked folders that is needed to make the working folder self-sufficient.
- Exclude anything that is not relevant to the task.
- After cloning and/or importing, you may forget the references or links because you will have everything you need in this working folder.
- Actively learn from the uploaded file and adapt the information to the Token Economy setup in this working folder.
- Understand the processes and systems described or implied in the uploaded file, then create a similar system for yourself that is adapted to the way you work.

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

Rebuild the wiki directly in repo-local markdown. This is a wiki transplant, not a pointer back to the source wiki:
- Treat the original wiki as source evidence only. After import, project facts must come from this working folder's repo-local wiki.
- Create `raw/YYYY-MM-DD-import-manifest.md` from `templates/import-manifest.template.md`.
- The import manifest must cover every original wiki item listed in the uploaded file: original page/path, summary, target local page, status (`adapted`, `archived`, or `discarded`), rationale, and provenance.
- Put source summaries and imported source evidence under `raw/`.
- Put active project state under `projects/`.
- Put verified durable facts under `L2_facts/`.
- Put reusable workflows and runbooks under `L3_sops/`.
- Put decisions into decision/project pages.
- Put durable Q&A into `queries/`.
- Put cold stale material into `L4_archive/` only when it is useful as warning/history.
- Create or update `README.md` for the imported target project from the uploaded summary.
- Update `index.md`, `L1_index.md`, and `log.md`.

Adapt the source wiki to Token Economy:
- Convert existing wiki links/naming into repo-local markdown wikilinks such as `[[projects/example/README]]`.
- Rewrite source-wiki information into better organized Token Economy pages instead of copying a flat dump.
- Preserve provenance from the full summary in every material page.
- Split large notes into focused pages when that improves retrieval and combine tiny duplicates when that improves access.
- Keep startup context lean; do not move broad target-project details into `start.md`, `L0_rules.md`, or `L1_index.md`.
- Import raw secrets into local config/env files only as appropriate for the project. Keep secret files local and out of the wiki.
- Preserve working commands, exact paths, setup steps, known failure fixes, durable decisions, facts, SOPs, and reusable lessons.
- Discard context rot listed in the summary only when the import manifest records why; archive stale material only when it is useful as a warning.
- Never leave synthesized pages that tell the next agent to "see the old wiki", "use the original wiki", or follow external/home-directory wiki rules.
- Original wiki paths may appear only as sealed provenance in `raw/` source notes or the import manifest, not as operational instructions.

Verification:
- Run `./te wiki lint --strict --fail-on-error`.
- Run `./te wiki import-audit --manifest raw/YYYY-MM-DD-import-manifest.md`.
- Run `./te doctor`.
- Run any project-specific smoke checks listed in the uploaded file when they are safe and do not require unavailable external services.
- Confirm no secret files or the uploaded file were written into the wiki or local config files.
- Confirm `index.md` and `L1_index.md` point to the new local wiki only.

Final handoff:
- What was imported.
- What was intentionally discarded.
- Import manifest path and coverage count.
- Where secrets now live locally.
- Wiki pages created/updated.
- Verification results.
- Remaining gaps and next actions.
