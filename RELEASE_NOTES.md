# Doubletake GUI v1.0.0 — first public release

A clean, standalone PySide6 frontend for the excellent [omarroth/doubletake](https://github.com/omarroth/doubletake) AirPlay sender for Linux.

**Unofficial project:** this is only a graphical controller; it is not an official part of Doubletake and does not ship the upstream engine.

### Highlights

- **Easy mode:** choose a TV, choose Automatic / NVIDIA NVENC / Intel/AMD VAAPI, press Start, approve KDE screen sharing if prompted.
- **No Konsole:** view Doubletake output and answer interactive prompts directly in the window.
- **English + Italiano:** switch instantly; all translations live in editable JSON files.
- **Safe configuration:** auto-detection never overwrites an existing path, even when temporarily unavailable. Searches `/opt/apple/bin` first.
- **Advanced tools:** upstream mirroring flags, command preview, daemon status/discovery/connect/disconnect and log export.
- **KDE-ready:** application icon, `.desktop` integration and scripts to install or remove the shortcut.
- **Open source:** LGPL-3.0-or-later; no pipx and no bundled Doubletake executable.

### Installation (after installing original Doubletake)

```bash
sudo mkdir -p /opt/apple
sudo tar -xzf doubletake-gui-1.0.0.tar.gz -C /opt/apple
/opt/apple/doubletake-gui/run.sh
/opt/apple/doubletake-gui/install-desktop.sh
```

**Read [`README.md`](README.md) first** for how to install the upstream [omarroth/doubletake](https://github.com/omarroth/doubletake), its Go/GStreamer requirements, and how to obtain PySide6.

### Asset

`doubletake-gui-1.0.0.tar.gz` — source, translations, application icon, license, documentation and desktop integration.

### Limitations

- Requires the separately installed Doubletake CLI and a Python interpreter with PySide6.
- AirPlay protocol and encoder compatibility are controlled by upstream.
- No end-to-end Apple TV/KDE hardware test is included in this package's automated checks.
