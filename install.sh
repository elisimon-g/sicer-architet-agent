#!/usr/bin/env bash

set -euo pipefail

OWNER="elisimon-g"
REPO="sicer-architet-agent"
VERSION="${VERSION:-main}"
PACKAGE_SPEC="git+https://github.com/${OWNER}/${REPO}.git@${VERSION}"
RAW_BASE_URL="https://raw.githubusercontent.com/${OWNER}/${REPO}/${VERSION}"
SKILL_NAME="sicer-architet-agent"
SKILL_DIR="${COPILOT_HOME:-$HOME/.copilot}/skills/${SKILL_NAME}"

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

print_next_steps() {
  cat <<EOF

Installed sicer-architet-agent.

Next steps in Copilot CLI:
  1. /mcp add
  2. Configure a stdio server with command:
       sicer-architet-agent
  3. /skills reload

Example prompt:
  Use the /sicer-architet-agent skill to analyze this multi-module workspace

EOF
}

install_package

if [ "${INSTALL_SKILL:-1}" = "1" ]; then
  install_skill
fi

print_next_steps
