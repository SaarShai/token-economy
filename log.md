# Log

## [2026-04-24] ship | universal agent framework v1

Added `start.md`, `token-economy.yaml`, the `te` CLI, lean agent adapters, L0/L1 memory files, wiki-search v1, context-refresh, delegate-router, and context-keeper v2 retrieval tools. Verified with `bash scripts/run_all_tests.sh`.

## [2026-04-24] ship | agent-ignition supplement

Added wiki schema v2 templates, model-agnostic skills/prompts, context meter + handoff lint, stricter delegation contracts, hooks/configs/extensions, install dry-run, profile support, framework smoke bench, and CI gate. Verified with `bash scripts/run_all_tests.sh`, `te wiki lint --strict --fail-on-error`, `te bench run --suite framework-smoke`, JSON config validation, and Python compile.

## [2026-04-24] ship | personal-assistant routing

Added `/pa` and `/btw` prompt bypass via `te pa`, hook routing, a personal-assistant skill, and router prompt. Purpose: route context-light prompts through a lightweight classifier/dispatcher with minimal context, escalating only when risk or complexity requires the main model.

## [2026-04-24] harden | repo-local startup review

Reviewed the framework, repo docs, and setup prompt for duplicated startup glue, stale global setup language, noisy hooks, and routing/context-meter gaps. Updated `HANDOFF.md`, startup docs, `L0_rules.md`, wiki schema defaults, docs audit scope, context meter model sizing, adapter overwrite detection, and prompt hook behavior. Verified with `bash scripts/run_all_tests.sh`, `./INSTALL.sh --dry-run`, `./te wiki lint --strict --fail-on-error`, `./te doctor`, `./te hooks doctor`, `./te bench run --suite framework-smoke`, Python compile, `git diff --check`, active-doc global-term scan, and token-budget checks.

## [2026-04-24] harden | fresh folder setup

Updated the setup prompt and onboarding docs to keep first-run setup simple: if the target folder lacks `token-economy.yaml`, the prompt explicitly permits clearing that current folder only, including hidden files and `.git`, then cloning the canonical repo fresh. Purpose: avoid false stops in non-empty setup folders while still forbidding deletion outside the target folder.

## [2026-04-24] feature | repo-maintainer worker

Added a lightweight repo-maintainer subagent prompt and routing policy for task workspaces with GitHub remotes. It runs only at verified save-points, before context refresh/handoff, or on explicit save/commit/push requests; it stages only intended task changes and skips entirely when no GitHub remote exists.

## [2026-04-24] feature | summ context refresh

Added the `summ` manual refresh prompt, a lightweight wiki-documenter subagent prompt, and stricter context-refresh rules. Fresh sessions now load only the lean handoff plus `start.md`; durable but non-immediate memory is routed to repo-local wiki documentation instead of being carried into fresh context.

## [2026-04-24] harden | terminal summ behavior

Updated `summ` so appended instructions become next-session requirements, generic checkpoints must be replaced with session-specific handoffs, missing documenter prompts use an inline fallback instead of broad searching, and old-context work stops after emitting the packet.

## [2026-04-24] feature | host context controls

Added host-native context control guidance for `summ`: Claude Code `/clear` and `/compact`, Codex `/new`, `/clear`, and `/compact`, Gemini `/compress`, and generic fallback to a fresh session. Added `./te context host-controls` so agents can retrieve the right command without loading broad docs.

## [2026-04-24] feature | subagent lifecycle cleanup

Added a lifecycle prompt for closing completed or idle subagents only after their result packet has been read, useful output has been merged or documented, and follow-up risks have been captured. This prevents thread-limit stalls without losing worker results.

## [2026-04-24] harden | summ host-boundary tests

Clarified that `summ` cannot assume the model can execute host slash commands from its own response. Added `prompts/summ-experiments.md` for measuring whether a host actually dropped context, and updated host-control guidance to require user/host execution unless a real tool exists.

## [2026-04-24] feature | fresh successor workaround

Added `./te context fresh-command` and documented the best non-slash workaround: start a fresh successor host process/session with only `start.md` and the handoff file. This bypasses a full old transcript even when the current host cannot be cleared programmatically.

## [2026-04-24] feature | Codex App Server fresh thread

Added `./te context codex-fresh-thread` as the verified Codex successor path. It uses Codex App Server `thread/start` + `turn/start` with an explicit accessible model, creates an ephemeral thread with `turns: []`, and loads only `start.md` plus the handoff. Live smoke passed with `gpt-5.3-codex-spark`; this bypasses rather than erases the old host transcript.

## [2026-04-24] verify | controlled summ fresh-thread result

