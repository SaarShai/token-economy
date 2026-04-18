import pathlib

def load(path, n=None):
    examples = []
    path = pathlib.Path(path)
    
    for cat_dir in (path / "News Articles").iterdir():
        if not cat_dir.is_dir():
            continue
        category = cat_dir.name
        summaries_dir = path / f"Summaries/{category}"
        
        for article_file in cat_dir.glob("*.txt"):
            nnn = article_file.stem
            summary_file = summaries_dir / f"{nnn}.txt"
            
            if not summary_file.exists():
                continue
                
            with open(article_file, 'r', encoding='utf-8') as f:
                context = f.read()
                
            with open(summary_file, 'r', encoding='utf-8') as f:
                answer = f.read().strip()
                
            example_id = f"{category}-{nnn}"
            examples.append({
                "id": example_id,
                "context": context,
                "question": "Summarize this article in one sentence.",
                "answer": answer,
                "type": "summarization",
                "meta": {"category": category}
            })
            
            if n is not None and len(examples) >= n:
                break
                
        if n is not None and len(examples) >= n:
            break
            
    return examples
