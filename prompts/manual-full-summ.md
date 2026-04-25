# Manual full-summ: old project export

Copy-paste this into the agent/session attached to the old Claude Code project.

```text
full-summ

Goal: create one complete local migration summary at `<OUTPUT_FULL_SUMM>` so a new Token Economy folder can import and adapt this project without carrying over context rot.

Inputs:
- Old project root: `<OLD_PROJECT_ROOT>`
- Obsidian/wiki root: `<OBSIDIAN_WIKI_ROOT>`
- Output file: `<OUTPUT_FULL_SUMM>`

Rules:
- Treat `<OLD_PROJECT_ROOT>` and `<OBSIDIAN_WIKI_ROOT>` as read-only.
- Write exactly one output file: `<OUTPUT_FULL_SUMM>`.
- Mark the output file at the top with: `LOCAL SECRET MATERIAL - DO NOT COMMIT`.
- Raw API keys/secrets are explicitly authorized for this local file. Put raw secret values only in the `Secrets` section.
- After writing the file, run `chmod 600 <OUTPUT_FULL_SUMM>` when possible.

Inventory thoroughly:
- Source files, docs, configs, scripts, tests, CI, hidden project files, agent files, package manifests, lockfiles, and deployment files.
- `.env*`, local config files, provider/model settings, API usage patterns, service credentials, and integration wiring.
- Git remotes, current branch, recent commits, tags if relevant, uncommitted work, ignored files that matter, and active branches.
- Obsidian/wiki pages, indexes, project notes, SOPs, decisions, source summaries, stale/conflicting notes, and backlinks that explain current behavior.
- Local runbooks, working commands, recurring failures, best practices, architectural decisions, constraints, active tasks, open questions, and known dead ends.

Keep:
- Verified current project truth.
- Commands that work and the directory where they work.
- Decisions with rationale and rejected alternatives when useful.
- Active constraints, dependencies, API contracts, deployment details, and reusable lessons.
- Stale/conflicting material only when it prevents repeating mistakes.

Drop:
- Transcript noise, chat filler, duplicated prose, abandoned plans, obsolete wiki pages with no current warning value, one-off dead ends, raw logs, and other context rot.

Write `<OUTPUT_FULL_SUMM>` with this structure:

# FULL_SUMM - <project name>

## 0. Import Contract
- Old project root:
- Obsidian/wiki root:
- Output file:
- Date/time:
- Summary author/session:
- Required new-folder goal:

## 1. Project Overview
- What this project is.
- Current status.
- Primary user goals.
- Non-negotiable constraints.

## 2. Import Map
- What must become raw source notes.
- What must become project pages.
- What must become durable facts.
- What must become SOPs.
- What must become decisions.
- What must become queries/answers.
- What should be archived or discarded.

## 3. Architecture + Code Inventory
- Important files/directories and why they matter.
- Entry points and runtime flow.
- APIs, schemas, data flow, jobs, scripts, tests, CI, deployment.
- Files that should not be imported except as references.

## 4. Wiki + Knowledge Inventory
- Obsidian/wiki structure.
- Pages to preserve and their target Token Economy page types.
- Pages to archive/discard and why.
- Important backlinks, indexes, and naming conventions to translate.

## 5. Secrets
For each raw secret/API key include:
- Service/provider:
- Raw value:
- Env var/config key:
- Source path:
- Scope/use:
- Rotation risk:
- Migration target in the new folder:
- Whether it should be committed: no

## 6. Commands + Workflows
- Setup/install commands.
- Development commands.
- Test/lint/build commands.
- Deploy/run/monitor commands.
- Known working directory for each command.
- Expected success output or failure modes.

## 7. Dependencies + External Services
- Packages, tools, runtimes, models/providers, accounts, dashboards, URLs, MCP/app/plugin integrations.
- Version constraints and compatibility notes.

## 8. Decisions + Best Practices
- Durable decisions with rationale.
- Patterns that repeatedly worked.
- Practices to avoid.
- Recurring failures and exact fixes.

## 9. Active Work + Open Questions
- Current tasks.
- Blockers.
- Next actions in priority order.
- Questions the new agent should resolve only after setup/import.

## 10. Discarded / Stale / Context Rot
- What was intentionally not carried forward.
- Why it is stale/noisy/duplicative.
- Any stale item worth preserving only as a warning.

## 11. Provenance
- Files/directories inspected.
- Wiki pages inspected.
- Commands run and important outputs.
- Git refs/commits checked.
- Known gaps in the inventory.
```
