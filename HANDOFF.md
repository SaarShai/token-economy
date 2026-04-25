---
schema_version: 2
title: "Token Economy Current Handoff"
type: handoff
domain: framework
tier: working
confidence: 0.8
created: 2026-04-24
updated: 2026-04-24
verified: 2026-04-24
sources: [start.md, stable/AGENT_PROMPT.md, token-economy.yaml]
supersedes: []
superseded-by:
tags: [handoff, repo-local, startup]
---

# Token Economy Current Handoff

## Current Contract

Token Economy is a repo-local, model-agnostic agent framework. The source of truth is this repository plus its interlinked markdown wiki. Agents start from `start.md`, load only `L0_rules.md` and `L1_index.md`, retrieve project facts on demand, and document durable findings only after verified work.

## Active Setup

- Current local working folder: the active project workspace
- Canonical repo: `https://github.com/SaarShai/token-economy.git`
- Config: `token-economy.yaml`
- Startup glue: `start.md`
- Startup adapters: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/token-economy.mdc`
- Wiki commands: `./te wiki search`, `./te wiki timeline <id>`, `./te wiki fetch <id>`
- Context commands: `./te context status`, `./te context meter`, `./te context checkpoint`, `./te context fresh-start`
- Delegation commands: `./te delegate classify`, `./te delegate plan`, `./te pa`

## Non-Negotiables

- Work inside the current working folder for the active project, not the template repo checkout.
- Do not edit home-directory agent settings, machine-wide config, global MCP config, or external wikis unless the user explicitly requests work outside this framework.
- Use repo-local markdown wiki pages and real wikilinks such as `[[start]]` or `[[projects/wiki-search/README]]`.
- Keep always-loaded files tiny. Put details behind `L1_index.md`, skills, prompts, templates, or wiki pages.
- Keep normal prompt hooks quiet. Use `/pa` or `/btw` for explicit context-light routing.
- Refresh context near 20% used with a compact handoff packet. Use `summ` for manual refresh: only the lean handoff enters fresh context; durable memory goes to the wiki-documenter worker. Claude can use native `/clear`; Codex current-thread clearing is not solved in the tested environment, so distinguish it from fresh-successor continuation.
- If setup starts in a folder without `token-economy.yaml`, the canonical setup prompt permits clearing that folder only, then cloning fresh.

## Verification Baseline

Before release or handoff, run:

```bash
./INSTALL.sh --dry-run
./te doctor
./te hooks doctor
./te wiki index
./te wiki lint --strict --fail-on-error
bash scripts/run_all_tests.sh
```

## Fresh-Agent Prompt

Use the current prompt in `stable/AGENT_PROMPT.md`. It explicitly authorizes cloning the canonical repo into the current folder, blocks global writes, requires repo-local wiki retrieval, and tells the agent to drop setup-only context after installation.
