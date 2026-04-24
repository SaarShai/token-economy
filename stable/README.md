---
type: project
axis: meta
tags: [stable, release, curated]
confidence: high
---

# stable/ — production-ready subset of Token Economy

Curated bundle of the measured, tested tools. Safe to install. Unstable/speculative bits (v2 specs, skill-crystallizer, wiki-search) intentionally excluded.

## What's in

| tool | axis | status | measured |
|---|---|---|---|
| **ComCom MCP** (`projects/compound-compression-pipeline/comcom_mcp/`) | input compression | shipped | 44.9% savings, Δq −0.12 on SQuAD n=8; 57.3% @ Δ +0.08 CI[−0.18,+0.34] on CoQA n=50 |
| **semdiff MCP** (`projects/semdiff/semdiff_mcp/`) | output filter (file reads) | shipped | 95.5% on argparse.py re-read |
| **context-keeper hook** (`projects/context-keeper/`) | cross-session memory (intra only) | shipped | 22 files / 21 cmds / 21 errs extracted per session |
| **skip_detector** (in ComCom pipeline_v2) | verification | shipped, default-on | caught 2/6 adversarial numeric items |
| **rename_detect** (in semdiff core) | verification | shipped, auto-wired | `alpha→gamma` conf=1.0 on test |
| **adversarial_bench.py** | measurement | shipped | CI gate working — caught regression Δ=−1.10 |
| **cost_estimator.py** | measurement | shipped | $ projection over N calls |

## What's NOT in

- context-keeper v2 (L0-L4) — framework-level memory tier, not part of stable measured subset
- skill-crystallizer — spec only
- wiki-search — spec only
- write-gate — doc only
- verify_anthropic.py / verify_logprob.py — written, not end-to-end tested with real API
- bench/adapters beyond CoQA+SQuAD — mixed

These live in the repo root; experiment freely.

## Known limitations (honest)

1. **ComCom damages dense-numeric adversarial content.** Δ=−1.10 CI[−1.90,−0.30] on 10-item adversarial set. skip_detector catches some (versions, %) but not all (temporal, unit comparisons). Use `adversarial_bench.py` as CI gate before trusting a commit.
2. **semdiff small-file overhead.** For files <500 tok, diff output is larger than full — don't use. Argparse-scale wins.
3. **context-keeper intra-session only.** Doesn't persist across sessions. v2 (L0-L4) planned.
4. **Eval statistical power low.** N=8 SQuAD, N=50 CoQA (1 run). Directional not conclusive.

## Install

Two paths — see [`AGENT_PROMPT.md`](AGENT_PROMPT.md) for a ready-to-paste prompt you can give any LLM agent.

- **Human CLI install:** [`INSTALL.sh`](INSTALL.sh) runs the exact commands.
- **Agent-driven:** paste [`AGENT_PROMPT.md`](AGENT_PROMPT.md) into any agent with shell and file access.

## Pinned version

This `stable/` directory is synced from the `main` branch at commit:
```
(see `git rev-parse HEAD` — this subset tracks main)
```

To re-verify before installing: run `scripts/verify_stable.sh` after clone.
