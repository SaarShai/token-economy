# Manual import full-summ

Import a full project summary into a fresh Token Economy-enabled target project folder.

Inputs:
- Full summary file: the uploaded file
- New target folder: current working directory

Identity rule:
- This is a target project that will use Token Economy as a local framework.
- The agent is not part of the Token Economy framework project unless the user explicitly asks to edit, improve, research, or maintain Token Economy itself.
- Do not import goals, tasks, roadmaps, active projects, handoffs, or maintainer-only instructions from the Token Economy framework repository.
- After setup, define the active project only from the uploaded summary and the user's current instructions.

Set up Token Economy first:
1. If `token-economy.yaml` is absent, clear only the current folder, including hidden files and `.git`, then clone:
   `find . -mindepth 1 -maxdepth 1 -exec rm -rf {} +`
   `git clone https://github.com/SaarShai/token-economy.git .`
2. Do not delete anything outside the current folder.
3. Run:
   `./INSTALL.sh --dry-run`
   `./INSTALL.sh --scope project --agent auto`
   `./te doctor`
   `./te hooks doctor`

Load only:
- `start.md`
- `token-economy.yaml`
- `L0_rules.md`
- `L1_index.md`
- `schema.md`
- the uploaded file

Use the uploaded file as the migration source of truth. It may contain raw secrets. Do not commit the uploaded file, `.env`, raw secret files, credentials, or any copied secret material.

Rebuild the wiki without Obsidian:
- Put source summaries and imported source evidence under `raw/`.
- Put active project state under `projects/`.
- Put verified durable facts under `L2_facts/`.
- Put reusable workflows and runbooks under `L3_sops/`.
- Put decisions into decision/project pages.
- Put durable Q&A into `queries/`.
- Put cold stale material into `L4_archive/` only when it is useful as warning/history.
- Update `index.md`, `L1_index.md`, and `log.md`.

Adapt to Token Economy:
- Convert Obsidian links/naming into repo-local markdown wikilinks such as `[[projects/example/README]]`.
- Preserve provenance from the full summary in every material page.
- Split large notes into focused pages only when that improves retrieval.
- Keep startup context lean; do not move broad target-project details into `start.md`, `L0_rules.md`, or `L1_index.md`.
- Do not edit framework-maintainer docs such as `ROADMAP.md`, `HANDOFF*.md`, or Token Economy maintainer-only skills unless the user explicitly asks for framework maintenance.
- Import raw secrets into local config/env files only as appropriate for the project. Keep secret files untracked.
- Preserve working commands, exact paths, setup steps, and known failure fixes.
- Discard context rot listed in the summary unless it is useful as a warning.

Verification:
- Run `./te wiki lint --strict`.
- Run `./te doctor`.
- Run any project-specific smoke checks listed in the uploaded file when they are safe and do not require unavailable external services.
- Check `git status --short` and ensure no secret files or the uploaded file are staged or committed.

Final handoff:
- What was imported.
- What was intentionally discarded.
- Where secrets now live locally.
- Wiki pages created/updated.
- Verification results.
- Remaining gaps and next actions.
