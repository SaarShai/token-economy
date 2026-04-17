"""CoQA adapter. Multi-turn QA — each turn's context = story + prior Q/A chain.
This makes CoQA ideal for testing:
  - ComCom on growing contexts
  - context-keeper (compaction of Q/A history)
"""
import json
from pathlib import Path


def load(path, n=None, min_turn=2, max_turn=8):
    """Yield eval-items. For each conversation, emit items for turns [min_turn..max_turn].

    Each item's context = story + all prior Q/A pairs (growing as turn increases).
    """
    data = json.loads(Path(path).read_text())
    items = []
    for conv in data.get("data", []):
        story = conv["story"]
        qs = conv["questions"]
        ans = conv["answers"]
        cid = conv["id"]
        for i, (q, a) in enumerate(zip(qs, ans)):
            if i + 1 < min_turn or i + 1 > max_turn: continue
            prior = "\n".join(
                f"Q{j+1}: {qs[j]['input_text']}\nA{j+1}: {ans[j]['input_text']}"
                for j in range(i)
            )
            ctx = f"STORY:\n{story}\n\nPRIOR:\n{prior}" if prior else f"STORY:\n{story}"
            items.append({
                "id": f"{cid}-t{i+1}",
                "context": ctx,
                "question": q["input_text"],
                "answer": a["input_text"],
                "type": "multiturn_qa",
                "meta": {"turn": i + 1, "conv_id": cid},
            })
            if n and len(items) >= n:
                return items
    return items
