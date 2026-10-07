#!/usr/bin/env bash
# IPGHOST launcher — Linux-first, works from any working directory.
set -euo pipefail

# Resolve project root from the script location (never rely on pwd).
SCRIPT_PATH="${BASH_SOURCE[0]:-}"
if [[ -z "$SCRIPT_PATH" ]]; then
  SCRIPT_PATH="$0"
fi
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

PYTHON_BIN=""
if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
elif [[ -x "$PROJECT_ROOT/.venv/Scripts/python.exe" ]]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "[ERROR] python3 not found. Please install Python 3.9+." >&2
  exit 5
fi

# Create a local venv on first run (no root, no sudo pip).
if [[ ! -x "$PROJECT_ROOT/.venv/bin/python" && ! -x "$PROJECT_ROOT/.venv/Scripts/python.exe" ]]; then
  if "$PYTHON_BIN" -c "import venv" >/dev/null 2>&1; then
    echo "[+] Creating virtual environment..." >&2
    "$PYTHON_BIN" -m venv "$PROJECT_ROOT/.venv" >&2 || true
    if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
      PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
    elif [[ -x "$PROJECT_ROOT/.venv/Scripts/python.exe" ]]; then
      PYTHON_BIN="$PROJECT_ROOT/.venv/Scripts/python.exe"
    fi
  fi
fi

# Zero runtime dependencies: stdlib only. If a future provider needs extra
# packages, install them here from a locked requirements file.
export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export IPGHOST_PROJECT_ROOT="$PROJECT_ROOT"

exec "$PYTHON_BIN" -m ipghost "$@"