Verified controlled `summ` successor run: `./te context codex-fresh-thread --handoff .token-economy/checkpoints/20260424-135455-fresh-session.md --model gpt-5.3-codex-spark --execute` returned `ok=true`, `thread_id=019dbfc5-edbe-7632-9a51-0dda81340fb0`, `assistant_responded=true`, and `thread_idle=true`. Events showed `thread/started` with `ephemeral=true` and `turns=[]`; successor read `start.md` plus the handoff only, while the old visible host transcript was not erased. Token usage still showed large Codex host/system overhead, about 53k input tokens, despite no old transcript in the successor-visible prompt. See [[prompts/summ-experiments]].

## 2026-04-17

Terminology: **ComCom** = our compound-compression project (disambiguate from Claude Code's "CC").
- Wiki created. Folder: repo-local `Token Economy/` markdown wiki.
- Ingested research brief → `raw/2026-04-17-research-brief.md`.
- Setup confirmed: caveman plugin active, superpowers skill loaded, wiki initialized.
- Next: flesh out concept pages, pick first project (likely compound-compression-pipeline or wiki-query-shortcircuit).
- Built [[projects/compound-compression-pipeline]] (aka **ComCom**). Measured 70-73% on prose, 59% on mixed technical at gentler rate. Code/paths/URLs preserved via placeholder protection.
- Ingested [[raw/2026-04-17-semantic-diff-survey]]. Novelty 4/5. Created [[concepts/semantic-diff-edits]]. Added [[ROADMAP]] as live tracker.
- Ran quality eval on Ollama (phi4:14b, 3 tasks). Result: 55.7% token savings @ 100% quality retention at rate=0.5. Placeholder format fixed (`XPROTECT{n}XEND` survives BERT tokenization). Compressed prompts also faster (1.4s vs 9.8s observed).
- Built eval-v2: SQuAD v2 + gemma4:31b judge + bootstrap CIs + failure-mode classification. Running in background.
- Built [[projects/semdiff]] (AST-node diff). Measured 95.5% savings after 2 method edits on argparse.py (2575 lines, 19,280 → 859 tokens); 99.5% on stable re-read. Tree-sitter for py/js/ts/rust.
- Kaggle auth set up (user: saarshai).
- Built [[projects/context-keeper]]. Skill + PreCompact hook. Regex extractor + optional local-LLM pass. Current framework writes memory under repo-local `.token-economy/` paths.
- **Eval-v2 completed** (SQuAD v2, n=8, 2 runs, phi4:14b + qwen3:8b judge). Token savings **44.5% CI [41.5-47.4]**. Δscore **−0.25 CI [−0.62, 0.00]**. Failure modes on comp: 8 NONE, 6 MISSING, 2 SWAP. **v1's "55.7% @ 100%" overstated**; principled measurement shows small, non-significant quality hit. N too small to resolve CI. Judge swap (gemma4:31b → qwen3:8b) fixed 129s latency thrash.
- Built ComCom v2 (pipeline_v2.py) with question-aware + critical-zone protection; eval-v3 in progress (4 conditions: full, v1, v2, adaptive-escalation). Early data shows v2 over-compresses (critical-protect + rate=0.5 on remainder = total too low). Fix planned: scale rate by (1 - protected_fraction).
- **semdiff MCP server built**. Python 3.11 + mcp SDK. 3 tools exposed (read_file_smart, snapshot_clear, snapshot_status). Protocol roundtrip tested (initialize, tools/list, tools/call all pass). CC plugin wrapper at `plugin/.mcp.json`. Install docs at [[projects/semdiff/INSTALL]].
- **bench/ built**. Kaggle API wired via registry.yaml. 7 datasets registered (2 downloaded so far). Adapters emit uniform {id, context, question, answer, type, meta} schema. CoQA multi-turn items designed for growing-context stress. Kaggle Notebook template drafted for free-T4-GPU evals (30h/wk, 10× local throughput). See [[bench/README]].
- **Eval-v3 complete (ComCom upgrade)**. D_adaptive (self-verify escalation) delivers 44.9% savings at Δscore −0.12 [−0.38, 0.00] — quality effectively preserved. Zero REFUSE failures. C_v2 (question-aware + critical-zone) confirmed broken by over-compression; fix deprioritized since D_adaptive bypasses the issue. Shipped config: `pipeline_v2.compress` + `verify.escalate_gen`.

## [2026-04-20] download-status | Qwen3.6-35B-A3B-5bit | M1=complete, M1B=in-progress (authenticated curl running, ETA ~12h)
## [2026-04-20 22:36 BST] download-complete | Qwen3.6-35B-A3B-5bit | M1B all 5 shards verified (24.73 GB) via LAN HTTP server; shard1 required fresh download after dual-curl corruption; see /tmp/resume_qwen36_report.md
## [2026-04-20] download-finish | Qwen3.6-35B-A3B-5bit | M1=complete, M1B=complete (LAN transfer from M1:8888, all 5 shards verified, ~23GB, completed ~14:36 PDT)
## [2026-04-21] download-finish | Qwen3.6-35B-A3B-5bit | M1=complete, M1B=complete
