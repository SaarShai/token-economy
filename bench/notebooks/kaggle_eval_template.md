# Running evals on Kaggle (free T4 GPU, 30h/wk)

Local eval on M-series CPU hits ~10s/generation for phi4:14b. On Kaggle T4 GPU with vLLM it drops to ~0.5s/gen. Ten times the throughput, free.

## Workflow

1. **Prepare eval items locally.**
   ```bash
   cd bench
   python3 -c "
   from adapters.coqa import load
   import json
   items = load('data/coqa/coqa-dev-v1.0.json', n=50)
   with open('/tmp/coqa_50.jsonl','w') as f:
       for it in items: f.write(json.dumps(it)+'\n')
   "
   ```

2. **Upload as a Kaggle dataset** (one-time or versioned).
   ```bash
   kaggle datasets init -p /tmp/coqa_50  # writes dataset-metadata.json
   # edit metadata: title="TokenEconomy CoQA-50", id="saarshai/tokecon-coqa-50"
   kaggle datasets create -p /tmp/coqa_50
   # or update:
   kaggle datasets version -p /tmp/coqa_50 -m "v2"
   ```

3. **Create a Kaggle Notebook** (via web or CLI):
   - Accelerator: **GPU T4 x2** (free tier).
   - Internet: ON (to pull models from HF).
   - Attach dataset: `saarshai/tokecon-coqa-50`.

4. **Notebook contents** (template below). Commits + runs. Outputs saved in `/kaggle/working/`, versioned.

5. **Download results**:
   ```bash
   kaggle kernels output saarshai/tokecon-eval-v1 -p ./results/
   ```

## Notebook template

```python
# Cell 1 — install
!pip install --quiet vllm tiktoken llmlingua datasets

# Cell 2 — pull items
import json
items = [json.loads(l) for l in open('/kaggle/input/tokecon-coqa-50/coqa_50.jsonl')]
print(f"{len(items)} items")

# Cell 3 — pull our pipeline code (small)
# Easiest: upload pipeline_v2.py + verify.py as a second dataset, or inline here
# inline version for brevity:
exec(open('/kaggle/input/tokecon-comcom/pipeline_v2.py').read())
exec(open('/kaggle/input/tokecon-comcom/verify.py').read())

# Cell 4 — target model via vLLM (fast)
from vllm import LLM, SamplingParams
llm = LLM("microsoft/Phi-4-mini-instruct", gpu_memory_utilization=0.8)
params = SamplingParams(temperature=0, max_tokens=200, seed=42)

# Cell 5 — judge via HF pipeline (smaller, keep resident)
from transformers import pipeline
judge = pipeline("text-generation", "Qwen/Qwen2.5-7B-Instruct", device="cuda")

# Cell 6 — run all 4 conditions × N items × runs
results = []
for item in items:
    for cond in ("A_full", "B_v1", "C_v2", "D_adaptive"):
        # reuse our pipeline_v2.compress and verify.escalate_gen
        ...
        results.append({...})

# Cell 7 — save
with open('/kaggle/working/results.jsonl', 'w') as f:
    for r in results: f.write(json.dumps(r) + '\n')
```

## Why this is the right shape

- **Free GPU**: 30h/wk T4 — plenty for N=500 across 4 conditions and 3 models.
- **Versioned kernels**: every run is reproducible by ID.
- **Public sharing**: flip kernel to public → others can re-run, peer review.
- **No cost to iterate**: local iteration for correctness, Kaggle runs for statistical power.

## One-off setup

```bash
# Upload our pipeline + verify + fetch modules as a companion dataset:
cd bench
mkdir /tmp/tokecon-code
cp ../projects/compound-compression-pipeline/{pipeline_v2.py,verify.py,pipeline.py} /tmp/tokecon-code/
kaggle datasets init -p /tmp/tokecon-code
# edit metadata id=saarshai/tokecon-comcom
kaggle datasets create -p /tmp/tokecon-code
```

Then attach BOTH datasets (items + code) to the notebook.

## Running semdiff evals

Different shape — semdiff is CPU-fast, GPU not needed. Run locally. But Kaggle is useful for:
- Running on many language grammars at once (containerized).
- Larger realistic codebases pulled from GitHub (uses internet quota).

## Budget planning (free tier)
- GPU: 30h/wk T4 → ~50 evals × 500 items × 4 conds / week.
- Notebook runtime: max 9h per run.
- Internet: free to use during run.
- Storage: 20GB dataset, 5GB output.

Enough for the foreseeable eval needs.
