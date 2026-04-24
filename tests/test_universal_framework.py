from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from token_economy.cli import main
from token_economy.config import detect_agent
from token_economy.codex_app_server import codex_fresh_thread_plan, default_codex_fresh_model
from token_economy.context import checkpoint, fresh_launch_commands, host_context_controls, lint_handoff, meter
from token_economy.docs import audit as docs_audit
from token_economy.delegate import classify, personal_assistant_packet, strip_pa_prefix
from token_economy.tokens import estimate_tokens
from token_economy.wiki import WikiStore


REPO = Path(__file__).resolve().parents[1]


class UniversalFrameworkTests(unittest.TestCase):
    def test_active_docs_do_not_reintroduce_global_or_app_setup(self):
        active_paths = [
            REPO / "AGENT_ONBOARDING.md",
            REPO / "INSTALL.md",
            REPO / "README.md",
            REPO / "start.md",
            REPO / "HANDOFF.md",
            REPO / "ROADMAP.md",
            REPO / "L0_rules.md",
            REPO / "stable/AGENT_PROMPT.md",
            REPO / "stable/INSTALL.sh",
            REPO / "stable/README.md",
            REPO / "schema.md",
            REPO / "token_economy/wiki.py",
            REPO / "token_economy/delegate.py",
            REPO / "projects/wiki-search/README.md",
            REPO / "projects/agents-triage/SKILL.md",
            REPO / "projects/agents-triage/install.sh",
            REPO / "projects/agents-triage/classify.py",
            REPO / "projects/agents-triage/agents/wiki-note.md",
        ]
        forbidden = ("obsidian", "vault", "~/.claude", "--scope user", "scope user")
        for path in active_paths:
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            for needle in forbidden:
                self.assertNotIn(needle, text, f"{needle!r} found in {path.relative_to(REPO)}")

    def test_setup_prompt_allows_fresh_folder_clear_only(self):
        text = (REPO / "stable/AGENT_PROMPT.md").read_text(encoding="utf-8")
        self.assertIn("explicit permission to clear the current folder", text)
        self.assertIn("find . -mindepth 1 -maxdepth 1 -exec rm -rf {} +", text)
        self.assertIn("git clone https://github.com/SaarShai/token-economy.git .", text)
        self.assertIn("Do not delete anything outside the current folder", text)
        self.assertNotIn("git restore --source origin/main", text)
        self.assertNotIn("git reset --hard", text)

    def test_start_and_adapters_stay_lean(self):
        start = (REPO / "start.md").read_text(encoding="utf-8")
        self.assertLessEqual(estimate_tokens(start), 1500)
        for adapter in [
            REPO / "adapters/claude/CLAUDE.md",
            REPO / "adapters/codex/AGENTS.md",
            REPO / "adapters/gemini/GEMINI.md",
            REPO / "adapters/cursor/token-economy.mdc",
            REPO / "CLAUDE.md",
            REPO / "AGENTS.md",
            REPO / "GEMINI.md",
            REPO / ".cursor/rules/token-economy.mdc",
        ]:
            combined = start + "\n" + adapter.read_text(encoding="utf-8")
            self.assertLessEqual(estimate_tokens(combined), 2500)

    def test_wiki_progressive_retrieval(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wiki = WikiStore(root)
            wiki.init()
            note = root / "concepts" / "context-refresh.md"
            note.write_text(
                """---
type: concept
axis: cross_session_memory
tags: [context-refresh]
confidence: high
evidence_count: 1
---

# Context Refresh

Use fresh session packets at 20 percent context to avoid context rot. Links to [[patterns/progressive-retrieval]].
""",
                encoding="utf-8",
            )
            linked = root / "patterns" / "progressive-retrieval.md"
            linked.write_text(
                """---
type: pattern
axis: knowledge_org
tags: [retrieval]
confidence: med
evidence_count: 1
---

# Progressive Retrieval

Search first, timeline second, fetch last.
""",
                encoding="utf-8",
            )
            result = wiki.index()
            self.assertGreaterEqual(result["indexed"], 2)
            hits = wiki.search("context refresh")
            self.assertTrue(hits)
            self.assertEqual(hits[0]["id"], "concepts/context-refresh")
            timeline = wiki.timeline("patterns/progressive-retrieval")
            self.assertTrue(timeline["backlinks"])
            fetched = wiki.fetch("concepts/context-refresh")
            self.assertIn("20 percent context", fetched["content"])
            lint = wiki.lint()
            self.assertEqual(lint["broken_links"], [])

    def test_checkpoint_packet_is_small_and_plan_mode(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "L1_index.md").write_text("# L1\n\n- x -> `x.md`\n", encoding="utf-8")
            transcript = root / "transcript.txt"
            transcript.write_text(
                "command: pytest tests/test_x.py\nERROR failed assertion\nTouched /tmp/example.py\n",
                encoding="utf-8",
            )
            result = checkpoint(root, goal="finish framework", plan="verify tests", transcript=transcript)
            self.assertLessEqual(result["tokens"], 2000)
            self.assertIn("Start in plan mode", result["packet"])
            self.assertIn("pytest tests/test_x.py", result["packet"])

    def test_delegate_prefers_cheapest_capable_worker(self):
        route = classify("summarize this markdown wiki note and document the result")
        self.assertEqual(route.tier, "simple")
        self.assertEqual(route.model_class, "lightweight")
        self.assertEqual(route.worker, "wiki-worker")

        repo_route = classify("commit and push verified changes to the GitHub repo")
        self.assertEqual(repo_route.model_class, "lightweight")
        self.assertEqual(repo_route.worker, "repo-maintainer")

    def test_personal_assistant_prompt_bypass(self):
        invoked, clean = strip_pa_prefix("/pa summarize this wiki note")
        self.assertTrue(invoked)
        self.assertEqual(clean, "summarize this wiki note")
        self.assertEqual(strip_pa_prefix("/btw: extract file paths")[1], "extract file paths")

        packet = personal_assistant_packet("/pa summarize this wiki note")
        self.assertEqual(packet["mode"], "personal_assistant")
        self.assertTrue(packet["bypass_context"])
        self.assertEqual(packet["router"]["model_class"], "lightweight")
        self.assertEqual(packet["handler"]["model_class"], "lightweight")
        self.assertFalse(packet["context_bundle"]["include_full_transcript"])
        self.assertTrue(packet["context_bundle"]["include_l1_index"])
        self.assertIn("Do not answer", packet["main_model_instruction"])

    def test_cli_pa_and_hook_route(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(main(["pa", "/pa summarize this wiki note"]), 0)
        packet = json.loads(buf.getvalue())
        self.assertEqual(packet["mode"], "personal_assistant")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(main(["pa", "--directive", "/btw", "summarize", "this"]), 0)
        self.assertIn("[token-economy:/pa]", buf.getvalue())
        self.assertIn("Do not answer directly", buf.getvalue())

        proc = subprocess.run(
            ["bash", str(REPO / "hooks/user-prompt-submit.sh")],
            input=json.dumps({"prompt": "/pa summarize this"}),
            text=True,
            cwd=REPO,
            capture_output=True,
            check=True,
        )
        self.assertIn("[token-economy:/pa]", proc.stdout)

        quiet = subprocess.run(
            ["bash", str(REPO / "hooks/user-prompt-submit.sh")],
            input=json.dumps({"prompt": "normal prompt"}),
            text=True,
            cwd=REPO,
            capture_output=True,
            check=True,
        )
        self.assertEqual(quiet.stdout, "")

    def test_context_keeper_v2_memory_api(self):
        memory_dir = REPO / "projects" / "context-keeper-v2"
        sys.path.insert(0, str(memory_dir))
        try:
            from memory_api import ck_fetch, ck_query, ck_recent

            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / "L2_facts").mkdir()
                (root / "L3_sops").mkdir()
                (root / "L4_archive").mkdir()
                (root / "L1_index.md").write_text("- routing -> `L2_facts/routing.md`\n", encoding="utf-8")
                (root / "L2_facts" / "routing.md").write_text("cheap models first for routing\n", encoding="utf-8")
                (root / "L4_archive" / "session.md").write_text("archive\n", encoding="utf-8")
                self.assertTrue(ck_query("routing", root=root))
                fetched = ck_fetch("L2", "routing", root=root)
                self.assertIn("cheap models", fetched["content"])
                self.assertTrue(ck_recent(root=root))
        finally:
            sys.path.remove(str(memory_dir))

    def test_cli_wiki_init_and_delegate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main(["--repo", str(root), "wiki", "init"]), 0)
            self.assertIn("wiki_root", json.loads(buf.getvalue()))
            self.assertTrue((root / "schema.md").exists())

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main(["--repo", str(root), "delegate", "classify", "one-line typo fix"]), 0)
            route = json.loads(buf.getvalue())
            self.assertEqual(route["tier"], "simple")

    def test_wiki_new_v2_page_and_strict_lint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wiki = WikiStore(root)
            wiki.init()
            # Copy templates into temp wiki to emulate repo install.
            (root / "templates").mkdir(exist_ok=True)
            for name in ("page.template.md", "decision.template.md", "source-summary.template.md"):
                (root / "templates" / name).write_text((REPO / "templates" / name).read_text(encoding="utf-8"), encoding="utf-8")
            created = wiki.new_page("page", "Progressive Retrieval", "framework")
            self.assertTrue((root / created["created"]).exists())
            lint = wiki.lint_pages(strict=True)
            self.assertEqual(lint["errors"], [])

    def test_context_meter_env_threshold_and_handoff_lint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            transcript = root / "transcript.txt"
            transcript.write_text("x" * 200, encoding="utf-8")
            old_refresh = os.environ.get("REFRESH_AT_PCT")
            old_warn = os.environ.get("WARN_AT_PCT")
            old_max = os.environ.get("TOKEN_ECONOMY_CONTEXT_MAX")
            os.environ["REFRESH_AT_PCT"] = "20"
            os.environ["WARN_AT_PCT"] = "15"
            os.environ["TOKEN_ECONOMY_CONTEXT_MAX"] = "250"
            try:
                status = meter(transcript, model="test")
                self.assertEqual(status["action"], "refresh")
            finally:
                for key, value in (("REFRESH_AT_PCT", old_refresh), ("WARN_AT_PCT", old_warn), ("TOKEN_ECONOMY_CONTEXT_MAX", old_max)):
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
            packet = checkpoint(root, goal="meter test", plan="verify", transcript=transcript)
            self.assertTrue(lint_handoff(Path(packet["path"]))["ok"])
            try:
                os.environ["REFRESH_AT_PCT"] = "0.20"
                self.assertEqual(meter(transcript, model="test", max_tokens=250)["refresh_threshold"], 0.20)
            finally:
                if old_refresh is None:
                    os.environ.pop("REFRESH_AT_PCT", None)
                else:
                    os.environ["REFRESH_AT_PCT"] = old_refresh
            self.assertEqual(meter(model="gemini-flash")["max_tokens"], 1_000_000)
            self.assertEqual(meter(model="claude-sonnet")["max_tokens"], 200_000)

    def test_delegate_plan_contract(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(main(["delegate", "plan", "extract two symbols from code"]), 0)
        plan = json.loads(buf.getvalue())
        self.assertNotEqual(plan["chosen_tier"], "reasoning_top")
        self.assertIn("Orchestrator does not delegate final synthesis", plan["orchestrator_rule"])
        self.assertIn("sources", plan["result_contract"])

    def test_output_filter_preserves_errors(self):
        proc = subprocess.run(
            ["bash", str(REPO / "hooks/output-filter/filter.sh")],
            input="same\nsame\nERROR exact failure\nsame\n",
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("ERROR exact failure", proc.stdout)
        self.assertIn("deduped", proc.stdout)

    def test_install_dry_run_and_bench(self):
        subprocess.run(["bash", str(REPO / "INSTALL.sh"), "--dry-run"], cwd=REPO, check=True, capture_output=True, text=True)
        blocked = subprocess.run(["bash", str(REPO / "INSTALL.sh"), "--scope", "user", "--dry-run"], cwd=REPO, capture_output=True, text=True)
        self.assertNotEqual(blocked.returncode, 0)
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["start", "--scope", "user"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(main(["bench", "run", "--suite", "framework-smoke"]), 0)
        self.assertTrue(json.loads(buf.getvalue())["ok"])

    def test_docs_audit_targets_startup_surface_only(self):
        rows = docs_audit(REPO)
        paths = {row["path"] for row in rows}
        self.assertIn("start.md", paths)
        self.assertIn("L1_index.md", paths)
        self.assertNotIn("README.md", paths)
        self.assertTrue(all(row["recommendation"] == "startup-safe" for row in rows if row["status"] == "lean"))
        self.assertTrue((REPO / "prompts/subagents/repo-maintainer.prompt.md").exists())
        self.assertTrue((REPO / "prompts/subagents/lifecycle.prompt.md").exists())
        self.assertTrue((REPO / "prompts/summ.md").exists())
        self.assertTrue((REPO / "prompts/summ-experiments.md").exists())
        self.assertTrue((REPO / "prompts/subagents/wiki-documenter.prompt.md").exists())
        lifecycle = (REPO / "prompts/subagents/lifecycle.prompt.md").read_text(encoding="utf-8")
        self.assertIn("Close a subagent only", lifecycle)
        self.assertIn("result packet has been read", lifecycle)
        self.assertIn("wiki-documenter", (REPO / "skills/context-refresh/SKILL.md").read_text(encoding="utf-8"))
        summ = (REPO / "prompts/summ.md").read_text(encoding="utf-8")
        self.assertIn("what to paste", summ)
        self.assertIn("Do not load anything else", summ)
        self.assertIn("STOP HERE", summ)
        self.assertIn("next-session requirements", summ)
        self.assertIn("host-controls", summ)
        self.assertIn("Do not assume you can execute host slash commands", summ)
        self.assertIn("codex-fresh-thread", summ)
        self.assertEqual(host_context_controls("codex")["clear"], "/clear")
        self.assertEqual(host_context_controls("gemini")["compact"], "/compress")
        self.assertIn("completion_test", host_context_controls("codex"))
        self.assertIn("codex-fresh-thread", fresh_launch_commands("codex", REPO, REPO / "handoff.md")["preferred"])
        plan = codex_fresh_thread_plan(REPO, REPO / "handoff.md")
        self.assertEqual(plan["model"], default_codex_fresh_model())
        self.assertEqual(plan["persistence"], "persistent")
        self.assertIn("thread/started", " ".join(plan["success_test"]))
        self.assertIn("turns: []", " ".join(plan["success_test"]))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(main(["context", "host-controls", "--agent", "claude"]), 0)
        self.assertEqual(json.loads(buf.getvalue())["clear"], "/clear")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(main(["context", "fresh-command", "--agent", "codex", "--handoff", "handoff.md"]), 0)
        self.assertIn("fresh successor", json.loads(buf.getvalue())["note"])

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(main(["context", "codex-fresh-thread", "--handoff", "handoff.md", "--model", "gpt-5.3-codex-spark"]), 0)
        self.assertEqual(json.loads(buf.getvalue())["mode"], "app-server-fresh-thread")
        self.assertIn("thread_persistent", (REPO / "prompts/summ.md").read_text(encoding="utf-8"))

    def test_agent_detection_ignores_provider_api_keys(self):
        original = os.environ.copy()
        try:
            os.environ.clear()
            os.environ["ANTHROPIC_API_KEY"] = "secret"
            self.assertEqual(detect_agent(), "codex")
            os.environ["CLAUDE_CODE_SESSION"] = "1"
            self.assertEqual(detect_agent(), "claude")
        finally:
            os.environ.clear()
            os.environ.update(original)


if __name__ == "__main__":
    unittest.main()
