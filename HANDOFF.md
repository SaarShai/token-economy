---
type: handoff
date: 2026-04-22
audience: next-agent (fresh session)
purpose: resume Token Economy work without re-learning
---

# Token Economy — HANDOFF

**One-liner.** Research workspace building tools that reduce LLM token/compute consumption without quality loss. Shipped: ComCom (compression+verify), semdiff (AST file-diff), context-keeper (PreCompact memory), agents-triage (model routing), TurboQuant llama-server wrapper. Active infra: 2-node EXO cluster + Ollama on 3 Macs + Kaggle eval pipeline.

**Mode**: CAVEMAN active (full). Drop articles, filler, hedging. Fragments OK. Code blocks unchanged.

---

## 0. Roots

| thing | path |
|---|---|
| GitHub repo | https://github.com/SaarShai/token-economy (branch `main`, `gh auth status` shows token in keyring) |
| Wiki root | `/Users/saar/Documents/Spark Obsidian Beast/Token Economy/` |
| Agent-install doc | `AGENT_ONBOARDING.md` (modes A/B/C) + `stable/AGENT_PROMPT.md` (copy-paste for any MCP client) |
| Live inventory | [[concepts/devices-inventory]] — auto-generated per-device state + models + services |
| Live index | [[index]] + [[ROADMAP]] + [[log.md]] |
| Governance | [[concepts/wiki-governance]] + [[concepts/optimization-axes]] |

---

## 1. Devices

| id | role | IP | user | RAM | SSH |
|---|---|---|---|---|---|
| **M2** | this machine (CC host, Ollama, TurboQuant llama-server, dev) | localhost | saar | 64GB Apple M2 Max | (local) |
| **M1** | EXO master + Farey Ollama runner | 192.168.1.218 | new | 32GB M1 Max | `ssh -i /Users/saar/.ssh/id_ed25519 -F /dev/null -o StrictHostKeyChecking=no new@192.168.1.218` |
| **M1B** | EXO worker | 192.168.1.64 | za | 32GB M1 Max | `ssh -i /Users/saar/.ssh/id_ed25519 -F /dev/null -o StrictHostKeyChecking=no za@192.168.1.64` |

Standard SSH flags: `-i /Users/saar/.ssh/id_ed25519 -F /dev/null -o StrictHostKeyChecking=no -o ConnectTimeout=10`.

---

## 2. Endpoints

| service | url | auth | notes |
|---|---|---|---|
| EXO (M1 master) | http://192.168.1.218:52415 | none | OpenAI-compat `/v1/chat/completions`. Model: `mlx-community/Qwen3.6-35B-A3B-5bit`. Layer split M1B=0-19, M1=19-40. **Unreliable — mid-gen drops, TB-bridge misconfig on M1B**. Fix pending (see [[concepts/devices-inventory]] §known-issues). |
| Ollama M2 | http://localhost:11434 | none | Models: qwen3.5:35b, qwen3:8b, phi4:14b, gemma4:26b, gemma4:31b, deepseek-r1:32b, qwen3.6:latest, others. |
| Ollama M1 | http://192.168.1.218:11434 | none | Models: deepseek-r1:32b, qwen3.5:35b, qwen3:8b, research-* variants. |
| TurboQuant llama-server (M2) | http://localhost:8080 (when up) | none | Started via `~/bin/llama-tq start <gguf>`. Default asymmetric `-ctk q8_0 -ctv turbo4`. See [[concepts/turboquant-kv-cache]]. |
| ComCom MCP | stdio | none | `python3.11 ~/Documents/Spark\ Obsidian\ Beast/Token\ Economy/projects/compound-compression-pipeline/comcom_mcp/server.py` |
| semdiff MCP | stdio | none | Same pattern, `projects/semdiff/semdiff_mcp/server.py` |

---

## 3. Credentials (locations only — rotate after session)

| what | location | status |
|---|---|---|
| SSH key | `~/.ssh/id_ed25519` | single key for M1/M1B |
| GitHub | `gh auth status` → `gho_...` in keyring, account `SaarShai` | scopes: `gist, read:org, repo, workflow` |
| Kaggle | `~/.kaggle/kaggle.json` (user `saarshai`) | **token pasted in chat earlier — rotate** |
| Anthropic | per-CC-session, not stored locally | — |
| HuggingFace | `~/.cache/huggingface/token` (if set) | check before gated pulls |
| Ollama / EXO | no auth | — |

---

