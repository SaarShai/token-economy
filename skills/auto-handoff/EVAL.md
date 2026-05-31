# auto-handoff — EVAL

Status: **built, tested, activated (2026-05-31), and pivoted to `mode=notify`
after a live failure** (see Live activation test). Default mode spawns nothing —
it hands the user an interactive launch command. The headless `spawn` path is
opt-in and exercised only in dry-run here.

## Tests

```
python3 skills/auto-handoff/tools/test_meter.py   # fill meter
python3 skills/auto-handoff/tools/test_hook.py    # gate + packet + loop-safety (dry-run)
```

### Meter (test_meter.py) — 4/4

| Case | Result |
|------|--------|
| 55% transcript | `pct 55.68` → `action refresh` |
| 20% transcript | `pct 20.24` → `action continue` |
| `REFRESH_AT_PCT=18` override | threshold 0.18 → `refresh` |
| missing/empty transcript | `0` tokens → `continue` (no crash) |

Content-vs-raw: estimate from message content `5568` < raw-bytes `7577` — JSON
scaffolding (event keys, uuids, tool envelopes) is excluded from the fill %.

### Gate + packet + loop-safety (test_hook.py) — 8/8

| Case | Result |
|------|--------|
| `packet.reuse` | `checkpoint()` reuse path → `…-fresh-session.md` (2537b), carries transcript facts, "Start in plan mode" present |
| `packet.fallback` | handoff/_lib absent → local fallback packet written, plan-mode instruction present |
| `gate.fire@55% notify` | default mode → manifest `status=notified`; cmd = `claude --add-dir … "<prompt>"` (no `-p`, no budget); `pending-relay.json` written |
| `gate.fire@55% spawn/dry` | `mode=spawn` → manifest `status=dryrun`; cmd has `claude -p … --max-budget-usd` |
| `gate.cooldown` | immediate re-run → no re-fire |
| `loop-safety.disable` | `AUTO_HANDOFF_DISABLE=1` → no fire **and writes nothing** |
| `loop-safety.gen-cap` | `AUTO_HANDOFF_GEN≥cap` → no fire |
| `gate.below@20%` | below threshold → no fire |

All cases `returncode 0` (reliability contract: the hook never blocks a turn).

## Headless spawn contract (opt-in `mode=spawn`, dry-run CLI)

```
$ AUTO_HANDOFF_DRYRUN=1 python3 skills/auto-handoff/tools/spawn.py --repo . --packet /tmp/ah-packet.md
status: dryrun
cmd: claude -p --add-dir . --max-budget-usd 2 'Read /tmp/ah-packet.md only. Continue from that handoff. Start in plan mode. Do not load anything else until retrieval proves relevance.'
child_gen: 1   disable_in_child: True
```

Child carries `AUTO_HANDOFF_DISABLE=1` + `AUTO_HANDOFF_GEN=1` → cannot spawn a
grandchild (anti-fork-bomb), and spend is capped by `--max-budget-usd`.

## Install (idempotent, not activated)

```
$ bash skills/auto-handoff/tools/install.sh --dry-run
dry-run: would symlink … → .claude/skills/auto-handoff
dry-run: would add UserPromptSubmit hook to .claude/settings.json
dry-run: no files changed.        # settings.json md5 identical before/after
```

Merge idempotency (temp settings, run twice): auto-handoff command added **once**,
a pre-existing unrelated `UserPromptSubmit` hook **preserved** (not clobbered).

## Live activation test (2026-05-31)

Activated with `install.sh --project`, then fired for real on the next turn at
**79.68%** fill. Findings:

- **Trigger works:** the `UserPromptSubmit` hook detected the threshold and fired
  on a real session unaided.
- **Headless spawn fails on OAuth-only auth:** the `mode=spawn` successor (pid
  75757) exited with `API Error: 401 Invalid authentication credentials`. A plain
  `claude -p` from the user's own shell 401'd identically; `ANTHROPIC_API_KEY` is
  unset (subscription auth) → headless print mode has nothing to authenticate
  with. The old "fragile spawn" lesson, reconfirmed.
- **Pivot:** default changed to `mode=notify` (detection-only). The notify
  directive was verified live against the real transcript — writes the packet and
  emits the interactive `claude --add-dir … "<prompt>"` command for the user to
  launch in a subscription session. No API key, no metered spend.

Left live in `mode=notify` (via `config.json`), threshold raised for testing.

## Known limitations

See SKILL.md → "Known limitations": parallel-work conflict (no auto-stop of the
parent; worktree isolation deferred per filesystem-safety rule), mechanical
(regex) packet fidelity < agent-summarized, char/4 fill estimate is approximate.

## Not yet measured

- **notify launch quality:** does a fresh session booted from the packet actually
  continue correctly, or does it need to ask the parent? (packet sufficiency)
- **false-fire rate** at the threshold over real sessions.
- **headless `spawn`** end-to-end — blocked here by auth; needs an API-key setup
  to measure.
