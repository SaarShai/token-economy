"""Code-refactoring 120K adapter. Before/after source pairs — semdiff fidelity eval.

Each item: context=before, answer=after. Question doesn't apply (not QA).
Use for: "given semdiff diff view of before→after, can LLM reconstruct the refactor?"
"""
import csv
from pathlib import Path


def load(path, n=None):
    f = Path(path)
    if f.is_dir():
        f = next(f.glob("*.csv"))
    items = []
    with f.open() as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            # Column names vary; common pattern: Code_Before, Code_After, Smell, Refactoring
            before = (row.get("Code_Before") or row.get("before") or
                      row.get("source_code") or row.get("buggy_code"))
            after = (row.get("Code_After") or row.get("after") or
                     row.get("refactored_code") or row.get("fixed_code"))
            if not before or not after: continue
            items.append({
                "id": row.get("id") or f"refactor-{i}",
                "context": before,
                "question": "Describe the change applied (name what was fixed).",
                "answer": row.get("commit_message") or row.get("Refactoring") or "?",
                "type": "code_edit",
                "meta": {"after": after, "smell": row.get("Smell"),
                         "refactoring": row.get("Refactoring"),
                         "commit_url": row.get("commit_url")},
            })
            if n and len(items) >= n: break
    return items
