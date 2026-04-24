from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from token_economy.cli import main
from token_economy.context import checkpoint
from token_economy.delegate import classify
from token_economy.tokens import estimate_tokens
from token_economy.wiki import WikiStore


REPO = Path(__file__).resolve().parents[1]


class UniversalFrameworkTests(unittest.TestCase):
    def test_start_and_adapters_stay_lean(self):
        start = (REPO / "start.md").read_text(encoding="utf-8")
        self.assertLessEqual(estimate_tokens(start), 1500)
        for adapter in [
            REPO / "adapters/claude/CLAUDE.md",
            REPO / "adapters/codex/AGENTS.md",
            REPO / "adapters/gemini/GEMINI.md",
            REPO / "adapters/cursor/token-economy.mdc",
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
        route = classify("summarize this Obsidian wiki note and document the result")
        self.assertEqual(route.tier, "simple")
        self.assertEqual(route.model_class, "cheap")
        self.assertEqual(route.worker, "wiki-worker")

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


if __name__ == "__main__":
    unittest.main()

