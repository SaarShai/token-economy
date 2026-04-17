---
type: project
tags: [benchmarks, kaggle, eval-infra]
confidence: med
evidence_count: 2
---

# bench/ — benchmark registry + fetchers + adapters + Kaggle integration

Unified eval infrastructure. Any dataset → uniform `eval-item` schema → our tools.

## Layout
```
bench/
├── registry.yaml        # named datasets + metadata
├── fetch.py             # pull any registered dataset (kaggle or hf)
├── adapters/            # source-specific → uniform schema
│   ├── coqa.py
│   ├── squad.py
│   └── refactoring.py
├── data/                # downloaded (gitignored)
└── notebooks/
    └── kaggle_eval_template.md
```

## Uniform item schema
```python
{
  "id": str,
  "context": str,       # to compress
  "question": str,      # for QA; "describe the change" for code_edit
  "answer": str,        # ground truth for judge
  "type": str,          # extractive_qa | multiturn_qa | code_edit | ...
  "meta": dict,         # task-specific
}
```

## Usage
```bash
python3 fetch.py                        # list registered datasets
python3 fetch.py coqa                   # download CoQA
python3 -c "from adapters.coqa import load; print(len(load('data/coqa/coqa-dev-v1.0.json')))"
```

## Current registry

| key | source | tests | type | status |
|---|---|---|---|---|
| squad_v2 | hf | ComCom | extractive_qa | used in eval-v2/v3 |
| coqa | kaggle | ComCom, context-keeper | multiturn_qa | downloaded |
| sciq | kaggle | ComCom | multiple_choice | registered |
| code_bug_fix_pairs | kaggle | semdiff | code_edit_pairs | downloaded |
| code_refactoring_120k | kaggle | never | metadata_only | REJECTED (no bodies) |
| bbc_news | kaggle | ComCom | summarization | registered |
| longbench | hf | ComCom | long_context_qa | registered |

## Kaggle strategy (three uses)

1. **Datasets** for eval material — pulled via registry.
2. **Kaggle Notebooks** as free T4 GPU (30h/wk) — run N=500+ evals without local laptop burn. vLLM gets ~10× throughput over our CPU-Ollama runs. See [[notebooks/kaggle_eval_template]].
3. **Publishing** — share results as Kaggle datasets + public notebooks for peer review.

## Why this matters

Our current N=8 evals give CI=±0.5 on quality delta. Kaggle free GPU → N=500 in ~6h → CI=±0.06. Same methodology, publishable tightness.

## Next
- Wire adapters into `eval_v4.py` that can eval any registered dataset.
- Upload first Kaggle dataset (bench items + our pipeline code).
- Run first Kaggle notebook (N=50 CoQA × 4 conds) as the reference run.
- Add BBC News + LongBench adapters.
- Add an MMLU adapter for factual-recall stress.
