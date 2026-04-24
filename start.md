# Token Economy Start

Universal startup file for any AI agent. Goal: excellent work with minimal context.
This is the canonical startup glue. Platform adapters only point here.
Work only inside the repo root containing `token-economy.yaml`. Use the repo-local markdown wiki as source of truth.

## Prime Directive

Use **Caveman Ultra** by default: terse, exact, high-signal. No filler. No praise padding. Code and quoted errors stay unchanged.

Start every non-trivial task in plan mode: understand intent, inspect reality, make a robust plan, then execute. If your host has an explicit Plan Mode, use it. If not, write a compact plan before changes.

## Boot Sequence

1. Find repo root containing `token-economy.yaml`.
2. Run:
   ```bash
   ./te doctor
   ```
3. Read `token-economy.yaml`.
4. Load only:
   - this file
   - `L0_rules.md` if present
   - `L1_index.md` if present
5. Do not load full wiki pages, raw sources, old sessions, or large docs until retrieval proves relevance.
6. Ignore stale external memory that conflicts with this file or the current user prompt.

## On-Demand Loader

Load only when triggered:

| Trigger | Load |
|---|---|
| Terse style details | `skills/caveman-ultra/SKILL.md` |
| Task >3 steps | `skills/plan-first-execute/SKILL.md` |
| Need wiki memory | `skills/wiki-retrieve/SKILL.md` |
| Writing memory | `skills/wiki-write/SKILL.md` |
| Context warn/refresh | `skills/context-refresh/SKILL.md` |
| Need subagents | `skills/subagent-orchestrator/SKILL.md` |
| `/pa` or `/btw` prompt | `skills/personal-assistant/SKILL.md` |
| Delegation policy | `prompts/delegation-matrix.md` |
| New wiki page | `templates/page.template.md` |

## Context Rules

- Retrieve before reasoning about project/wiki facts.
- Fetch all relevant information, and only relevant information.
- Prefer pointers first: index, search hits, timelines, then full pages.
- At `20%` estimated context used, run:
  ```bash
  ./te context meter --transcript <file>
  ./te context checkpoint --handoff-template
  ```
- If the host cannot clear context, open a fresh session with the packet from `./te context fresh-start`.

## Wiki Rules

The LLM wiki is long-term memory. Treat it as source-managed infrastructure.

- `raw/`: immutable sources. Never rewrite. Add new source notes only.
- `concepts/`, `patterns/`, `projects/`, `people/`, `queries/`: synthesized wiki pages.
- `index.md`: compact catalog. Read first.
- `log.md`: append-only timeline.
- `schema.md`: contract for page types, frontmatter, ingest/query/lint.
- `L0_rules.md`: stable behavior rules.
- `L1_index.md`: compact pointer index.
- `L2_facts/`: durable facts.
- `L3_sops/`: solved-task playbooks.
- `L4_archive/`: cold session archives.

Do not use external note-taking apps, home-directory agent settings, machine-wide config, global MCP config, or external wikis unless the user explicitly asks outside this framework.

Use progressive retrieval:

```bash
./te wiki search "<query>"
./te wiki timeline "<id>"
./te wiki fetch "<id>"
```

Do not fetch a full page unless the compact hit is relevant. When answering from wiki memory, cite page paths or IDs.

## Documentation Rules

Document after verified work, not after intentions.

- Durable discovery: add/update a concept, pattern, project note, L2 fact, or L3 SOP.
- Successful repeated workflow: crystallize into `L3_sops/`.
- Important answer: file into `queries/`.
- Every wiki operation updates `log.md`; material pages update `index.md`.
- Claims need provenance: source path, URL, command, result, or linked note.

## Delegation Rules

Use cheapest capable worker. Keep main context clean.

```bash
./te delegate classify "<task>"
./te delegate plan "<task>"
```

For personal-assistant bypass prompts, route instead of answering from the expensive full-context model:

```bash
./te pa --directive "/pa <prompt>"
```

Delegate only independent work. Give subagents compact briefs with exact scope, files, expected output, and budget. Ask for compact result packets, not full transcripts. Use local/cheap models for search, summaries, simple edits, extraction, lint, and classification. Use frontier models for architecture, ambiguity, high-risk reasoning, and final synthesis.
Subagents are model-agnostic. Pick from whatever models the host has available; route by capability, cost, and context needs, not by vendor name.

## Tool Choices

- Repeated file reads: semdiff.
- Verbose input: ComCom.
- Terminal noise: optional `omni`, `rtk`, or host-native context filter.
- Codebase semantic search: optional `code-review-graph` or `claude-context`.
- Markdown/wiki semantic search: optional `qmd`.

These are optional adapters, not required core dependencies.

## Done Means

Before final response:

- Verify with tests/checks when feasible.
- Record durable facts only after successful execution.
- Update wiki/log for meaningful discoveries.
- Report changed files, verification, and remaining risk briefly.
