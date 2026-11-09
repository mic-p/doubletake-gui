"""Verify quick-start arguments without importing Qt."""
import ast
import sys
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'app.py'
root = ast.parse(SOURCE.read_text(encoding='utf-8'))
main_class = next(node for node in root.body if isinstance(node, ast.ClassDef) and node.name == 'MainWindow')
function = next(node for node in main_class.body if isinstance(node, ast.FunctionDef) and node.name == 'easy_args')
# Sposta il metodo in un modulo sintetico: nel corpo non sono richieste API Qt.
module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
namespace = {}
exec(compile(module, str(SOURCE), 'exec'), namespace)
easy_args = namespace['easy_args']


class Field:
    def __init__(self, value):
        self.value = value

    def currentText(self):
        return self.value


class FakeWindow:
    def __init__(self, ip, encoder):
        self.ip = ip
        self.hw = Field(encoder)
        self.advanced_flags = ['-debug', '-fps', '144']

    def target_args(self, required=False):
        if required and not self.ip:
            raise ValueError('target required')
        return ['-target', self.ip] if self.ip else []


class SimpleModeTests(unittest.TestCase):
    def test_automatic(self):
        self.assertEqual(easy_args(FakeWindow('', 'auto')), [])

    def test_nvidia(self):
        self.assertEqual(easy_args(FakeWindow('192.168.1.77', 'nvenc')),
                         ['-target', '192.168.1.77', '-hwaccel', 'nvenc'])

    def test_intel_amd(self):
        self.assertEqual(easy_args(FakeWindow('192.168.1.77', 'vaapi')),
                         ['-target', '192.168.1.77', '-hwaccel', 'vaapi'])

    def test_no_extra_advanced_flags(self):
        self.assertNotIn('-debug', easy_args(FakeWindow('', 'auto')))
        self.assertNotIn('-fps', easy_args(FakeWindow('', 'nvenc')))

    def test_pairing_requires_ip(self):
        with self.assertRaises(ValueError):
            easy_args(FakeWindow('', 'auto'), pair=True)
        self.assertEqual(easy_args(FakeWindow('192.168.1.77', 'auto'), pair=True),
                         ['-target', '192.168.1.77', '-pair'])

    def test_video_only(self):
        self.assertEqual(easy_args(FakeWindow('', 'auto'), video_only=True), ['-no-audio'])


if __name__ == '__main__':
    unittest.main()
