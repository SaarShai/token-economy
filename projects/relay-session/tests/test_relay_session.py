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
                        json.dumps({"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Changed files:\n- projects/relay-session/relay_session/core.py\n- projects/relay-session/tests/test_relay_session.py\n\nVerification:\n- python3 -m pytest projects/relay-session/tests/test_relay_session.py -q -> 3 passed"}]}}),
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
            self.assertIn("## 9. Instructions for next agent", text)
            self.assertIn("User asked: Fix relay handoff summaries", text)
            self.assertIn("projects/relay-session/relay_session/core.py", text)
            self.assertIn("3 passed", text)
            self.assertIn("## 6. Key decisions\n- none captured", text)
            self.assertNotIn("Handoff generated as a lean continuation packet", text)

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
