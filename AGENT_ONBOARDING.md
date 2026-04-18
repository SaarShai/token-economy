# AGENT_ONBOARDING — how any agent can adopt this toolset

Point any LLM agent (Claude Code, Cursor, Cline, Zed, Windsurf, Aider) at this file. It will: (a) understand what each tool does, (b) install what applies to its client, (c) activate hooks/MCP servers, (d) start benefitting.

## One-paragraph pitch

Token Economy is a suite of 7 independent tools that reduce LLM token consumption, improve reliability, and build compound benefit over a project's lifetime. Each tool targets one of seven **optimization axes**. Install whichever apply; all work standalone.

## Step 0 — read this first

```bash
git clone https://github.com/SaarShai/token-economy
cd token-economy
```

Read [concepts/optimization-axes.md](concepts/optimization-axes.md) for the taxonomy. Then come back here.

---

## Step 1 — detect your client

| If you're running inside | install these | skip these |
|---|---|---|
| Claude Code | all (MCP + hooks + skills) | — |
| Cursor / Cline / Zed / Windsurf / any MCP client | MCP servers only | hooks, skills |
| Aider | CLI tools + wrappers | hooks, skills, MCP (until Aider supports) |
| Generic Python script | CLI + library imports | all agent-specific |

---

## Step 2 — install by axis

### Axis A: input compression (ComCom)
**What it saves:** ~45% of input tokens on verbose contexts, quality preserved with self-verify escalation.

- **MCP server (universal):**
  ```bash
  pip install mcp tiktoken llmlingua
  # Claude Code:
  claude mcp add comcom -- python projects/compound-compression-pipeline/comcom_mcp/server.py
  # Cursor/Cline/Zed: add same command to their MCP config
  ```
- **Tools exposed:** `comcom_compress`, `comcom_skip_check`, `comcom_verify`, `comcom_estimate_cost`.
- **Verify backend:** auto-detects Ollama or Anthropic API (set `ANTHROPIC_API_KEY` for Claude).

Full docs: [projects/compound-compression-pipeline/INSTALL.md](projects/compound-compression-pipeline/INSTALL.md)

### Axis B: tool-output filtering (semdiff + omni)
**What it saves:** 95% on repeated file reads (semdiff). ~90% on terminal noise (omni).

- **semdiff MCP:**
  ```bash
  pip install mcp 'tree-sitter<0.22' tree-sitter-languages
  claude mcp add semdiff -- python projects/semdiff/semdiff_mcp/server.py
  ```
  Tools: `read_file_smart`, `snapshot_clear`, `snapshot_status`. Supports Python/JS/TS/Rust.

- **omni (external, Rust, MIT):**
  ```bash
  brew install fajarhide/tap/omni
  omni init --all   # wires hooks + MCP automatically
  ```

Full docs: [projects/semdiff/INSTALL.md](projects/semdiff/INSTALL.md)

### Axis C: cross-session memory (context-keeper v1 + v2)
**What it saves:** facts across `/compact` events; prevents repeated mistakes.

- **v1 (intra-session PreCompact hook, Claude Code only):**
  ```json
  // ~/.claude/settings.json
  "PreCompact": [{
    "matcher": "*",
    "hooks": [{"type":"command","command":"bash ~/.claude/skills/context-keeper/hook.sh"}]
  }]
  ```
  Symlink skill dir:
  ```bash
  ln -sf "$(pwd)/projects/context-keeper" ~/.claude/skills/context-keeper
  ```

- **v2 (L0-L4 tiered cross-session memory):** skeleton at [projects/context-keeper-v2/](projects/context-keeper-v2/). Not yet installable — in development.

### Axis D: verification / quality
**What it ensures:** reliability under compression; avoid destructive compressions.

- Already bundled with ComCom (`comcom_skip_check`, `comcom_verify`).
- Code: `skip_detector.py`, `verify.py`, `verify_anthropic.py`, `rename_detect.py` (semdiff).

### Axis E: knowledge organization (wiki)
**What it gives:** persistent structured knowledge; fast lookup; productivity.

- Clone this repo into your Obsidian vault (or anywhere):
  ```bash
  git clone https://github.com/SaarShai/token-economy ~/my-vault/token-economy
  ```
