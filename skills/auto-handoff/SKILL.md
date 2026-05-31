---
name: auto-handoff
description: UserPromptSubmit hook that auto-checkpoints at ~50% context fill and hands the task to a fresh session. Default mode is detection-only — it writes a lean handoff packet and injects a ready-to-run interactive launch command (reuses your subscription auth). Opt-in mode=spawn launches a headless `claude -p` successor (needs an API key — 401s on OAuth-only). Claude Code only, behind loop/cost rails. Distinct from `handoff` (slash-only) — does NOT modify it.
model: haiku
effort: low
tools: [Bash, Read, Write]
---

# auto-handoff — auto-checkpoint + headless successor at ~50% fill

## What it does

Every turn, a `UserPromptSubmit` hook estimates context fill from the transcript.
When fill crosses the **refresh threshold (default 50%)**, it:

1. writes a lean handoff **packet** (reuses handoff's tested `checkpoint()` with
   the transcript so the packet carries files/commands/errors; local fallback if
   `handoff/_lib` is gone),
2. **hands off** — default `mode=notify` (detection-only): injects a
   `<system-reminder>` with the packet path + a ready-to-run interactive
   `claude --add-dir … "<continue prompt>"` for you to launch in a fresh
   subscription session. Opt-in `mode=spawn` instead launches a detached headless
   `claude -p` successor and surfaces its pid + log (needs an API key — see Auth).

This is the capability the repo dropped in v1.3.0 (`context-refresh`'s
auto-launcher, "never worked reliably"). It works now because two primitives
exist that didn't then:
- `UserPromptSubmit` hooks fire **every turn** and receive `transcript_path` — a
  real per-turn trigger (no more "agent must remember to run `./te context status`").
- `claude` gained safe headless-spawn flags: `-p`, `--add-dir`, `--max-budget-usd`.

## Trigger & fire sequence

```
UserPromptSubmit ──> hook.py
   AUTO_HANDOFF_DISABLE set?        ─► exit 0   (successors carry this)
   gen >= cap?                      ─► exit 0
   fill < threshold?                ─► exit 0
   cooldown / same transcript?      ─► exit 0
   else: write packet ─► notify (default) | spawn `claude -p` (opt-in) ─► emit directive ─► exit 0
```