## 4. Installed MCP servers + skills + agents + scheduled tasks

### MCP servers (CC user scope — see `~/.claude.json`)

- `comcom` ✓ — 4 tools: `comcom_compress`, `comcom_skip_check`, `comcom_verify`, `comcom_estimate_cost`
- `semdiff` ✓ — 3 tools: `read_file_smart`, `snapshot_clear`, `snapshot_status`
- `omni` ✓ — external, Rust; terminal-output filter (90% claim from vendor)

### Hooks (in `~/.claude/settings.json`)

- PreToolUse (Bash) → `omni --pre-hook`
- PostToolUse (Bash) → `omni --post-hook`
- PreCompact → `node ~/.claude/hooks/pre-compact.js` + **`bash ~/.claude/skills/context-keeper/hook.sh`**
- SessionStart → `omni --session-start`
- UserPromptSubmit → `bash <repo>/projects/agents-triage/hook.sh`

### Skills (in `~/.claude/skills/`)

- `context-keeper` (PreCompact structured memory, hook active)
- `agents-triage` (model-routing hook, see [[projects/agents-triage/SKILL]])

### Subagents (in `~/.claude/agents/`)

- `wiki-note`, `quick-fix`, `local-ollama`, `research-lite`, `kaggle-feeder`, `turboquant-local` — bundled
- plus plugin-provided: `adversarial-reviewer`, `architect`, `build-error-resolver`, `chief-of-staff`, `code-reviewer`, `doc-updater`, `harness-optimizer`, `planner`, etc.

### Scheduled tasks (via `mcp__scheduled-tasks__list_scheduled_tasks`)

- `resume-qwen36-downloads` (v1, **disabled**)
- `resume-qwen36-downloads-v2` (**armed**, fires once — Qwen3.6 already complete on both nodes so likely no-op)
- `download-two-thinking-models` (**disabled** — Qwen3-Next-80B-Thinking + DeepSeek-R1-Distill-70B MLX 4bit, paused)

---

## 5. Reading order (fresh agent)

1. **[[index]]** — wiki catalog, links to everything.
2. **[[ROADMAP]]** — live tracker: 11 directions, status, next steps.
3. **[[AGENT_ONBOARDING]]** — install modes for new clients.
4. **[[concepts/optimization-axes]]** — 7 axes + tool-to-axis mapping.
5. **[[concepts/wiki-governance]]** — schema, supersession, hooks.
6. **[[concepts/devices-inventory]]** — ground truth on machines.
7. **Per-project READMEs**:
   - [[projects/compound-compression-pipeline/RESULTS]] — ComCom eval history
   - [[projects/semdiff/README]] + [[projects/semdiff/INSTALL]]
   - [[projects/context-keeper/README]] (+ v2 spec dir)
   - [[projects/agents-triage/SKILL]]
   - [[projects/skill-crystallizer/README]] (spec)
   - [[projects/wiki-search/README]] (spec)
   - [[projects/write-gate/README]]
8. **[[stable/README]]** — curated production subset + install script.

---

## 6. Measured results (quick reference)

| tool | metric | value | CI / caveat |
|---|---|---|---|
| ComCom D_adaptive (SQuAD n=8) | savings | 44.9% | Δq −0.12 [−0.38, 0.00] |
| ComCom (CoQA n=50 Kaggle v8) | savings | 57.3% | Δq −0.16 [−0.40, +0.06] |
| ComCom + skip_heuristics | adversarial Δscore | **+0.00** [+0.00, +0.00] | passes 10-item adversarial bench |
| semdiff (argparse.py re-read, 2 edits) | savings | **95.5%** | 19280 → 859 tok |
| semdiff (stable re-read) | savings | 99.5% | 101 tok |
| TurboQuant turbo4 (M5 data) | KV compress | 3.8× | +0.23% PPL |
| context-keeper v1 (100-turn session) | facts extracted | 22 files / 21 cmds / 21 errs | no quality eval yet |

Kaggle result files: `projects/compound-compression-pipeline/kaggle_results/v{4,7,8}-*.jsonl`.

---

## 7. Done / In-progress / Blocked

