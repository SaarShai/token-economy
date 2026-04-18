# AGENT_PROMPT — copy-paste for any LLM agent

Paste the block below into **Claude Code / Cursor / Cline / Zed / Windsurf / Aider** (any agent with shell + file access). The agent will clone, install, verify, and report.

Two variants: MODE A (global install, one machine) and MODE B (project install, per-repo). Pick one.

---

## MODE A — global (recommended for personal machine)

```
You are installing the "Token Economy" stable toolset on this machine. Follow these steps exactly, report completion after each:

0. CONTEXT
   Token Economy provides 3 measured tools:
   - ComCom: prompt compression with self-verify escalation (~45% input-token cut at ~neutral quality, validated on SQuAD n=8 and CoQA n=50)
   - semdiff: AST-node file diff for re-reads (95.5% savings on 2575-line file after 2 method edits)
   - context-keeper: PreCompact hook extracting structured state to markdown
   Plus shared: skip_detector (pre-filter), rename_detect (semdiff), adversarial_bench (CI gate), cost_estimator.

1. CLONE
   cd ~/src && git clone https://github.com/SaarShai/token-economy && cd token-economy

2. READ
   Read stable/README.md for what's measured + known limits. Report back the "Known limitations" section in one line.

3. INSTALL
   bash stable/INSTALL.sh
   This runs `claude mcp add --scope user` for comcom + semdiff, installs pip deps (mcp, tiktoken, llmlingua, tree-sitter<0.22, tree-sitter-languages), symlinks context-keeper skill into ~/.claude/skills/.

4. HOOK
   Add this to ~/.claude/settings.json under hooks.PreCompact (chain if hook already exists):
   {"type":"command","command":"bash ~/.claude/skills/context-keeper/hook.sh"}

5. VERIFY
   claude mcp list
   Confirm both "comcom ✓ Connected" and "semdiff ✓ Connected" appear.

6. SMOKE TEST
   - ComCom: echo "Please kindly help me understand why this function is really slow" > /tmp/t.txt && python3 ~/src/token-economy/projects/compound-compression-pipeline/pipeline.py /tmp/t.txt --show
   - semdiff: python3 -m semdiff.cli read ~/src/token-economy/projects/semdiff/semdiff/core.py --session test (requires sys.path includes projects/semdiff)

7. REPORT
   Report to user: (a) which tools installed, (b) MCP ✓ Connected count, (c) any pip install warnings, (d) next steps (restart Claude Code to load MCP tools).

DO NOT:
- Install anything marked as spec or WIP (context-keeper v2, skill-crystallizer, wiki-search).
- Edit files outside ~/.claude/settings.json and ~/.claude/skills/.
- Run adversarial_bench (requires Ollama running locally — optional).
```

---

## MODE B — project-scoped (per-repo, does NOT affect other CC sessions)

```
You are installing Token Economy stable toolset into THIS project only (not globally). Follow exactly:

0. CONTEXT (same as MODE A)

1. ADD AS SUBMODULE
   git submodule add https://github.com/SaarShai/token-economy tools/token-economy
   git submodule update --init

2. INSTALL (scope=project)
   bash tools/token-economy/stable/INSTALL.sh --project

3. HOOK (project file)
   Edit ./.claude/settings.json (create if absent). Add:
   {
     "hooks": {
       "PreCompact": [{
         "matcher": "*",
         "hooks": [{"type":"command","command":"bash ./.claude/skills/context-keeper/hook.sh"}]
       }]
     }
   }

4. COMMIT
   git add .gitmodules tools/token-economy .claude/ && git commit -m "add Token Economy stable toolset"

5. VERIFY
   From a CC session opened in THIS folder:
   claude mcp list
   Confirm comcom + semdiff present.

6. REPORT
   As MODE A step 7, plus: note that other CC sessions on this machine will NOT see these tools. Scope is project-only.

DO NOT:
- Install to ~/.claude/ — this is project-scoped.
- Commit API keys or local secrets.
```

---

## Troubleshooting prompt (if MCP fails to connect)

```
If `claude mcp list` shows `comcom ✗` or `semdiff ✗`:
1. Check the server runs manually:
   /opt/homebrew/bin/python3.11 <repo>/projects/<tool>/*_mcp/server.py
   Type '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' + Enter. Must respond with result.
2. If "ModuleNotFoundError: mcp" — Python wrong; use python3.10+ explicitly.
3. If "ModuleNotFoundError: tree_sitter_languages" — pip pin wrong: pip install 'tree-sitter<0.22' tree-sitter-languages --force-reinstall
4. Report exact error to user. Do not silently retry.
```

---

## Expected result (paste to user)

After install completes:
- `comcom` MCP exposes `comcom_compress`, `comcom_skip_check`, `comcom_verify`, `comcom_estimate_cost`
- `semdiff` MCP exposes `read_file_smart`, `snapshot_clear`, `snapshot_status`
- `context-keeper` hook fires on next `/compact`, writes to ~/.claude/memory/sessions/
- `$ comcom_estimate_cost` from shell: project $ saved for your usage pattern

Measured claim: 44.9%-57.3% input-token savings on QA workloads, quality effectively preserved (CI touches zero on Δscore). Regression detection via `scripts/adversarial_bench.py`.

Honest limits: small eval N, dense-numeric content still takes quality hit despite skip_detector. Run bench before trusting.

Repo: https://github.com/SaarShai/token-economy
