#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
set -euo pipefail
DESKTOP_FILE="${XDG_DATA_HOME:-$HOME/.local/share}/applications/doubletake-gui.desktop"
rm -f -- "$DESKTOP_FILE"
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
fi
printf 'KDE desktop launcher removed: %s\n' "$DESKTOP_FILE"
