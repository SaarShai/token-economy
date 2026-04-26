# Token Economy Usage Index

Catalog for a target project that uses Token Economy locally. Load only matched pages.

## Startup
- [[start]] — universal agent entrypoint: operating rules, retrieval, context refresh, delegation
- [[L0_rules]] + [[L1_index]] — lean startup memory tiers
- [[schema]] — repo-local markdown wiki contract
- `token-economy.yaml` — local framework config

## Commands
- `./te doctor` — verify local framework health
- `./te wiki search "topic"` — find relevant wiki pointers
- `./te wiki timeline "<id>"` — inspect nearby context
- `./te wiki fetch "<id>"` — load a relevant page
- `./te wiki context "task"` — build an audited bounded context packet
- `./te code map "symbol or path"` — inspect compact code structure before file reads
- `./te wiki lint --strict` — validate wiki pages
- `./te context status` — inspect context budget
- `./te context checkpoint --handoff-template` — create a lean continuation packet
- `./te delegate classify "task"` — classify work for delegation
- `./te delegate document --verified ...` — route verified durable evidence to wiki-documenter
- `./te pa --directive "/pa <prompt>"` — route context-light personal-assistant prompts

## Wiki Layout
- `raw/` — source summaries and imported evidence
- `projects/` — active target-project state
- `L2_facts/` — verified durable facts
- `L3_sops/` — reusable workflows and runbooks
- `queries/` — durable Q&A
- `L4_archive/` — cold history kept only when useful

## Prompt Workflows
- [[prompts/complete-migrate-export]] — export an old project into `complete_migrate_export dot md`
- [[prompts/complete-migrate-import]] — import `complete_migrate_export dot md` into a new Token Economy-enabled target folder
- [[prompts/summ]] — context refresh workflow
- [[prompts/summarize-for-handoff]] — handoff packet template

## Extension Points
- [[adapters/README]] — project-local agent adapters
- `token_economy/code_map.py` — compact structural code-map provider
- [[concepts/framework-hardening-adoption]] — ranked adoption matrix and current hardening learnings
- [[concepts/lean-execution]] — plan/context/delegation pruning rules and source synthesis
- [[raw/2026-04-25-agent-memory-framework-research-rerun]] — Gemini and local Gemma research outputs
- [[concepts/local-model-setup]] — current M1/M1B/M2 local model policy
- [[templates/page.template]] — wiki page template
- [[templates/source-summary.template]] — source summary template
- [[templates/decision.template]] — decision template
