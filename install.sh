#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_HOME="${HOME}/.local/share/git-story"
VENV_DIR="${INSTALL_HOME}/venv"
BIN_DIR="${HOME}/.local/bin"
TARGET_BIN="${BIN_DIR}/git-story"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[x] python3 is required but not found in PATH"
  exit 1
fi

echo "[>] Installing git-story from: ${REPO_DIR}"

if command -v pipx >/dev/null 2>&1; then
  echo "[>] Using pipx (recommended)"
  if pipx list 2>/dev/null | grep -q "package git-story"; then
    pipx reinstall "${REPO_DIR}"
  else
    pipx install "${REPO_DIR}"
  fi
else
  echo "[>] pipx not found, using isolated venv install"
  mkdir -p "${INSTALL_HOME}"
  python3 -m venv "${VENV_DIR}"
  "${VENV_DIR}/bin/pip" install --upgrade pip >/dev/null
  "${VENV_DIR}/bin/pip" install --upgrade "${REPO_DIR}"

  mkdir -p "${BIN_DIR}"
  ln -sf "${VENV_DIR}/bin/git-story" "${TARGET_BIN}"
fi

if command -v git-story >/dev/null 2>&1; then
  echo "[ok] Installed successfully"
  echo "[ok] Run: git-story --help"
  exit 0
fi

echo "[!] Installed, but git-story is not in your PATH yet"
echo "[!] Add this to your shell config (~/.bashrc or ~/.zshrc):"
echo '    export PATH="$HOME/.local/bin:$PATH"'
echo "[!] Then restart your terminal and run: git-story --help"
