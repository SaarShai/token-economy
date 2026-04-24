# Token Economy — Index

Catalog. Read this + schema.md first. Grep folders for topic. Load only matched pages.

## For other agents
- [[AGENT_ONBOARDING]] — **master install guide**: point any agent at this file
- [[start]] — **universal agent entrypoint**: Caveman Ultra, wiki retrieval, 20% context refresh, delegation
- [[adapters/universal/START]] — canonical startup glue used by all platform adapters
- [[L0_rules]] + [[L1_index]] — lean startup memory tiers

## Framework
- [[concepts/optimization-axes]] — 7 axes, tool mappings, gap analysis
- [[schema]] — rigorous LLM wiki ingest/query/lint/crystallize contract
- [[templates/page.template]] — v2 frontmatter page template
- [[prompts/delegation-matrix]] — model-agnostic delegation tiers
- [[skills/caveman-ultra/SKILL]] — Caveman Ultra skill
- [[skills/personal-assistant/SKILL]] — `/pa` and `/btw` bypass router for context-light prompts

## Concepts (techniques)
- [[concepts/caveman-output-compression]] — terse output style, 65% savings
- [[concepts/caveman-compress-session-files]] — rewrite CLAUDE.md etc, 46% avg
- [[concepts/llmlingua]] — token-level perplexity dropping, 2-6x
- [[concepts/prefix-caching]] — 90% cost cut on repeat
- [[concepts/karpathy-wiki]] — offload context to structured KB
- [[concepts/structured-outputs]] — JSON schema vs chat, 3-8x output cut
- [[concepts/speculative-decoding]] — EAGLE-3, Medusa, 2-3x throughput
- [[concepts/kv-cache-eviction]] — StreamingLLM, SnapKV, H2O
- [[concepts/unsloth-distill]] — tiny specialist replaces API call
- [[concepts/superpowers-skills]] — front-load behavior as skill.md

## Patterns
- [[patterns/compound-compression-pipeline]] — stack 4 techniques, 80-90% total
- [[patterns/semantic-diff-edits]] — send diff not full file
- [[patterns/wiki-query-shortcircuit]] — grep vault before re-synthesis
- [[patterns/tiny-model-router]] — 0.5B classifier dispatches

## Roadmap
- [[ROADMAP]] — live tracker: directions, status, next steps

## Infrastructure
- [[bench/README]] — **benchmark registry** (Kaggle + HF), uniform item schema, Kaggle Notebook template for free-GPU evals

## Projects (our builds)
- [[projects/compound-compression-pipeline/RESULTS]] — **ComCom** prototype, 44.5% @ ~Δ−0.25 score (SQuAD eval-v2); eval-v3 in progress
- [[projects/semdiff/README]] — **prototype, 95.5% on large file re-read**
- [[projects/context-keeper/README]] — **prototype, structured PreCompact memory**
- [[projects/context-keeper-v2/README]] — **v2 retrieval API**: `ck_query`, `ck_fetch`, `ck_recent`
- [[projects/wiki-search/README]] — **implemented v1**, progressive disclosure wiki search/timeline/fetch
- [[projects/context-refresh/README]] — fresh-context packet workflow at 20% context
- [[projects/delegate-router/README]] — model-agnostic routing and subagent supervision policy
- [[projects/agents-triage/SKILL]] — **shipped, UserPromptSubmit hook + 5 subagents (wiki-note, quick-fix, local-ollama, research-lite, kaggle-feeder)**

## Universal CLI
- `./te doctor` — verify framework health
- `./te wiki new --template page|decision|source-summary` — create v2 wiki page
- `./te wiki init|index|search|timeline|fetch|lint|ingest|query` — Obsidian wiki operations
- `./te context status|meter|checkpoint|fresh-start|lint-handoff` — context tracking and fresh-session packets
- `./te docs audit|split|load` — always-loaded doc hygiene
- `./te delegate models|classify|plan` — model/subagent routing
- `./te pa --directive "/pa <prompt>"` — personal-assistant prompt bypass and minimal-context dispatch
- `./te hooks doctor`, `./te profile show|set`, `./te bench run --suite framework-smoke` — productization checks

## Infra
- [[raw/2026-04-20-machine-baselines]] — M1/M1B/M2 tok/s, bottlenecks, tweaks
- [[concepts/turboquant-kv-cache]] — KV-cache compression 3.8-5.1x, installed on M2 via llama.cpp fork
- [[raw/2026-04-20-turboquant-research]] — full subagent survey

## People
- [[people/julius-brussee]] — caveman
- [[people/jesse-vincent]] — superpowers (obra)
- [[people/karpathy]] — wiki pattern
- [[people/unsloth-team]] — daniel + michael han

## Raw
- [[raw/2026-04-17-research-brief]] — initial token-efficiency landscape survey
