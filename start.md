# Token Economy Start

Startup glue. Goal: excellent work, minimal context.
Work only inside the repo root containing `token-economy.yaml`. Use the repo-local markdown wiki as source of truth.

Default: use Token Economy for the current target project. Do not treat this as framework work unless the user explicitly asks to maintain Token Economy. Framework files, `ROADMAP.md`, and `projects/` are not target goals.

## Prime Directive

Use **Caveman Ultra**: terse, exact, high-signal. No filler/praise padding, no softening, no conversational lead-ins. Code and quoted errors stay unchanged.

Start non-trivial tasks in plan mode: short plan, inspect reality, execute.

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
6. Determine target project from prompt, handoff, imported summary, or project wiki.
7. Ignore stale external memory that conflicts with this file or the current user prompt.

## On-Demand Loader

Load only when triggered:

| Trigger | Load |
|---|---|
| Terse style details | `skills/caveman-ultra/SKILL.md` |
| Task >3 steps | `skills/plan-first-execute/SKILL.md` |
| Need wiki memory | `skills/wiki-retrieve/SKILL.md` |
| Writing memory | `skills/wiki-write/SKILL.md` |
| Context refresh/clear/`summ` | `skills/context-refresh/SKILL.md` |
| Need subagents | `skills/subagent-orchestrator/SKILL.md`; `prompts/subagents/lifecycle.prompt.md` |
| GitHub repo maintenance | `prompts/subagents/repo-maintainer.prompt.md` |
| `/pa` or `/btw` prompt | `skills/personal-assistant/SKILL.md` |
| Before completion claim | `skills/verification-before-completion/SKILL.md` |
| Delegation policy | `prompts/delegation-matrix.md` |
| New wiki page | `templates/page.template.md` |

Maintainer-only docs/skills (`ROADMAP.md`, `HANDOFF*.md`, `AGENT_ONBOARDING.md`, external-adoption skill) require explicit framework-maintenance intent.

## Context Rules

- Retrieve before reasoning about project/wiki facts.
- Check relevant skills before action; load only matching skills.
- Fetch all relevant information, and only relevant information.
- Prefer pointers first: index, search hits, timelines, then full pages.
- At `20%` estimated context used: `./te context status`, `./te context meter --transcript <file>`, `./te context checkpoint --handoff-template`.
- For `summ`, use host-native clear/compact when available; then continue only in fresh context.
- If the host cannot clear context, open a fresh session with only `./te context fresh-start` output + `start.md`.

## Wiki Rules

The LLM wiki is long-term memory for the current target project. Bundled framework wiki pages are not target goals/tasks unless the user explicitly says the target project is Token Economy itself.

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

Fetch full pages only after compact relevance. Cite wiki paths/IDs.

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

Keep normal prompt hooks quiet unless `TOKEN_ECONOMY_CLASSIFY_ALL=1` is explicitly set. Use `/pa` or `/btw` when a prompt should bypass the full-context model.

Delegate only independent work. Give compact briefs: scope, files, output, budget. Ask for compact result packets, not transcripts. Use cheap models for search, summaries, simple edits, extraction, lint, classification; frontier models for architecture, ambiguity, high-risk reasoning, final synthesis. Subagents are model-agnostic. Close only after results are captured and documented/merged.

GitHub remote? Use `prompts/subagents/repo-maintainer.prompt.md` at verified save-points. No GitHub remote? Skip.

## Done Means

Before final response:

- Verify with tests/checks when feasible.
- Record durable facts only after successful execution.
- Update wiki/log for meaningful discoveries.
- Report changed files, verification, and remaining risk briefly.
