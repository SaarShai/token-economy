---
name: token-economy-external-adoption
description: Use only when maintaining the Token Economy framework repo and considering adoption from another repo.
---

# Token Economy External Adoption

Scope: Token Economy framework maintenance only. This is mandatory for agents modifying this repo when they consider adopting learnings, code sections, skills, files, hooks, integrations, docs patterns, or architecture from another repo into Token Economy. It is not for normal framework users or downstream installed adapters.

Rule: learn deeply before adopting; adopt in the shape of this framework.

## Trigger

Use this skill before any adoption work when the task mentions:
- adopting, integrating, porting, borrowing, copying, vendoring, or learning from another repo
- external skills, hooks, prompts, adapters, MCP servers, CLIs, docs patterns, or architecture
- direct code copy, subtree import, package dependency, or optional external adapter

## Protocol

1. Source inspection:
   - Identify repo URL, commit SHA or tag, license, README/docs, manifests, configs, entrypoints, tests, examples, and relevant conventions.
   - Use web or an ignored local checkout under `.token-economy/external-src/<repo-slug>/`.
   - Do not copy files into tracked source during inspection.

2. Deep understanding:
   - Read docs, implementation, and tests.
   - Map what the repo does, how it works, why its mechanics work, public interfaces, data flow, dependencies, runtime assumptions, failure modes, and security-sensitive behavior.
   - Compare behavior against Token Economy principles: repo-local operation, model-agnostic design, lean startup context, progressive retrieval, no global config by default, and measured claims only.

3. Adoption mode:
   - Choose exactly one: `cite-only`, `pattern-reimplementation`, `native-adapter`, `direct-code-copy`, `vendored-subtree`, or `external-dependency`.
   - Default to `pattern-reimplementation` or `native-adapter`.
   - Use `direct-code-copy`, `vendored-subtree`, or `external-dependency` only with compatible license, clear provenance, small or isolated surface, and documented maintenance/security cost.
   - If license is missing or incompatible, use `cite-only` or clean-room reimplementation.

4. Contradiction and overlap check:
   - Search existing Token Economy tools and wiki before adding new surface.
   - Reject parts that duplicate existing tools without measurable benefit.
   - Reject parts that require global agent settings, hidden network behavior, unsafe secret handling, or unverified savings claims.

5. Framework integration:
   - Decide the exact Token Economy surface: CLI, hook, skill, prompt, config key, MCP/server adapter, docs page, wiki page, or test helper.
   - If the adopted feature is for framework users, wire it into the relevant runtime docs, loader, commands, hooks, or config.
   - If the adopted workflow is only for Token Economy maintainers, keep it in project-maintenance docs/skills and do not expose it as a universal user rule.
   - Distinguish provenance links from operational dependencies.

6. Verification loop:
   - Run upstream examples or tests when feasible to understand baseline behavior.
   - Add local tests proving the adopted behavior works inside Token Economy.
   - Run relevant unit tests, `./te doctor`, and CLI/hook smoke checks.
   - Fix failures and rerun until clean.
   - Do not claim adoption is complete without fresh verification evidence.

7. Documentation:
   - For material adoptions, create or update a source-summary/wiki note with URL, commit SHA/tag, license, inspected files, mechanics learned, adopted pieces, rejected pieces, local implementation paths, verification commands, and residual risk.
   - Update `external-adapters.md`, relevant project/concept docs, `log.md`, and indexes only after verified work.
   - Do not document planned adoption as completed adoption.

## Output Contract

Before implementation, produce a compact adoption brief:
- source and commit/tag
- inspected files and mechanics learned
- chosen adoption mode and rejected alternatives
- contradiction/overlap result
- Token Economy integration surface
- verification plan

After implementation, report changed files, verification commands, provenance, and remaining risk.
