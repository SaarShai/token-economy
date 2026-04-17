"""SQuAD v2 adapter (HF datasets)."""
def load(_path=None, n=None):
    from datasets import load_dataset
    ds = load_dataset("rajpurkar/squad_v2", split="validation")
    items = []
    for x in ds:
        if not x["answers"]["text"]: continue
        if not (300 <= len(x["context"]) <= 3000): continue
        items.append({
            "id": x["id"],
            "context": x["context"],
            "question": x["question"],
            "answer": x["answers"]["text"][0],
            "type": "extractive_qa",
            "meta": {},
        })
        if n and len(items) >= n: break
    return items
