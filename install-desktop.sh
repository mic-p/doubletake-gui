#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# Install the KDE desktop shortcut for the current user, without root.
set -euo pipefail
APP_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/doubletake-gui.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Doubletake GUI
Name[it]=Doubletake GUI
GenericName=AirPlay screen mirroring
GenericName[it]=Duplicazione schermo AirPlay
Comment=Unofficial graphical frontend for omarroth/doubletake with an integrated log
Comment[it]=Interfaccia grafica non ufficiale per omarroth/doubletake con log integrato
Exec="$APP_DIR/run.sh"
TryExec=$APP_DIR/run.sh
Icon=$APP_DIR/icons/doubletake-gui.png
Terminal=false
Categories=AudioVideo;Network;Utility;
Keywords=AirPlay;screen;mirroring;Apple TV;Doubletake;
Keywords[it]=AirPlay;schermo;mirroring;Apple TV;Doubletake;
StartupNotify=true
EOF
chmod 644 "$DESKTOP_DIR/doubletake-gui.desktop"
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
fi
printf 'KDE desktop launcher installed: %s\n' "$DESKTOP_DIR/doubletake-gui.desktop"
