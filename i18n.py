# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tiny, dependency-free JSON-based translator for the Doubletake GUI."""
from __future__ import annotations

import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parent / 'translations'
LANGUAGES = ('en', 'it')


class Translator:
    def __init__(self, language: str = 'en', directory: Path = CATALOG) -> None:
        self.directory = Path(directory)
        self.english = self._read('en')
        self.language = 'en'
        self.strings = self.english
        self.set_language(language)

    def _read(self, language: str) -> dict[str, str]:
        with (self.directory / f'{language}.json').open(encoding='utf-8') as file:
            result = json.load(file)
        if not isinstance(result, dict) or not all(isinstance(k, str) and isinstance(v, str)
                                                   for k, v in result.items()):
            raise ValueError(f'Invalid translation catalog: {language}')
        return result

    def set_language(self, language: str) -> None:
        if language not in LANGUAGES:
            language = 'en'
        self.strings = self.english if language == 'en' else self._read(language)
        self.language = language

    def t(self, key: str, **kwargs) -> str:
        pattern = self.strings.get(key, self.english.get(key, key))
        return pattern.format(**kwargs) if kwargs else pattern
