---
type: concept
axis: input_compression  # KV cache is inference-time context memory
tags: [turboquant, kv-cache, llama-cpp, apple-silicon, gguf-stack]
confidence: med
evidence_count: 4
related: [[concepts/optimization-axes]], [[raw/2026-04-20-turboquant-research]]
---

# TurboQuant — KV-cache compression (ICLR 2026)

## What it is

KV-cache quantization for transformer inference. NOT weight quantization. Runs during inference; compresses the key-value tensors that accumulate as the context grows.

**Mechanism**: Walsh-Hadamard random rotation (O(d log d)) spreads outliers → near-Beta distribution → Lloyd-Max scalar quantization per coordinate. Within ~2.7× of Shannon entropy lower bound.

## Measured compression (Apple Silicon, M5 Max)

| cache type | bits/val | compression | PPL vs q8_0 |
|---|---:|---:|---:|
| turbo4 | 4.25 | **3.8×** | **+0.23%** (safe default) |
| turbo3 (blk=128) | 3.125 | **5.1×** | +1.06% |
| turbo2 | 2.5 | **6.4×** | +6.48% (extreme) |

## Stacks on top of GGUF

User's claim verified. TurboQuant compresses the *runtime* KV cache. Weight quantization (Q4_K_M etc.) is independent. Safe stack for Q4_K_M GGUFs: **`-ctk q8_0 -ctv turbo4`** (asymmetric — K at q8_0, V compressed).

**Symmetric on low-bit weights = catastrophic** on some models (Qwen2.5-7B Q4_K_M + turbo3/turbo3 → PPL 3556, gibberish). Bigger models handle symmetric fine (104B: +3.6%, 70B: +11.4%).

## Validated findings (community cross-tested)

1. **V compression is free.** Even 2-bit V at q8_0 K = zero measurable quality loss.
2. **All quality degradation comes from K compression.** → asymmetric K/V rescues low-bit models.
3. **Boundary layers (first 2 + last 2) sensitive.** Protect them at higher precision → 37-91% of quality gap recovered.
4. **QJL stage hurts attention.** The paper's 2nd stage (1-bit residual) amplifies softmax variance. All community implementations confirm: disable it. TheTom's fork uses MSE-only.

## Repos (reviewed)

| repo | best for | install |
|---|---|---|
| **TheTom/llama-cpp-turboquant** | **Apple Silicon (Metal)** — primary | git clone + cmake + Metal |
| TheTom/turboquant_plus | research/diagnostic Python package | pip from pyproject |
| ekryski/mlx-swift-lm | fastest Apple-native (Swift MLX) | Xcode |
| OnlyTerp/turboquant | pip library + vLLM/SGLang PRs | pip install turboquant |
| tonbistudio/turboquant-pytorch | PyTorch research (CUDA/Win only) | pip + CUDA |

## Relevance to our stack (Token Economy)

| our tool | interaction with TurboQuant |
|---|---|
| ComCom | orthogonal (input-side compression; TQ is inference-side) — composes cleanly |
| semdiff | no interaction |
| context-keeper | no interaction |
| Ollama (M1/M2) | **incompatible** — Ollama doesn't expose `-ctk/-ctv` flags. Bypass via direct llama-server. |
| EXO (M1/M1B MLX) | different runtime; Swift MLX fork exists but not wired into EXO. Don't patch EXO. |

## Per-machine install status

| machine | decision | reason |
|---|---|---|
| **M2 Max (local)** | **INSTALL** (in progress) | Clean, no active downloads, 64GB headroom. llama.cpp Metal fork building. |
| **M1 Max** | WAIT | Active Qwen3.6-35B download + 32GB RAM tight. After download done, test. |
| **M1B Max** | NO | EXO worker. Don't disrupt cluster. |

## Usage (after M2 build completes)

```bash
~/src/llama-cpp-turboquant/build/bin/llama-server \
  -m <path-to-Q4_K_M.gguf> \
  -ctk q8_0 -ctv turbo4 \
  -fa 1 -ngl 99 \
  --port 8080
```

Then HTTP requests to `http://localhost:8080/v1/chat/completions` — OpenAI-compatible.

## Caveats

1. `--cache-type-k turbo3 -ctv turbo3` on Q4_K_M = can catastrophically fail. Validate PPL first.
2. macOS Metal memory cap: for 70B+ at long context, raise `iogpu.wired_limit_mb` manually.
3. Ollama is NOT compatible. Must run llama-server directly.
4. Still experimental (April 2026). Expect API churn.
5. "×6" headline = turbo2 only. Practical number is 3.8-5.1× at near-neutral quality.

## Sources

- Paper: arxiv 2504.19874
- Google Research blog
- TheTom/llama-cpp-turboquant README + docs/turboquant-recommendations.md
- Community testing across 30+ testers / multiple GPUs
- See [[raw/2026-04-20-turboquant-research]] for full subagent survey