- Read [schema.md](schema.md) for the frontmatter conventions (`type`, `axis`, `confidence`, `tags`).
- Copy [index.md](index.md) + [ROADMAP.md](ROADMAP.md) + [log.md](log.md) as templates.
- Optional: install [projects/wiki-search/](projects/wiki-search/) MCP for progressive-disclosure retrieval (skeleton, in development).

### Axis F: measurement / trust
**What it ensures:** claims backed by numbers, not vibes.

- Bench registry + adapters at [bench/](bench/).
- Evaluations at `projects/compound-compression-pipeline/eval_v{1,2,3,4}.py`.
- Kaggle Notebook template at [bench/notebooks/kaggle_eval_template.md](bench/notebooks/kaggle_eval_template.md) (free T4 GPU).

### Axis G: skill crystallization
**What it saves:** re-solving the same problem.

- Skeleton at [projects/skill-crystallizer/](projects/skill-crystallizer/). Not yet installable.
- Pattern: on task completion, detector extracts tool sequence → LLM writes L3 SOP → next similar task reuses.

---

## Step 3 — verify install

After install, in Claude Code:
```
/mcp
```
You should see: `semdiff ✓`, `comcom ✓` (if installed), `omni ✓` (if installed).

Test each:
```bash
# ComCom: compress a file
echo "long verbose text here" > /tmp/t.txt
python projects/compound-compression-pipeline/pipeline.py /tmp/t.txt --show

# semdiff: read a file twice
python -m semdiff.cli read /path/to/code.py --session test
# edit the file
python -m semdiff.cli read /path/to/code.py --session test  # diff view

# context-keeper: trigger manually
bash ~/.claude/skills/context-keeper/hook.sh < <(echo '{"transcript_path":"...","session_id":"..."}')
```

---

## Step 4 — measure your own benefit

```bash
# Estimate $ saved over N calls
python projects/compound-compression-pipeline/scripts/cost_estimator.py \
  --n_calls 1000 --avg_in 4000 --avg_out 200 \
  --model claude-sonnet-4 --savings_rate 0.45 --verify_overhead 50
```

Expected output for heavy Claude Sonnet usage: **$5.40 saved per 1000 calls** at 4K avg input tokens, with quality effectively preserved.

---

## Step 5 — contribute back

If your agent session produces:
- New adapter for a benchmark dataset → `bench/adapters/<name>.py`
- New eval result → commit to `projects/compound-compression-pipeline/kaggle_results/`
- Design insight → `concepts/<slug>.md` with frontmatter
- Failed experiment → `raw/YYYY-MM-DD-<slug>.md` (negative results matter)

PR against https://github.com/SaarShai/token-economy.

---

## Quick reference: which tool for which pain

| your pain | tool |
|---|---|
| Context window filling up | ComCom + context-keeper |
| Re-reading the same file costs tokens | semdiff |
| Terminal commands flood the context | omni |
| Agent keeps making the same mistake | context-keeper + skill-crystallizer (WIP) |
| Don't know how much I'm actually saving | cost_estimator + bench |
| Wiki is huge, loading it blows context | wiki-search (WIP) |
| Model hallucinates on compressed context | verify + skip_detector |

---

## Status snapshot (2026-04)

| tool | axis | status | measured |
|---|---|---|---|
| ComCom | A | shipped + MCP | 44.9% savings, Δq −0.12 CI[−0.38,0.00] (SQuAD n=8) |
| semdiff | B | shipped + MCP | 95.5% re-read savings (argparse.py) |
| omni | B | installed, external | 90% stdout claim (not our measurement) |
| context-keeper v1 | C | shipped, hook active | 68 files / 21 cmds / 21 errs from 100-turn session |
| context-keeper v2 | C | spec | — |
| skill-crystallizer | G | spec | — |
| wiki-search | E | spec | — |
| write-gate | D | lib | — |
| bench | F | wired, Kaggle kernel running | 7 datasets, 2 downloaded |

---

## Anti-patterns (what NOT to do)

- **Don't install everything if you don't need it.** Each tool is standalone. Pick by axis.
- **Don't use ComCom on code blocks / dense numeric tables.** Run `comcom_skip_check` first.
- **Don't activate context-keeper without a PreCompact hook.** It only runs on compaction.
- **Don't skip verification.** Compression without verify → subtle quality decay you won't notice.
- **Don't trust a single eval.** Our ComCom 44.9% is n=8 SQuAD. Run it on your workload before believing it.
