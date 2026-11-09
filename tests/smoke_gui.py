"""CI-only PySide6 smoke test, executable with QT_QPA_PLATFORM=offscreen.

Unlike unittest tests, this requires the real PySide6 runtime.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

with tempfile.TemporaryDirectory() as folder:
    os.environ['XDG_CONFIG_HOME'] = folder
    from PySide6.QtWidgets import QApplication
    from app import MainWindow

    application = QApplication([])
    window = MainWindow()
    assert window.locale.language == 'en'
    window.easy_target.setText('192.168.1.77')
    assert window.target.text() == '192.168.1.77'
    window.easy_encoder.setCurrentIndex(window.easy_encoder.findData('nvenc'))
    assert window.easy_args() == ['-target', '192.168.1.77', '-hwaccel', 'nvenc']
    window.language.setCurrentIndex(window.language.findData('it'))
    assert window.locale.language == 'it'
    assert 'Condividi' in window.easy_hint.text() or 'Premi' in window.easy_hint.text()
    assert window.easy_args() == ['-target', '192.168.1.77', '-hwaccel', 'nvenc']
    window.close()
    application.quit()
print('GUI smoke test OK')
