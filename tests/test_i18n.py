"""Validate English/Italian catalogs and their references in app.py (no Qt needed)."""
import ast
import json
import string
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from i18n import Translator


class InternationalizationTests(unittest.TestCase):
    def setUp(self):
        self.en = json.loads((ROOT / 'translations/en.json').read_text(encoding='utf-8'))
        self.it = json.loads((ROOT / 'translations/it.json').read_text(encoding='utf-8'))

    def test_same_keys_in_both_languages(self):
        self.assertEqual(set(self.en), set(self.it))
        self.assertGreater(len(self.en), 100)

    def test_no_empty_translations(self):
        for key in self.en:
            self.assertTrue(self.en[key].strip(), key)
            self.assertTrue(self.it[key].strip(), key)

    def test_placeholders_match(self):
        formatter = string.Formatter()
        for key in self.en:
            for language in ('it',):
                source = {name for _, name, _, _ in formatter.parse(self.en[key]) if name is not None}
                dest = {name for _, name, _, _ in formatter.parse(self.it[key]) if name is not None}
                self.assertEqual(source, dest, (key, language))

    def test_all_keys_referenced_by_app_exist(self):
        source = ast.parse((ROOT / 'app.py').read_text(encoding='utf-8'))
        prefixes = ('title.', 'tab.', 'easy.', 'encoder.', 'button.', 'label.', 'hint.',
                    'advanced.', 'flag.', 'daemon.', 'settings.', 'placeholder.',
                    'log.', 'status.', 'dialog.', 'error.')
        for node in ast.walk(source):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.startswith(prefixes):
                    self.assertIn(node.value, self.en, node.value)

    def test_language_switch_and_format(self):
        t = Translator('en')
        self.assertIn('ready', t.t('log.ready', version='1.0.0'))
        t.set_language('it')
        self.assertIn('pronta', t.t('log.ready', version='1.0.0'))
        self.assertEqual(t.language, 'it')

    def test_invalid_language_falls_back_to_english(self):
        t = Translator('xx')
        self.assertEqual(t.language, 'en')
        self.assertEqual(t.t('status.ready'), 'READY')


if __name__ == '__main__':
    unittest.main()