The hook **always exits 0** (a non-zero `UserPromptSubmit` hook can block the
user's prompt). Any error degrades to a silent exit 0.

## Configuration

Two equivalent sources, **env wins over config**:
- **Env vars** — for whoever launches the Claude Code process (can't change mid-session).
- **`.token-economy/auto-handoff/config.json`** — read fresh every turn, so this is
  the **only knob that works mid-session** (the running process env is fixed).
  Keys map 1:1 to the vars below (`mode`, `refresh_at_pct`, `cooldown`,
  `budget_usd`, `gen_cap`, `context_max`, `disable`, `dryrun`).

| Var | Default | Meaning |
|-----|---------|---------|
| `AUTO_HANDOFF_MODE` | `notify` | `notify` (detection-only) or `spawn` (headless `claude -p`, needs API key) |
| `REFRESH_AT_PCT` | `0.50` | fire threshold (accepts `0.50` or `50`) |
| `TOKEN_ECONOMY_CONTEXT_MAX` | `200000` | context window for the fill ratio (Opus) |
| `AUTO_HANDOFF_BUDGET_USD` | `2` | `--max-budget-usd` cap on the successor (spawn mode) |
| `AUTO_HANDOFF_COOLDOWN` | `1800` | seconds between fires |
| `AUTO_HANDOFF_GEN_CAP` | `3` | max successor depth (backstop) |
| `AUTO_HANDOFF_DRYRUN` | unset | spawn mode: build + log the command, don't launch |
| `AUTO_HANDOFF_DISABLE` | unset | truthy ⇒ hook no-ops (set automatically in every successor) |

## Safety rails

1. **Anti-fork-bomb (spawn mode):** every successor is launched with
   `AUTO_HANDOFF_DISABLE=1`, so its own hook no-ops and it can never spawn a
   grandchild. `AUTO_HANDOFF_GEN_CAP` is a second backstop.
2. **No thrash:** cooldown window + same-or-smaller transcript dedup.
3. **Cost (spawn mode):** `--max-budget-usd` cap on the successor.
4. **Reliability:** hook always exits 0 — never blocks a turn.
5. **Visibility:** every fire (notify or spawn) is appended to
   `.token-economy/auto-handoff/manifest.json`; spawn-mode successor output →
   `successor-<ts>.log`.
6. **Dry-run (spawn mode):** `AUTO_HANDOFF_DRYRUN=1` builds + logs the command
   without launching.

## Install (opt-in — wires the live hook)

```bash
bash skills/auto-handoff/tools/install.sh --dry-run   # preview the settings.json merge
bash skills/auto-handoff/tools/install.sh --project   # actually wire it
```

Mirrors `context-keeper`: symlinks the skill into `.claude/skills/auto-handoff`
and idempotently adds the `UserPromptSubmit` hook to `.claude/settings.json`.

## Known limitations

- **Headless spawn needs an API key (auth).** `mode=spawn` runs `claude -p`,
  which bills as a metered API workload and authenticates via
  `ANTHROPIC_API_KEY` / `apiKeyHelper`. On OAuth-only (Pro/Max subscription) it
  **401s — verified live** (pid + direct shell both failed). The default
  `mode=notify` sidesteps this: it hands you an interactive command that reuses
  your logged-in subscription session.
- **Parallel-work conflict (spawn mode only).** A spawned successor and the
  current session can both touch the repo until the parent winds down (a hook
  can't terminate its host). Isolated worktrees are the fix but **not**
  auto-created (the filesystem-safety rule forbids unconfirmed `.git` ops in
  `~/Documents`). In `notify` mode you launch the successor yourself, so this
  doesn't arise. Future: opt-in `AUTO_HANDOFF_WORKTREE=1`.
- **Mechanical packet quality.** The unattended packet is regex-extracted, not
  agent-summarized — lower fidelity than `/handoff`. The successor starts in plan
  mode and re-derives, which absorbs most of the gap.
- **char/4 fill estimate.** Approximate (no provider tokenizer); conservative
  (slightly over-counts ⇒ fires a touch early). Tune with
  `TOKEN_ECONOMY_CONTEXT_MAX` / `REFRESH_AT_PCT`.

## Relationship to other skills

- **`handoff`** — slash-only, writes a doc, **no successor launch**. Untouched by
  this skill. Use it for manual/interactive handoffs.
- **`context-keeper`** — `PreCompact` hook (fires at compaction, ~full), preserves
  structured memory. auto-handoff fires *earlier* (50%) and *acts* (notify, or opt-in spawn).

## Files

```
tools/
├── hook.sh      # UserPromptSubmit shim (always exit 0)
├── hook.py      # meter + gate + packet + spawn + directive
├── meter.py     # fill% from transcript message content
├── relay.py     # threshold/cooldown/dedup gate (adapted from handoff/_lib/context.py)
├── packet.py    # lean packet (reuse checkpoint() with transcript; local fallback)
├── spawn.py     # notify (interactive cmd) + opt-in headless `claude -p` + manifest
├── tokens.py    # char/4 estimator (repo-standard copy)
├── install.sh   # idempotent UserPromptSubmit wiring (mirrors context-keeper)
├── test_meter.py
└── test_hook.py # gate + packet + loop-safety (all dry-run)
```

## Lineage

Supersedes `context-refresh`'s auto-launcher (dropped v1.3.0). The "no per-turn
trigger" cause is fixed by the `UserPromptSubmit` hook. The "fragile blind
`claude …` shell-out" cause proved **still real**: a live test showed headless
`claude -p` 401s under OAuth-only auth — so the **default is detection-only
`notify`** (hand the user an interactive launch command), with headless `spawn`
as an opt-in for API-key setups.