**Done** (shipped + measured):
- ComCom (pipeline_v1, pipeline_v2 + skip_heuristics + verify + verify_anthropic + verify_logprob + respect_skip default).
- semdiff (core, rename_detect, ignore_comments, MCP server, CC plugin wrapper). Multi-lang tested.
- context-keeper v1 (PreCompact hook active, confidence tagging).
- agents-triage (hook + 6 subagents + classify.py with TurboQuant route).
- TurboQuant built on M2 (`~/src/llama-cpp-turboquant/build/bin/llama-server`, `~/bin/llama-tq` wrapper).
- bench/ infra (25 adversarial categories, 7 datasets registered, Kaggle kernel pipeline).
- Stable bundle (`stable/` + INSTALL.sh + AGENT_PROMPT.md).
- Kaggle evals v4/v7/v8 complete + committed.
- EXO cluster architecturally working (2-node, layer split verified, short-gen OK).
- Qwen3.6-35B-A3B-5bit downloaded on M1 + M1B.
- `concepts/devices-inventory.md` auto-generated.

**In-progress / unstable**:
- EXO mid-gen drops (TB bridge 169.254 issue on M1B). Fix drafted twice (sonnet subagent dispatches rejected by user); next agent can try minimal-diff approach — see [[concepts/devices-inventory]] §known-issues and `EXO_P2P_STATUS.md` in Farey folder.
- context-keeper v2 (L0-L4 tier_manager + l1_indexer shipped, not benchmarked).
- skill-crystallizer (detector.py compiles, not wired).
- wiki-search (spec + schema.sql only, no impl).

**Blocked / waiting**:
- Qwen3-Next-80B-A3B-Thinking + DeepSeek-R1-Distill-Llama-70B downloads (scheduled task **paused**).
- N=50+ Kaggle CoQA eval (tighter CI).

---

## 8. Open directions (from [[ROADMAP]])

Priority order:
1. **Fix EXO mid-gen drops** — path B: force WiFi inter-node transport (launch flag or route-level block of 169.254). See sonnet-subagent prompt history in transcript.
2. Run adversarial sweep on Kaggle for all 25 categories (one big kernel).
3. Quality eval for context-keeper v1 (synthetic compaction fact-retention).
4. Wire rename_detect into semdiff MCP signature-hash mode.
5. Run first Kaggle notebook via `kaggle-feeder` subagent.
6. Benchmark TurboQuant'd Qwen3.6 vs vanilla Ollama on M2 (needs GGUF path — check `concepts/turboquant-kv-cache` §usage).
7. Activate GitHub Actions CI (`.github/workflows/adversarial_bench.yml` shipped, not enabled).

---

## 9. Governance rules (do NOT break)

- **Caveman mode full**. Terse. Code unchanged. Errors quoted exact.
- **Computational verification gate** (per `~/.claude/rules/common.md`): any claimed theorem/asymptotic → numerical verify with mpmath/10⁵ terms before use.
- **Destructive op protocol**: rename before delete; document before act; restart EXO only per documented procedure.
- **Delegation preference**: cheap models first (local Ollama / haiku / sonnet) → opus only for complex reasoning. See [[projects/agents-triage/SKILL]].
- **Model-routing**: see `/Users/saar/Desktop/Farey-Local/model_context/MODEL_ROUTING.md` for Farey; for Token Economy use [[concepts/optimization-axes]] + triage classifier.
- **Commit + push after substantive changes**. Branch `main`.
- **Do not touch**: EXO cluster-wide settings (peer discovery, bootstrap, libp2p port); `~/.exo/event_log/` (except documented restart `.bin`+`.bin.zst` clear); any `.safetensors`; user's launchd / cron beyond own scripts.

---

## 10. Known failure modes + recoveries

| symptom | cause | fix |
|---|---|---|
| EXO `nodes=0` | stale `event_log/` peer cache | `rm event_log/{master,api}/*.bin*` both nodes, restart M1 `--force-master` first, then M1B bootstrap | 
| EXO instance disappears | inactivity eviction | re-POST `/place_instance` |
| EXO mid-gen drop | TB 169.254 link-local misrouting | unfixed — needs advertise-addr flag OR route blackhole 169.254/16 |
| qwen3.5:35b empty output | too-long multi-spec prompt | split to atomic; use deepseek-r1:32b instead |
| Kaggle kernel CUDA error | torch sm_75 dropped | force CPU path with Qwen2.5-1.5B/3B |
| ComCom damages dense-numeric | skip_heuristics not wired | enable `respect_skip=True` (default in pipeline_v2) |

Full Farey-side recovery docs:
- `/Users/saar/Desktop/Farey-Local/experiments/EXO_DISTRIBUTED_WORKING.md`
- `/Users/saar/Desktop/Farey-Local/experiments/EXO_P2P_STATUS.md`
- `/Users/saar/Desktop/Farey-Local/experiments/EXO_INFERENCE_WORKING.md`
- `~/bin/exo_cluster_restart.sh`

