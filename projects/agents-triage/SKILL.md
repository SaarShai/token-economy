---
name: agents-triage
description: Classifies each user prompt with regex + local-Ollama before the main model thinks. Emits a directive suggesting which subagent/model should handle the task. Goal — avoid spending opus tokens on tasks solvable by haiku/sonnet/local models. Use when paired with the UserPromptSubmit hook and the bundled subagent definitions.
---

# agents-triage — bypass opus for simple tasks

## Problem
User runs opus-4.7-1M (high-effort) as default. Many tasks — wiki notes, one-line fixes, factual lookups — don't need opus. Opus burns thinking tokens deciding this each time.

## Approach (3-layer)

### Layer 1: pre-model hook (`UserPromptSubmit`)
`hook.sh` runs BEFORE main model sees prompt. Calls `classify.py`:
- **Regex fast-path** (<5ms) matches known patterns.
- **Ollama fallback** (<1.5s) — local `qwen3:8b` classifies if regex uncertain.

Outputs JSON + directive block appended to context:
```json
{"tier": "simple|medium|hard", "agent": "wiki-note|quick-fix|local-ollama|research-lite|none",
 "model": "haiku|sonnet|opus|local:<model>", "confidence": 0-1, "reason": "...", "lean_context": [...]}
```

### Layer 2: opus sees directive, dispatches via Task tool
Opus reads `⚡ [agents-triage] ...` block → emits `Task(subagent_type, model, prompt)` immediately. Minimal thinking because the directive already specifies what to do.

Full opus bypass isn't possible (CC always routes through main model), but the directive keeps opus' thinking budget near zero on simple tasks.

### Layer 3: specialized subagents
Five bundled agents, each minimal-context:
- **wiki-note** (haiku) — repo-local wiki edits only. Read+Write+Glob+Grep, no Bash.
- **quick-fix** (haiku) — small scoped edits, one `Bash` verify max.
- **local-ollama** (haiku coordinator) — shells out to local Ollama models, zero API cost for the actual work.
- **research-lite** (haiku) — ≤5 web calls, ≤800-word output.
- **kaggle-feeder** (haiku) — archived Kaggle eval pipeline maintainer for queued notebook runs.

## Install

Project-local:
```bash
bash projects/agents-triage/install.sh
```

This:
1. Symlinks skill -> `.claude/skills/agents-triage/`.
2. Copies agent definitions -> `.claude/agents/` including `kaggle-feeder`.
3. Adds `UserPromptSubmit` hook to `.claude/settings.json` when project settings are supported.

Project-scoped variant:
```bash
bash projects/agents-triage/install.sh --project
```

## Override
Type `NO TRIAGE` (anywhere in prompt) → hook exits silently → opus gets prompt normally.

## Environment vars
- `AGENTS_TRIAGE_NO_OLLAMA=1` — skip Ollama fallback, regex-only.
- `AGENTS_TRIAGE_LOG=/path` — log every classification to file.

## Cost math
Typical prompt path (simple task):
- **Without triage**: opus sees prompt → thinks → acts → writes → verifies. ~3-8K tokens.
- **With triage**: hook runs (0 tokens) → opus sees directive + prompt → emits Task (~200 tokens) → haiku subagent does work (~500-2000 tokens haiku cost).
- **Net**: ~70-90% token cost reduction on simple tasks, per our informal estimate. Verification pending.

## Known failure modes
1. **False-positive classification** → wrong subagent gets the task, returns "escalate", opus re-handles. Small wasted round-trip.
2. **Ollama down** → falls back to regex only. Still works; coverage narrower.
3. **User prompt is adversarial to classifier** (e.g., says "this is simple: [complex thing]") → will mis-route. Mitigation: opus can still override the directive.
4. **Subagent can't escalate mid-task** → if wiki-note realizes the job needs opus, it has to return "escalate" and wait.

## Research lineage
Pattern inspired by:
- OpenRouter / Not Diamond routing layer.
- RouteLLM paper (2024).
- Claude Code Task tool + subagent_type.
- Orchestrator-worker multi-agent papers 2024-2026.

See `raw/2026-04-19-triage-patterns.md` for full survey.

## Files
```
projects/agents-triage/
├── SKILL.md        (this file)
├── classify.py     (regex + Ollama classifier)
├── hook.sh         (UserPromptSubmit entry)
├── install.sh      (wires into project-local `.claude/`)
└── agents/
    ├── wiki-note.md
    ├── quick-fix.md
    ├── local-ollama.md
    ├── research-lite.md
    └── kaggle-feeder.md
```
