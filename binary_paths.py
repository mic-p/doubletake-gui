# SPDX-License-Identifier: LGPL-3.0-or-later
"""Conservative Doubletake executable discovery; independent from Qt."""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def executable_path(raw: str) -> str:
    """Return the canonical path only when it points to an executable file."""
    raw = raw.strip()
    if not raw:
        return ''
    expanded = os.path.expandvars(os.path.expanduser(raw))
    if os.path.sep not in expanded:
        expanded = shutil.which(expanded) or expanded
    candidate = Path(expanded)
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate.resolve())
    return ''


def find_binary(name: str, preferred: str = '', base: Path | None = None) -> str:
    """Search for actual executables; never fabricate a plausible path."""
    base = base or Path(__file__).resolve().parent
    candidates = ([preferred] if preferred.strip() else []) + [
        f'/opt/apple/bin/{name}',
        str(base / 'bin' / name),
        str(base.parent / 'bin' / name),
        str(Path.home() / '.local' / 'bin' / name),
    ]
    which = shutil.which(name)
    if which:
        candidates.append(which)
    candidates += [f'/usr/local/bin/{name}', f'/usr/bin/{name}']
    for candidate in candidates:
        result = executable_path(candidate)
        if result:
            return result
    return ''


def detect_only_if_empty(current: str, name: str, preferred: str = '',
                         base: Path | None = None) -> str:
    """Never replace a non-empty user-selected path, valid or not."""
    return current if current.strip() else find_binary(name, preferred, base)
