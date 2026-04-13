#!/usr/bin/env bash

set -euo pipefail

OWNER="elisimon-g"
REPO="sicer-architet-agent"
VERSION="${VERSION:-main}"
PACKAGE_SPEC="git+https://github.com/${OWNER}/${REPO}.git@${VERSION}"
RAW_BASE_URL="https://raw.githubusercontent.com/${OWNER}/${REPO}/${VERSION}"
COPILOT_DIR="${COPILOT_HOME:-$HOME/.copilot}"
SKILL_NAME="sicer"
SKILL_DIR="${COPILOT_DIR}/skills/${SKILL_NAME}"
MCP_CONFIG_PATH="${COPILOT_DIR}/mcp-config.json"
MCP_SERVER_NAME="sicer"

log() {
  printf '[sicer-architet-agent] %s\n' "$1"
}

fail() {
  printf '[sicer-architet-agent] %s\n' "$1" >&2
  exit 1
}

download_to() {
  local url="$1"
  local output="$2"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$output"
    return
  fi

  if command -v wget >/dev/null 2>&1; then
    wget -qO "$output" "$url"
    return
  fi

  fail "curl or wget is required to download skill files."
}

install_package() {
  if command -v pipx >/dev/null 2>&1; then
    log "Installing CLI with pipx"
    pipx install --force "$PACKAGE_SPEC"
    return
  fi

  if command -v uv >/dev/null 2>&1; then
    log "Installing CLI with uv tool"
    uv tool install --force "$PACKAGE_SPEC"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    log "Installing CLI with python3 -m pip --user"
    python3 -m pip install --user --upgrade "$PACKAGE_SPEC"
    return
  fi

  fail "pipx, uv, or python3 is required to install the CLI."
}

install_skill() {
  mkdir -p "$SKILL_DIR"
  download_to "${RAW_BASE_URL}/skills/${SKILL_NAME}/SKILL.md" "${SKILL_DIR}/SKILL.md"
  log "Installed Copilot skill in ${SKILL_DIR}"
}

configure_mcp() {
  mkdir -p "$COPILOT_DIR"

  if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 is required to update Copilot MCP configuration automatically."
  fi

  MCP_CONFIG_PATH="$MCP_CONFIG_PATH" MCP_SERVER_NAME="$MCP_SERVER_NAME" python3 <<'PY'
import json
import os
from pathlib import Path

config_path = Path(os.environ["MCP_CONFIG_PATH"])
server_name = os.environ["MCP_SERVER_NAME"]

if config_path.exists():
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {config_path}: {exc}") from exc
else:
    data = {}

if not isinstance(data, dict):
    raise SystemExit(f"Expected {config_path} to contain a JSON object.")

mcp_servers = data.setdefault("mcpServers", {})
if not isinstance(mcp_servers, dict):
    raise SystemExit("Expected 'mcpServers' to be a JSON object.")

mcp_servers[server_name] = {
    "command": "sicer-architet-agent",
    "args": []
}

config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

  log "Configured Copilot MCP server '${MCP_SERVER_NAME}' in ${MCP_CONFIG_PATH}"
}

print_next_steps() {
  cat <<EOF

Installed sicer-architet-agent.

Copilot CLI is now preconfigured with:
  - MCP server: ${MCP_SERVER_NAME}
  - skill: /${SKILL_NAME}

Next steps in Copilot CLI:
  1. Restart Copilot CLI or run /skills reload if a session is already open

Example prompt:
  Use /sicer to scan this project and show me the top critical issue

EOF
}

install_package
configure_mcp

if [ "${INSTALL_SKILL:-1}" = "1" ]; then
  install_skill
fi

print_next_steps
