# Complete migrate export

complete-migrate-export

Goal: create one complete local migration export at `[project-name]_complete_migrate_export.md` so a new Token Economy-enabled target working folder can import, adapt, and continue this project without carrying over context rot or depending operationally on the old folder.

Think carefully, step by step, and devise a plan for the following, then execute the plan.

Raw API keys/secrets are explicitly authorized for this local file. Put raw secret values only in the `Secrets` section. After writing the file, run `chmod 600 [project-name]_complete_migrate_export.md` when possible.

## Subagent orchestration

Use smaller/lightweight subagents for bounded admin and extraction work when the host supports them. The main agent keeps final synthesis, resolves conflicts, and writes the final export.

Spawn or route compact workers for:
- File inventory: source files, docs, configs, scripts, tests, CI, hidden project files, package manifests, lockfiles, generated artifacts, and deployment files.
- Wiki inventory: Obsidian/wiki pages, indexes, project notes, SOPs, decisions, source summaries, stale/conflicting notes, backlinks/outlinks, aliases, and tags.
- Config/secrets inventory: `.env*`, local config, provider/model settings, API usage patterns, service credentials, external services, and integration wiring.
- Git/provenance inventory: remotes, branch, recent commits, tags, uncommitted work, ignored files that matter, active branches, and inspected refs.
- Commands/runbooks inventory: setup, dev, test, lint, build, deploy, monitor, recurring failures, known fixes, and working directories.

Each worker must return a compact result packet with:
- Scope handled.
- Files/pages/commands inspected.
- Findings.
- Source paths and important line references when useful.
- Confidence.
- Gaps and risks.

Use `prompts/subagents/lifecycle.prompt.md` when supervising workers. Close a subagent only after its result packet has been read, useful results have been merged into this export, and durable gaps/follow-ups have been captured. Do not delegate final synthesis.

## Inventory rules

Inventory thoroughly:
- Source files, docs, configs, scripts, tests, CI, hidden project files, agent files, package manifests, lockfiles, generated artifacts, and deployment files.
- `.env*`, local config files, provider/model settings, API usage patterns, service credentials, and integration wiring.
- Git remotes, current branch, recent commits, tags if relevant, uncommitted work, ignored files that matter, and active branches.
- Obsidian/wiki pages, indexes, project notes, SOPs, decisions, source summaries, stale/conflicting notes, and backlinks that explain current behavior.
- For every original wiki item, capture: page/path, title, one-line summary, backlinks/outlinks when useful, current/stale status, target Token Economy category, and whether it should be adapted, archived, or discarded.
- Capture wiki naming conventions, folder conventions, aliases, recurring tags, project-specific rules, and any external/home-directory rules the old project depended on so the importer can replace them with repo-local Token Economy pages.
- Local runbooks, working commands, recurring failures, best practices, architectural decisions, constraints, active tasks, open questions, and known dead ends.

Keep:
- Verified current project truth.
- Commands that work and the directory where they work.
- Decisions with rationale and rejected alternatives when useful.
- Active constraints, dependencies, API contracts, deployment details, and reusable lessons.
- Stale/conflicting material only when it prevents repeating mistakes.

Drop:
- Transcript noise, chat filler, duplicated prose, abandoned plans, obsolete wiki pages with no current warning value, one-off dead ends, raw logs, and other context rot.

Write `[project-name]_complete_migrate_export.md` with this structure:

# COMPLETE_MIGRATE_EXPORT

## 0. Import Contract
- Old project root:
- Obsidian/wiki root:
- Output file:
- Date/time:
- Export author/session:
- Required target-project goal:
- Expected new working folder:

## 1. Project Overview
- What this project is.
- Current status.
- Primary user goals.
- Non-negotiable constraints.

## 2. Source Location Index
Create a complete index of where important things live in the original project. Include:
- Code roots and important packages/modules.
- Docs, specs, plans, and READMEs.
- Config files, manifests, lockfiles, runtime settings, and deployment files.
- Tests, fixtures, scripts, CI, hooks, and generated artifacts.
- Wiki/knowledge roots, indexes, source summaries, and project notes.
- Secret/config sources, without raw values except in the `Secrets` section.
- Local-only files, ignored files that matter, and files outside the repo that influence behavior.
- External tools/services/models/APIs that are required but live outside the folder.
- Agent instructions, skills, MCP/plugin/app setup, home-directory rules, and machine-wide assumptions that the new project must replace or localize.

## 3. Transfer Manifest
For every important source item, record:

| Source path/location | Kind | Target path/category | Action | Rationale | Dependencies | Verification |
|---|---|---|---|---|---|---|

Allowed `Action` values:
- `copy`: copy the file/directory into the new working folder.
- `adapt`: rewrite into Token Economy wiki/docs/config or adjust paths/settings for the new folder.
- `regenerate`: recreate from commands, templates, package managers, or build steps.
- `reference-only`: use as evidence during import but do not carry forward operationally.
- `secret-local`: recreate locally outside wiki/committed guidance with raw value recorded only in `Secrets`.
- `archive`: keep only as cold history/warning.
- `discard`: intentionally omit as stale/noisy/duplicative.

Include a complete original-wiki coverage map: each original wiki page/path -> target Token Economy page type/path -> import status (`adapted`, `archived`, or `discarded`) -> rationale.

## 4. Architecture + Code Inventory
- Important files/directories and why they matter.
- Entry points and runtime flow.
- APIs, schemas, data flow, jobs, scripts, tests, CI, deployment.
- Files that should not be imported except as references.

## 5. Wiki + Knowledge Inventory
- Obsidian/wiki structure.
- Complete page inventory, including indexes, project pages, facts, SOPs/runbooks, decisions, source summaries, queries/answers, stale/conflicting notes, and hidden or home-directory agent rules that influenced behavior.
- Pages to preserve and their target Token Economy page types/paths.
- Pages to archive/discard and why.
- Important backlinks, outlinks, aliases, tags, indexes, folder conventions, and naming conventions to translate.
- Information that must be rewritten so the new working folder is self-contained and does not refer agents back to the source wiki.

## 6. Secrets
For each raw secret/API key include:
- Service/provider:
- Raw value:
- Env var/config key:
- Source path:
- Scope/use:
- Rotation risk:
- Migration target in the new folder:
- Whether it should be committed: no

## 7. Commands + Workflows
- Setup/install commands.
- Development commands.
- Test/lint/build commands.
- Deploy/run/monitor commands.
- Known working directory for each command.
- Expected success output or failure modes.

## 8. Dependencies + External Services
- Packages, tools, runtimes, models/providers, accounts, dashboards, URLs, MCP/app/plugin integrations.
- Version constraints and compatibility notes.
- External dependencies that intentionally remain outside the new folder.

## 9. Decisions + Best Practices
- Durable decisions with rationale.
- Patterns that repeatedly worked.
- Practices to avoid.
- Recurring failures and exact fixes.

## 10. Active Work + Open Questions
- Current tasks.
- Blockers.
- Next actions in priority order.
- Questions the new agent should resolve only after setup/import.

## 11. Discarded / Stale / Context Rot
- What was intentionally not carried forward.
- Why it is stale/noisy/duplicative.
- Any stale item worth preserving only as a warning.

## 12. Provenance
- Files/directories inspected.
- Wiki pages inspected.
- Commands run and important outputs.
- Git refs/commits checked.
- Subagent result packets used.
- Known gaps in the inventory.
