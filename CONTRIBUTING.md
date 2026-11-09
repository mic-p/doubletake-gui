# Contributing to Doubletake GUI

This is an **unofficial frontend** for [omarroth/doubletake](https://github.com/omarroth/doubletake). Please keep GUI reports separate from upstream AirPlay/encoder issues.

1. Make an issue or pull request describing the GUI problem or improvement.
2. Keep the three-step **Get started** screen uncluttered; put specialized settings under **Advanced**.
3. All visible GUI strings belong in both `translations/en.json` and `translations/it.json`, with the same keys. The application changes language live.
4. Never overwrite configured executable paths during automatic discovery.
5. Never print mirroring PINs/passwords in the GUI log or store them in `config.ini`.
6. Run `python3 -m unittest discover -s tests -v` and `python3 -m py_compile app.py i18n.py binary_paths.py` before submitting changes.
7. Keep links and attribution to the main project visible in the README and Settings page.

Source files are distributed under LGPL-3.0-or-later. Any third-party code or images added in the future must have compatible attribution and licensing.
