#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
set -euo pipefail
APP_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

fail() {
  local en="$1" it="$2" message="$1"
  if [[ "${LANG:-}" == it* || "${LC_ALL:-}" == it* || "${LC_MESSAGES:-}" == it* ]]; then
    message="$it"
  fi
  if command -v kdialog >/dev/null 2>&1; then kdialog --error "$message" || true; fi
  printf '%s\n' "$message" >&2
  exit 1
}

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  fail "Python 3 not found: $PYTHON_BIN. Install Python or set PYTHON_BIN." \
       "Python 3 non trovato: $PYTHON_BIN. Installa Python o imposta PYTHON_BIN."
fi

if ! "$PYTHON_BIN" -c 'from PySide6.QtWidgets import QApplication' >/dev/null 2>&1; then
  fail "PySide6 is not available in $PYTHON_BIN. Install PySide6 for that interpreter (see README.md)." \
       "PySide6 non è disponibile in $PYTHON_BIN. Installalo per quell’interprete (vedi README.md)."
fi

exec "$PYTHON_BIN" "$APP_DIR/app.py" "$@"
