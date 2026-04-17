# Token Economy — Index

Catalog. Read this + schema.md first. Grep folders for topic. Load only matched pages.

## Concepts (techniques)
- [[concepts/caveman-output-compression]] — terse output style, 65% savings
- [[concepts/caveman-compress-session-files]] — rewrite CLAUDE.md etc, 46% avg
- [[concepts/llmlingua]] — token-level perplexity dropping, 2-6x
- [[concepts/prefix-caching]] — 90% cost cut on repeat
- [[concepts/karpathy-wiki]] — offload context to structured KB
- [[concepts/structured-outputs]] — JSON schema vs chat, 3-8x output cut
- [[concepts/speculative-decoding]] — EAGLE-3, Medusa, 2-3x throughput
- [[concepts/kv-cache-eviction]] — StreamingLLM, SnapKV, H2O
- [[concepts/unsloth-distill]] — tiny specialist replaces API call
- [[concepts/superpowers-skills]] — front-load behavior as skill.md

## Patterns
- [[patterns/compound-compression-pipeline]] — stack 4 techniques, 80-90% total
- [[patterns/semantic-diff-edits]] — send diff not full file
- [[patterns/wiki-query-shortcircuit]] — grep vault before re-synthesis
- [[patterns/tiny-model-router]] — 0.5B classifier dispatches

## Roadmap
- [[ROADMAP]] — live tracker: directions, status, next steps

## Infrastructure
- [[bench/README]] — **benchmark registry** (Kaggle + HF), uniform item schema, Kaggle Notebook template for free-GPU evals

## Projects (our builds)
- [[projects/compound-compression-pipeline/RESULTS]] — **ComCom** prototype, 44.5% @ ~Δ−0.25 score (SQuAD eval-v2); eval-v3 in progress
- [[projects/semdiff/README]] — **prototype, 95.5% on large file re-read**
- [[projects/context-keeper/README]] — **prototype, structured PreCompact memory**

## People
- [[people/julius-brussee]] — caveman
- [[people/jesse-vincent]] — superpowers (obra)
- [[people/karpathy]] — wiki pattern
- [[people/unsloth-team]] — daniel + michael han

## Raw
- [[raw/2026-04-17-research-brief]] — initial token-efficiency landscape survey
