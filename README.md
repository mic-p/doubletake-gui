# Doubletake GUI

**A simple, unofficial, bilingual PySide6 frontend for [omarroth/doubletake](https://github.com/omarroth/doubletake) on Linux.**

[![License: LGPL-3.0-or-later](https://img.shields.io/badge/License-LGPL--3.0--or--later-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-Linux-informational)
![Language](https://img.shields.io/badge/UI-English%20%7C%20Italiano-informational)

![Doubletake GUI application icon](icons/doubletake-gui-128.png)

Doubletake GUI makes desktop-to-TV mirroring a **choose → start → allow** operation. It launches the original command-line program in the background, captures its output in a live log and lets you answer its prompts **without opening Konsole**. A separate Advanced area exposes the upstream flags and daemon controls when you need them.

> [!IMPORTANT]
> **Install Doubletake itself first.** This project is **not** the AirPlay implementation, is **not an official component of Doubletake**, and is **not affiliated with or maintained by its author**. All mirroring, discovery, pairing and media encoding are performed by the original [`omarroth/doubletake`](https://github.com/omarroth/doubletake) project. This archive includes **only the GUI**; no upstream binaries are bundled.

## Features

- **Get started:** enter a receiver IP or leave it blank for network discovery, choose an encoder, press **Start Mirroring**, and grant KDE screen-sharing permission if asked.
- **Encoder presets:** Automatic (default), NVIDIA NVENC (`-hwaccel nvenc`), Intel/AMD VAAPI (`-hwaccel vaapi`). Advanced mode also includes `openh264` and `none`.
- **First-time pairing**, **video-only mode**, **Stop**, and an always-visible **live log** with a save-to-file button.
- **Interactive prompt input** to answer a receiver selection or PIN/password request without an external terminal.
- **English and Italian** with a live language selector. All interface strings and messages are stored in editable UTF-8 JSON files under `translations/`.
- **Safe executable discovery:** remembers the chosen paths to `doubletake` and `doubletake-ctl`, including paths outside `$PATH` such as `/opt/apple/bin`.
- **Advanced mirroring:** FPS, bitrate, latency, video codec, UDP range, credentials backend/file, debug options and argument preview.
- **Daemon controls:** start `doubletake -daemonize`; run `doubletake-ctl status`, `discover`, `devices`, `connect`, `disconnect`, `mute`, `unmute` and `pin`.
- KDE Plasma `.desktop` launcher, local configuration, editable Python source, no pipx, no application-specific Python package build.

## 1. Prerequisites: install the original Doubletake

Original project: **[github.com/omarroth/doubletake](https://github.com/omarroth/doubletake)**  
Original documentation: **[upstream README](https://github.com/omarroth/doubletake#readme)**  
Original issue tracker: **[upstream issues](https://github.com/omarroth/doubletake/issues)** (for problems in the underlying AirPlay engine).

Doubletake is an AirPlay sender for Linux supporting X11 and Wayland with PipeWire/xdg-desktop-portal. According to the upstream README, building it requires **Go 1.23+**, **GStreamer 1.0** with the base/good/bad/ugly/libav plugin families, PulseAudio utilities (`pactl`) and either PipeWire or X11 screen capture. Refer to upstream for changes to these requirements.

### Ubuntu / Debian: upstream GStreamer dependencies

The following package list is taken from the [upstream installation documentation](https://github.com/omarroth/doubletake#requirements):

```bash
sudo apt install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly gstreamer1.0-libav pulseaudio-utils
```

Also ensure `git`, `make`, and **Go >= 1.23** are installed using your distribution's normal tools. Package names can vary across releases.

### Arch Linux: upstream GStreamer dependencies

```bash
sudo pacman -S gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad \
  gst-plugins-ugly gst-libav libpulse
```

Upstream also lists AUR packages named [`doubletake`](https://aur.archlinux.org/packages/doubletake), [`doubletake-git`](https://aur.archlinux.org/packages/doubletake-git) and [`doubletake-bin`](https://aur.archlinux.org/packages/doubletake-bin). If you install through a package manager, skip the source-build steps below and locate the installed executables in the GUI.

### Build and install Doubletake from its original repository

This example places the upstream binaries under `/opt/apple/bin`, matching the default discovery order of this GUI:

```bash
git clone https://github.com/omarroth/doubletake.git
cd doubletake
make
sudo install -d /opt/apple/bin
sudo make install PREFIX=/opt/apple
```

The original Makefile builds `bin/doubletake`, `bin/doubletake-ctl`, and `bin/doubletake-test-receiver`. The extra `install -d` above is deliberate: the upstream installation recipe expects `PREFIX/bin` to exist. The original `make install` also installs man pages under the selected prefix. If you prefer the upstream default installation prefix, use `sudo make install` instead (installs into `/usr/local`).

Verify the installation:

```bash
/opt/apple/bin/doubletake -h
/opt/apple/bin/doubletake-ctl -h
```

> Use the **upstream README as the authority** for current build requirements, options and compatibility. Doubletake also provides its own [KDE Plasma widget](https://github.com/omarroth/doubletake/tree/main/plasmoid); this standalone GUI is an alternative focused on a simple workflow and visible logs.

### Install PySide6 for your Python interpreter

This GUI needs **Python 3.10+** and **PySide6** in the Python interpreter that starts it. Prefer your Linux distribution's Python/PySide6 packages. Check the result:

```bash
python3 -c 'from PySide6.QtWidgets import QApplication; print("PySide6 OK")'
```

If PySide6 is installed in a different interpreter, set `PYTHON_BIN=/path/to/python` when running the launcher. This package itself is shipped as source in a `.tar.gz` archive; it does **not** ship Python wheels, an app bundle or a `pipx` installation process.

## 2. Install Doubletake GUI

Download the versioned `doubletake-gui-1.0.0.tar.gz` file from **this GUI project's** release page. From the directory containing the file:

```bash
sudo mkdir -p /opt/apple
sudo tar -xzf doubletake-gui-1.0.0.tar.gz -C /opt/apple
/opt/apple/doubletake-gui/run.sh
```

The archive always extracts to `doubletake-gui/`, so upgrades can be unpacked over earlier installations. Your configuration is stored in your home directory and is not removed when you replace `/opt/apple/doubletake-gui`.

To add the application to KDE Plasma's application launcher **for your user**, run without `sudo`:

```bash
/opt/apple/doubletake-gui/install-desktop.sh
```

For a custom Python interpreter:

```bash
PYTHON_BIN=/path/to/python3 /opt/apple/doubletake-gui/run.sh
```

The executable paths can be set under **Settings** and are never modified by this installer.

### Upgrade

Extract the new `.tar.gz` over `/opt/apple` using the same command. The `~/.config/doubletake-gui/config.ini` file remains untouched. It is good practice to close the GUI before upgrading its code. Re-run `install-desktop.sh` if you moved the directory.

### Remove the launcher or uninstall

```bash
/opt/apple/doubletake-gui/uninstall-desktop.sh
sudo rm -rf /opt/apple/doubletake-gui
```

The second command removes **only the GUI files**; it does not uninstall upstream Doubletake. To delete your saved GUI settings too, remove `~/.config/doubletake-gui/` manually **only if you no longer want them**. Avoid modifying `/opt/apple/bin` when uninstalling the GUI, since those binaries belong to the upstream installation.

## 3. Quick start: three steps

1. **Choose a TV:** enter its local IP address (for example `192.168.1.77`) or leave the field blank to let Doubletake discover receivers.
2. **Choose an encoder:** leave **Automatic** unless you know your GPU supports NVIDIA NVENC or Intel/AMD VAAPI through GStreamer.
3. **Press Start Mirroring:** if a KDE Wayland/portal dialog appears, select the display and approve sharing. Wait for the receiver to connect and check the live log for progress.

The **Stop** button terminates only the Doubletake process started by this GUI. The GUI does not close other independently running Doubletake sessions.

For a first-time PIN pairing, enter the receiver IP and press **First time? Pair with TV**. If the receiver uses a fixed password, enter it in the masked PIN/password field. For a prompt that appears after startup, type the response in the masked field below the log and press **Send**; a blank response can also be sent.

The easy mode intentionally ignores *other* advanced options such as FPS, bitrate and debug. It uses only the receiver IP, chosen encoder and optional credential, plus `-pair` or `-no-audio` if you chose those actions. This keeps normal use predictable.

### Commands behind the buttons

| Operation | Upstream command generated by the GUI |
| --- | --- |
| Auto-discover & stream | `doubletake` |
| Target a TV | `doubletake -target 192.168.1.77` |
| NVIDIA encoding | `doubletake -target 192.168.1.77 -hwaccel nvenc` |
| Intel / AMD encoding | `doubletake -target 192.168.1.77 -hwaccel vaapi` |
| Force pairing | `doubletake -target 192.168.1.77 -pair` |
| No audio | `doubletake -target 192.168.1.77 -no-audio` |
| Detailed diagnostics | `doubletake -target 192.168.1.77 -debug` |

The GPU choice is saved and shared with the Advanced tab. **Selecting an accelerator does not install drivers or GStreamer encoders.** Only the upstream `-hwaccel auto` selection attempts encoder fallback; explicit NVENC/VAAPI selections may fail if those GStreamer elements are unavailable.

## 4. Settings and executable discovery

By default settings are stored at:

```text
~/.config/doubletake-gui/config.ini
```

The XDG convention is honored when `$XDG_CONFIG_HOME` is set. See [`config.example.ini`](config.example.ini) for a readable example. Existing v2 settings keys, including `binaries/doubletake`, `binaries/doubletake_ctl`, `stream/target` and `stream/hw`, are preserved.

The built-in search looks for executables in `/opt/apple/bin`, nearby `bin/` directories, `~/.local/bin`, the user's `PATH`, `/usr/local/bin` and `/usr/bin`. It checks that a candidate is an executable file rather than assuming a path exists.

**Path safety guarantee:**

- A non-empty path manually entered or loaded from settings is **never overwritten** by Auto-detect, even if the path currently does not exist (e.g. a drive is not mounted).
- Auto-detect only fills an **empty** field, and only when it finds a real executable.
- To intentionally replace a stored path, choose **Browse** or clear its field and run Auto-detect, then save.
- `doubletake-ctl` is optional for the three-step experience; it is needed for the Daemon & control tab.

The **Verify paths** button checks the current fields without editing them.

## 5. Languages

Choose **English** or **Italiano** in the main window's top-right selector. Changes apply **immediately** and are saved for the next launch.

Translation files are plain UTF-8 JSON:

```text
translations/en.json
translations/it.json
```

Each file uses the same stable dotted keys. To update a translation, edit the corresponding JSON value. To add a new UI message, add the same key to both language catalogs and reference the key in the source using `self.t(...)` (or the UI binding helpers). **Raw output from the original Doubletake program is not translated**; it is displayed exactly as Doubletake prints it.

## 6. Advanced mode and daemon control

The **Advanced → Mirroring** tab includes optional upstream flags: `-fps`, `-bitrate`, `-target-latency-ms`, `-hwaccel`, `-video-codec`, `-port`, `-port-range`, `-creds`, `-cred-backend`, `-pair`, `-no-audio`, `-test`, `-no-encrypt`, `-direct-key`, and `-debug`. The **generated command preview** deliberately omits PINs/passwords. Additional flags can be supplied as separate shell-style arguments, but the application runs Doubletake via `QProcess` without invoking a shell.

The **Advanced → Daemon & control** tab can start `doubletake -daemonize` and send documented `doubletake-ctl` subcommands. Use **Status**, **Discover**, **Devices**, **Connect**, **Disconnect**, **Mute**, **Unmute**, and **Send PIN** as needed. The actual daemon socket and multi-target behavior are provided by upstream. For details, consult the upstream [daemon control documentation](https://github.com/omarroth/doubletake#daemon-control-doubletake-ctl).

**Security and credentials:** the normal mirroring PIN/password is passed to the spawned process through its `DOUBLETAKE_CODE` environment variable, not through argv, and is not persisted in the GUI configuration. This is the method recommended by the upstream README. The GUI's prompt input is masked and its response is not echoed in the GUI log. However, **`doubletake-ctl connect TARGET PASSWORD` and `doubletake-ctl pin PASSWORD` accept the secret as a command-line argument in the upstream interface**; it may be visible to system tools such as `ps`. The GUI masks the corresponding log entry but cannot eliminate that upstream exposure. As with any log, verbose Doubletake debug output may include protocol data; review saved logs before sharing them.

## 7. Troubleshooting

| Problem | What to check |
| --- | --- |
| `doubletake` cannot be found | In **Settings**, use Browse to select the real executable (for example `/opt/apple/bin/doubletake`). Auto-detect will not override a previously entered path. |
| Nothing appears on the TV | Confirm that sender and receiver are reachable on the same local network and AirPlay is enabled. Try a known receiver IP instead of discovery. Check upstream's troubleshooting/issues. |
| KDE asks for permission | On Wayland, approve the PipeWire / xdg-desktop-portal screen-sharing dialog and select a display. |
| NVENC / VAAPI fails | Try Automatic. Confirm that the GStreamer encoder is installed and can be inspected using `gst-inspect-1.0` as described by upstream. |
| PIN / password rejected | Check whether the receiver wants a transient pairing PIN or a fixed AirPlay password. See [upstream authentication instructions](https://github.com/omarroth/doubletake#password-protected-receivers). |
| Video works but audio fails | Try **Audio issues? Try video only**. Doubletake depends on receiver capabilities and host audio plugins. |
| Receiver not visible on a restricted firewall | Consult [upstream's firewall guidance](https://github.com/omarroth/doubletake#firewall) regarding the `-port-range` option; no internet port forwarding is required. |
| No PySide6 available | Verify which interpreter `run.sh` uses and install PySide6 for that Python; override it with `PYTHON_BIN` if needed. |

For bugs in the GUI or translations, report them to the **GUI project's** repository. For AirPlay protocol, codecs, receiver compatibility and pairing problems, first consult the **[main Doubletake project](https://github.com/omarroth/doubletake)**.

## 8. Development and tests

The entire GUI is open Python source with just the PySide6 runtime dependency. Tests that do not require Qt can be run from the project folder:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile app.py i18n.py binary_paths.py
```

A Qt smoke test can run headlessly with PySide6 using `QT_QPA_PLATFORM=offscreen python3 tests/smoke_gui.py`; the included GitHub Actions workflow runs this check. Tests cover executable path preservation, generated quick-start arguments, UDP ranges and translation catalog consistency. No bundled Doubletake binary or receiver is used in tests.

To package a release from a source checkout (from the parent folder):

```bash
tar -czf doubletake-gui-1.0.0.tar.gz doubletake-gui/
sha256sum doubletake-gui-1.0.0.tar.gz
```

## 9. Licensing, credits and attribution

**Doubletake GUI** (this separate frontend) is distributed under the **GNU Lesser General Public License v3.0 or later** (`LGPL-3.0-or-later`). The archive contains `LICENSE` (LGPLv3) and `COPYING.GPL` (the GPLv3 terms incorporated by LGPLv3). See [LICENSE](LICENSE) and [COPYING.GPL](COPYING.GPL) for the full license texts. The GUI includes its own icon and translation catalogs.

**Upstream Doubletake**, by **[omarroth](https://github.com/omarroth)** and its contributors, is a different project: [omarroth/doubletake](https://github.com/omarroth/doubletake). Its current main branch states `LGPL-3.0-or-later` (earlier releases used `GPL-3.0-or-later`); refer to **upstream's own license and version** for the precise terms of your Doubletake installation. No portion of upstream's source or executable is included in this GUI's release package.

This project is **unofficial**. Naming Doubletake and linking to its project is attribution and interoperability information, **not** an endorsement or an indication of affiliation.

---

**Upstream project:** https://github.com/omarroth/doubletake  
**This project's role:** a standalone, optional graphical controller that runs the existing Doubletake executables.
