# Sicer Architet Agent

Standalone local agent for GitHub Copilot CLI built with **LangGraph** and **MCP**.

It is designed for **multi-module codebases** and helps Copilot answer questions such as:

- which module should I modify first?
- what other modules are impacted?
- what files should I inspect before patching?
- what is a safe order for a cross-module change?

## What it provides

This project exposes an MCP server with three initial tools:

- `detect_project_type`
- `list_modules`
- `plan_multimodule_change`

The planning flow is orchestrated with LangGraph, but kept deterministic in the first version so it can run locally without external model calls.

## Installation

### One-line install

```bash
curl -fsSL https://raw.githubusercontent.com/elisimon-g/sicer-architet-agent/main/install.sh | bash
```

The installer:

- installs the `sicer-architet-agent` CLI
- installs the optional Copilot skill in `~/.copilot/skills/sicer`
- auto-registers the MCP server in `~/.copilot/mcp-config.json`
- leaves Copilot CLI ready to use after a restart or `/skills reload`

### Option 1: local editable install

```bash
cd sicer-architet-agent
python -m pip install -e .
```

### Option 2: run with uv

```bash
cd sicer-architet-agent
uv sync
```

## Run locally

```bash
sicer-architet-agent
```

The server uses **STDIO** transport for MCP hosts.

## Add it to GitHub Copilot CLI

The installer auto-configures Copilot CLI with a `sicer` MCP server that launches:

```text
sicer-architet-agent
```

If you prefer `uv`, point Copilot CLI to:

```text
uv --directory /absolute/path/to/sicer-architet-agent run sicer-architet-agent
```

Example config snippet:

```json
{
  "mcpServers": {
    "architect-agent": {
      "command": "sicer-architet-agent",
      "args": []
    }
  }
}
```

## Optional skill

This repository also includes an optional skill under `skills/sicer`.

You can add it in Copilot CLI with `/skills add /absolute/path/to/sicer-architet-agent/skills`
and reload with `/skills reload`.

Example prompt:

```text
Use /sicer to plan a safe change in this Maven monolith.
```

## Development

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Tool behavior

### `detect_project_type`

Inspects a workspace and summarizes the dominant build and architectural signals.

### `list_modules`

Parses Maven root and child `pom.xml` files and reports modules, packaging, dependencies, and quick indicators.

### `plan_multimodule_change`

Builds a structured plan:

- primary module
- secondary modules
- likely entry points
- candidate files to inspect
- change risks
- recommended implementation order
