"""Ensure automatic discovery never destroys user-specified executable paths."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from binary_paths import detect_only_if_empty, executable_path, find_binary


class PathSafetyTests(unittest.TestCase):
    def test_valid_manual_path_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            good = Path(directory) / 'doubletake'
            good.write_text('#!/bin/sh\nexit 0\n')
            good.chmod(0o755)
            self.assertEqual(detect_only_if_empty(str(good), 'doubletake'), str(good))

    def test_even_missing_manual_path_is_kept(self):
        path = '/mnt/disco-smontato/bin/doubletake'
        self.assertEqual(detect_only_if_empty(path, 'doubletake'), path)

    def test_no_fake_path_on_failed_search(self):
        with tempfile.TemporaryDirectory() as directory:
            name = 'doubletake-guibehavior-test-unlikely-987654'
            with patch('binary_paths.shutil.which', return_value=None):
                self.assertEqual(find_binary(name, base=Path(directory)), '')
                self.assertEqual(detect_only_if_empty('', name, base=Path(directory)), '')

    def test_prefers_real_executable_when_field_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            good = Path(directory) / 'doubletake'
            good.write_text('#!/bin/sh\nexit 0\n')
            good.chmod(0o755)
            self.assertEqual(find_binary('doubletake', preferred=str(good), base=Path(directory)),
                             str(good.resolve()))
            self.assertEqual(detect_only_if_empty('', 'doubletake', str(good), Path(directory)),
                             str(good.resolve()))

    def test_non_executable_is_not_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / 'doubletake'
            bad.write_text('not executable')
            bad.chmod(0o644)
            self.assertEqual(executable_path(str(bad)), '')

    def test_tilde_is_expanded_for_check_only(self):
        with tempfile.TemporaryDirectory() as directory:
            good = Path(directory) / 'doubletake'
            good.write_text('#!/bin/sh\nexit 0\n')
            good.chmod(0o755)
            with patch.dict(os.environ, {'HOME': directory}):
                # expanduser() picks up HOME on Unix, independently of Path.home().
                self.assertEqual(executable_path('~/doubletake'), str(good.resolve()))


if __name__ == '__main__':
    unittest.main()
