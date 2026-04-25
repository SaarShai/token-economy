# Manual import corrective prompt

Use this when an agent already consumed the older import prompt and mistakenly anchored itself to the Token Economy source checkout instead of the active project workspace.

```text
You are in the active project workspace, not the Token Economy source repository.

Reset your assumptions:
- Treat the current working folder as the only workspace.
- Do not move to or operate from the `token-economy` template repo unless I explicitly ask you to edit the framework itself.
- If `token-economy.yaml` and `start.md` are present in this folder, use them here.
- If you previously assumed the template repo was the workspace, discard that assumption now.

Continue from the current folder only:
1. Read `start.md`, `token-economy.yaml`, `L0_rules.md`, and `L1_index.md` from this workspace.
2. Follow the workspace-local wiki and prompt files in this folder.
3. Use the uploaded summary, handoff, and current instructions as the source of truth for the target project.
4. If you need to import or refresh, keep all writes inside this workspace.
5. Do not re-bootstrap into the template repo or clear/clone any other folder unless explicitly instructed.

Start in plan mode and proceed only after the workspace has been re-anchored correctly.
```