---

## 11. Cross-project pointer — Farey research (SEPARATE PROJECT)

Farey research = different project. If user mentions **Koyama correspondence, Farey discrepancy, Mertens spectroscope, zeta zeros, Chowla, NDC (chi, rho) pairs, Lean 4 formalization, Aristotle API** — that's Farey, NOT Token Economy. Do not cross-pollinate:

| Farey resource | path |
|---|---|
| vault | `/Users/saar/Desktop/Farey-Local/` + Obsidian "Spark Obsidian Beast" other folders |
| compute docs | `/Users/saar/Desktop/Farey-Local/model_context/COMPUTE_MANAGEMENT.md` |
| model routing | `/Users/saar/Desktop/Farey-Local/model_context/MODEL_ROUTING.md` |
| remote prompt | `/Users/saar/Desktop/Farey-Local/model_context/REMOTE_SYSTEM_PROMPT.txt` |
| queues | `~/Desktop/Farey-Local/M1MAX_QUEUE.txt`, `~/Desktop/Farey-Local/M5MAX_QUEUE.txt` |
| results | `~/Desktop/Farey-Local/experiments/` |
| NDC canonical pairs (ANTI-FABRICATION) | in REMOTE_SYSTEM_PROMPT.txt — use EXACT definitions, never guess |

Author attribution rule (STM 2025): AI NOT listed as author. Author = Saar Shai. AI in disclosure.

---

## 12. Start here (next agent — pick one)

If user is vague on next step, prioritize:

1. **EXO stability fix** — highest leverage blocker. Try launch-arg `--advertise-addr 192.168.1.218` (M1) / `192.168.1.64` (M1B). If that doesn't exist, `sudo route add -net 169.254/16 -interface lo0` on both nodes. Verify with two 500+ token consecutive generations (no mid-gen drop).
2. **Run adversarial sweep on Kaggle** — `kaggle-feeder` agent + queue has tasks ready.
3. **Benchmark TurboQuant on M2** — need a GGUF path. `qwen3.6:latest` lives in Ollama blob; see wiki §Ollama GGUF reuse for symlink recipe.
4. **Smoke-test agents-triage on real traffic** — have user issue a mix of prompts ("add note to wiki X", "research Y", "fix typo in Z") and verify routing decisions. classify.py tests covered in prior session.

---

## 13. Paths quick-reference

```
Repo root:            /Users/saar/Documents/Spark Obsidian Beast/Token Economy/
GitHub:               https://github.com/SaarShai/token-economy
Stable bundle:        <repo>/stable/
MCP code:             <repo>/projects/{compound-compression-pipeline,semdiff}/*_mcp/server.py
Wiki index:           <repo>/index.md
Roadmap:              <repo>/ROADMAP.md
Log:                  <repo>/log.md
Devices inventory:    <repo>/concepts/devices-inventory.md
Raw research:         <repo>/raw/*.md (date-prefixed)
Kaggle results:       <repo>/projects/compound-compression-pipeline/kaggle_results/v{4,7,8}-*.jsonl
Subagent defs (src):  <repo>/projects/agents-triage/agents/*.md
Subagent defs (cc):   ~/.claude/agents/*.md
Skill defs:           ~/.claude/skills/{context-keeper,agents-triage}/SKILL.md
Hooks config:         ~/.claude/settings.json
CC MCP config:        ~/.claude.json
Kaggle CLI:           ~/.local/bin/kaggle (also ~/Library/Python/*/bin/kaggle)
TurboQuant binary:    ~/src/llama-cpp-turboquant/build/bin/llama-server
TurboQuant wrapper:   ~/bin/llama-tq
SSH key:              ~/.ssh/id_ed25519
EXO daemon path:      /Applications/EXO.app/Contents/Resources/exo/exo (M1, M1B)
```

---

## 14. Recent log (auto-chronological — read bottom-up for latest)

See [[log.md]]. Last entries include: Qwen3.6-35B download complete both nodes, EXO cluster restarts + `events.bin` clear discovery, context-keeper hook activation, stable bundle cut, 20+ adversarial categories committed, TurboQuant concept doc shipped.

---

**End of HANDOFF.** For any ambiguity, check [[index]] first, then [[ROADMAP]], then the specific project README. If user-asked question doesn't map to any of the above, it's probably Farey — check §11.
