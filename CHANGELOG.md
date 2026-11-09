# Changelog

All notable changes to **Doubletake GUI** are documented here. This changelog describes the unofficial GUI, **not** [omarroth/doubletake](https://github.com/omarroth/doubletake).

## [1.0.0] — 2026-11-09

### Added

- Public release packaging as a source-only `.tar.gz` with LGPL-3.0-or-later licensing and full license texts.
- Complete English README with prerequisite and installation links to the original Doubletake project.
- English default interface and Italian translation, maintained as separate UTF-8 JSON catalogs.
- Live English / Italiano language selection with persistent preference.
- KDE Plasma desktop launcher and its user-level installer/uninstaller.
- User-friendly three-step screen-sharing workflow, alongside a full Advanced area and integrated logging.
- Documentation and tests for safe binary discovery, generated commands and localization.

### Preserved from preview versions

- Non-empty executable paths are **never overwritten** by auto-detection.
- `/opt/apple/bin` is a preferred executable search location.
- Automatic, NVIDIA NVENC and Intel/AMD VAAPI encoding presets.
- Saved streaming preferences, file-based configuration, encrypted-secret field, daemon controls, and log export.

### Packaging note

This release **does not** bundle Doubletake. Install it separately from [omarroth/doubletake](https://github.com/omarroth/doubletake) before starting the GUI.
