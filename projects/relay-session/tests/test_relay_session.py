import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from relay_session.cli import main
from relay_session.core import ask_old_plan, checkpoint, lint_handoff, relay_session_name


class RelaySessionTests(unittest.TestCase):
    def test_checkpoint_lints_and_preserves_old_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "start.md").write_text("# start\n", encoding="utf-8")
            transcript = root / "session.jsonl"
            transcript.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Fix relay handoff summaries."}]}}),
                        json.dumps({"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Changed files:\n- projects/relay-session/relay_session/core.py\n- projects/relay-session/tests/test_relay_session.py\n\nVerification:\n- python3 -m pytest projects/relay-session/tests/test_relay_session.py -q -> 3 passed\n\nConfirmed: handoffs should prefer fact bullets over transcript snippets.\nBackend listed is not the same as Desktop UI visible."}]}}),
                        *[f"command: noisy-{idx} /tmp/file-{idx}.py" for idx in range(100)],
                    ]
                ),
                encoding="utf-8",
            )
            old_thread = os.environ.get("CODEX_THREAD_ID")
            os.environ["CODEX_THREAD_ID"] = "thread-xyz"
            try:
                packet = checkpoint(root, "relay test", plan="continue", transcript=transcript)
            finally:
                if old_thread is None:
                    os.environ.pop("CODEX_THREAD_ID", None)
                else:
                    os.environ["CODEX_THREAD_ID"] = old_thread
            handoff = Path(packet["path"])
            self.assertTrue(lint_handoff(handoff)["ok"])
            text = handoff.read_text(encoding="utf-8")
            self.assertIn("old-thread-id: thread-xyz", text)
            self.assertIn("## 2. Context packet", text)
            self.assertIn("### Proven facts", text)
            self.assertIn("### Current git state", text)
            self.assertIn("## 9. Instructions for next agent", text)
            self.assertIn("Layer 1: read `start.md` plus this handoff only", text)
            self.assertIn("Layer 4: if the old session identifies an even older relay handoff", text)
            self.assertIn("even older relay handoff", text)
            self.assertIn("Omit `--execute` to dry-run", text)
            self.assertIn("Narrow repo retrieval means targeted", text)
            self.assertNotIn("User asked:", text)
            self.assertNotIn("Assistant reported:", text)
            self.assertIn("projects/relay-session/relay_session/core.py", text)
            self.assertIn("3 passed", text)
            self.assertIn("handoffs should prefer fact bullets", text)
            self.assertIn("Backend listed is not the same as Desktop UI visible", text)
            self.assertNotIn("## 6. Key decisions\n- none captured", text)
            self.assertNotIn("Handoff generated as a lean continuation packet", text)
            self.assertFalse(lint_handoff(handoff)["warnings"])

    def test_checkpoint_preserves_relay_visibility_conclusion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            transcript = root / "visibility.jsonl"
            transcript.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Relay 24 is not visible. Figure out the boundary."}]}}),
                        json.dumps(
                            {
                                "type": "response_item",
                                "payload": {
                                    "type": "message",
                                    "role": "assistant",
                                    "content": [
                                        {
                                            "type": "output_text",
                                            "text": "\n".join(
                                                [
                                                    "Conclusion:",
                                                    "- Launcher/backend relay creation works, but Codex Desktop sidebar visibility can lag or be affected by generated handoff/session content.",
                                                    "- Regression boundary: a1e4514 made Relay[24] not appear; revert commit 7b81e50 restored visible Relay[25].",
                                                    "",
                                                    "Decisions:",
                                                    "- Do not touch projects/relay-session/relay_session/cli.py.",
                                                    "- Do not touch projects/relay-session/relay_session/codex_app.py.",
                                                    "",
                                                    "Verification:",
                                                    "- Relay[25] appeared in the UI after revert.",
                                                    "- lint ok: true",
                                                ]
                                            ),
                                        }
                                    ],
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )
            packet = checkpoint(root, "verify relay visibility handoff", plan="stop and evaluate", transcript=transcript)
            text = Path(packet["path"]).read_text(encoding="utf-8")
            self.assertIn("Launcher/backend relay creation works", text)
            self.assertIn("a1e4514 made Relay[24] not appear", text)
            self.assertIn("7b81e50 restored visible Relay[25]", text)
            self.assertIn("Do not touch projects/relay-session/relay_session/cli.py", text)
            self.assertIn("Relay[25] appeared in the UI after revert", text)
            self.assertTrue(lint_handoff(Path(packet["path"]))["ok"])

    def test_checkpoint_keeps_long_noisy_handoff_under_budget(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            transcript = root / "long.jsonl"
            noisy_lines = [f"- fixed noisy detail {idx} with some repeated extra words for trimming" for idx in range(80)]
            transcript.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Conclusion:\n" + "\n".join(noisy_lines) + "\n\nVerification:\n- focused tests -> 4 passed"}]}}),
                    ]
                ),
                encoding="utf-8",
            )
            packet = checkpoint(root, "long handoff", plan="continue", transcript=transcript, max_packet_tokens=2000)
            handoff = Path(packet["path"])
            lint = lint_handoff(handoff)
            self.assertLessEqual(lint["tokens"], 2000)
            self.assertTrue(lint["ok"], lint)

    def test_ask_old_plan_prefers_thread_then_transcript(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            thread_handoff = root / "thread.md"
            thread_handoff.write_text("---\nold-thread-id: thread-abc\nold-transcript: none\n---\n", encoding="utf-8")
            self.assertEqual(ask_old_plan(root, thread_handoff, "question")["mode"], "codex-old-thread")

            transcript = root / "old.jsonl"
            transcript.write_text("secret relay sentinel BLUE-17\n", encoding="utf-8")
            transcript_handoff = root / "transcript.md"
            transcript_handoff.write_text(f"---\nold-thread-id: none\nold-transcript: {transcript}\n---\n", encoding="utf-8")
            answer = ask_old_plan(root, transcript_handoff, "relay sentinel")
            self.assertEqual(answer["mode"], "transcript")
            self.assertTrue(answer["ok"])

    def test_cli_checkpoint_and_name(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertEqual(relay_session_name("demo", "02"), "Relay[02]: demo")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main(["--repo", str(root), "checkpoint", "--goal", "demo"]), 0)
            result = json.loads(buf.getvalue())
            self.assertTrue(Path(result["path"]).exists())


if __name__ == "__main__":
    unittest.main()
