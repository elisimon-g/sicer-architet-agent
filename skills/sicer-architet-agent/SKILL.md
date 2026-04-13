---
name: sicer-architet-agent
description: Use this skill when you need to analyze a multi-module workspace, identify the right module to modify, or plan a safe cross-module change with the sicer-architet-agent MCP tools.
---

When this skill is relevant, prefer the MCP tools exposed by the standalone `sicer-architet-agent` server.

Use them in this order:

1. Run `detect_project_type` to classify the workspace and confirm whether it is multi-module.
2. Run `list_modules` to identify the primary and secondary modules.
3. Run `plan_multimodule_change` with the user's requested change to produce:
   - primary module
   - secondary modules
   - entry points
   - files to inspect
   - risks
   - recommended implementation order

Guidelines:

- Prefer architectural analysis before proposing code edits.
- Do not assume REST or UI modules are the correct starting point.
- For legacy monoliths, bias toward core/shared modules unless repository evidence points elsewhere.
- If the user asks for a patch, complete the analysis first and then propose the narrowest safe change set.
