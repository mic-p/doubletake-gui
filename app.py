#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Unofficial PySide6 GUI for omarroth/doubletake. No terminal required."""
from __future__ import annotations

import os
import re
import shlex
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QProcess, QProcessEnvironment, QSettings, Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QSpinBox, QTabWidget,
    QVBoxLayout, QWidget,
)

from binary_paths import detect_only_if_empty, executable_path, find_binary
from i18n import Translator

APP_DIR = Path(__file__).resolve().parent
ICON = APP_DIR / 'icons' / 'doubletake-gui.png'
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'doubletake-gui' / 'config.ini'
PORT_RANGE_RE = re.compile(r'^(\d{1,5})-(\d{1,5})$')
VERSION = '1.0.0'


def validate_port_range(raw: str) -> None:
    """Raise ValueError with a stable translation key on an invalid UDP range."""
    if not raw:
        return
    match = PORT_RANGE_RE.fullmatch(raw)
    if not match:
        raise ValueError('error.udp_format')
    low, high = map(int, match.groups())
    if not (1 <= low <= high <= 65535 and high - low >= 2):
        raise ValueError('error.udp_bounds')


def field() -> QLineEdit:
    edit = QLineEdit()
    edit.setClearButtonEnabled(True)
    return edit


def spin(low: int, high: int, default: int) -> QSpinBox:
    widget = QSpinBox()
    widget.setRange(low, high)
    widget.setValue(default)
    return widget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        self.cfg = QSettings(str(CONFIG), QSettings.Format.IniFormat)
        self.locale = Translator(str(self.cfg.value('ui/language', 'en')))
        self.bindings: list[tuple[callable, str]] = []
        self._hint_key = 'hint.ready'
        self._stream_mode = 'mirror'
        self._stop_requested = False
        self.stream = QProcess(self)
        self.stream.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.stream.readyReadStandardOutput.connect(lambda: self.read_output(self.stream))
        self.stream.started.connect(self.stream_started)
        self.stream.finished.connect(self.stream_finished)
        self.stream.errorOccurred.connect(lambda error: self.process_error('doubletake', self.stream, error))
        self.ctl = QProcess(self)
        self.ctl.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.ctl.readyReadStandardOutput.connect(lambda: self.read_output(self.ctl))
        self.ctl.finished.connect(self.ctl_finished)
        self.ctl.errorOccurred.connect(lambda error: self.process_error('doubletake-ctl', self.ctl, error))
        self.setWindowIcon(QIcon(str(ICON)))
        self.setWindowTitle('Doubletake GUI')
        self.resize(940, 825)
        self.setMinimumSize(690, 600)
        self.build_ui()
        self.restore_config()
        self.refresh_preview()
        self.refresh_status()
        self.log(self.t('log.ready', version=VERSION))
        self.log(self.t('log.config', path=str(CONFIG)))
        self.check_paths(silent=True)

    def t(self, key: str, **kwargs) -> str:
        return self.locale.t(key, **kwargs)

    def bind(self, setter, key: str) -> None:
        """Register a translatable widget property for live language switching."""
        self.bindings.append((setter, key))
        setter(self.t(key))

    def label(self, key: str, *, name: str = '', wrap: bool = False) -> QLabel:
        item = QLabel()
        self.bind(item.setText, key)
        if name:
            item.setObjectName(name)
        item.setWordWrap(wrap)
        return item

    def button(self, key: str, callback, *, role: str = '') -> QPushButton:
        widget = QPushButton()
        self.bind(widget.setText, key)
        widget.clicked.connect(callback)
        if role:
            widget.setProperty('role', role)
        return widget

    def group(self, key: str) -> QGroupBox:
        widget = QGroupBox()
        self.bind(widget.setTitle, key)
        return widget

    def entry(self, key: str, *, secret: bool = False) -> QLineEdit:
        widget = field()
        self.bind(widget.setPlaceholderText, key)
        if secret:
            widget.setEchoMode(QLineEdit.EchoMode.Password)
        return widget

    def tab(self, tabs: QTabWidget, widget: QWidget, key: str) -> None:
        index = tabs.addTab(widget, self.t(key))
        self.bind(lambda value, t=tabs, i=index: t.setTabText(i, value), key)

    def combo_item(self, combo: QComboBox, key: str, data: str) -> None:
        index = combo.count()
        combo.addItem(self.t(key), data)
        self.bind(lambda value, c=combo, i=index: c.setItemText(i, value), key)

    def form_row(self, form: QFormLayout, key: str, widget) -> None:
        form.addRow(self.label(key), widget)

    def hint(self, key: str) -> None:
        self._hint_key = key
        self.easy_hint.setText(self.t(key))

    def change_language(self, index: int) -> None:
        language = self.language.currentData()
        if not language or language == self.locale.language:
            return
        self.locale.set_language(language)
        self.cfg.setValue('ui/language', language)
        self.cfg.sync()
        for setter, key in self.bindings:
            setter(self.t(key))
        self.hint(self._hint_key)
        self.refresh_status()
        self.refresh_preview()
        self.log(self.t('log.language'))

    def page(self) -> tuple[QScrollArea, QVBoxLayout]:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(11)
        scroll.setWidget(body)
        return scroll, layout

    def form_group(self, key: str) -> tuple[QGroupBox, QFormLayout]:
        box = self.group(key)
        form = QFormLayout(box)
        form.setSpacing(9)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        return box, form

    def build_ui(self) -> None:
        outer = QWidget()
        self.setCentralWidget(outer)
        root = QVBoxLayout(outer)
        root.setContentsMargins(18, 15, 18, 14)
        root.setSpacing(10)
        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(QIcon(str(ICON)).pixmap(54, 54))
        header.addWidget(icon)
        title_col = QVBoxLayout()
        title_col.addWidget(self.label('title.app', name='heading'))
        title_col.addWidget(self.label('title.subtitle', name='muted'))
        header.addLayout(title_col)
        header.addStretch()
        header.addWidget(self.label('label.language'))
        self.language = QComboBox()
        self.language.addItem('English', 'en')
        self.language.addItem('Italiano', 'it')
        self.language.setCurrentIndex(self.language.findData(self.locale.language))
        self.language.currentIndexChanged.connect(self.change_language)
        header.addWidget(self.language)
        self.status_label = QLabel()
        self.status_label.setObjectName('status')
        header.addWidget(self.status_label)
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.tab(self.tabs, self.build_easy_tab(), 'tab.easy')
        self.tab(self.tabs, self.build_settings_tab(), 'tab.settings')
        advanced = QTabWidget()
        self.tab(advanced, self.build_mirror_tab(), 'tab.mirror')
        self.tab(advanced, self.build_daemon_tab(), 'tab.daemon')
        self.tab(self.tabs, advanced, 'tab.advanced')
        self.easy_target.textChanged.connect(self.sync_easy_target)
        self.target.textChanged.connect(self.sync_advanced_target)
        self.easy_encoder.currentIndexChanged.connect(self.sync_easy_encoder)
        self.hw.currentIndexChanged.connect(self.sync_advanced_encoder)
        self.easy_code.textChanged.connect(self.sync_easy_code)
        self.code.textChanged.connect(self.sync_advanced_code)
        root.addWidget(self.tabs, 7)

        log_header = QHBoxLayout()
        log_header.addWidget(self.label('label.output'))
        log_header.addStretch()
        log_header.addWidget(self.button('button.clear', lambda: self.output.clear()))
        log_header.addWidget(self.button('button.save_log', self.save_log))
        root.addLayout(log_header)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName('logview')
        self.output.document().setMaximumBlockCount(4000)
        self.output.setMinimumHeight(130)
        font = QFont('monospace')
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(10)
        self.output.setFont(font)
        root.addWidget(self.output, 3)
        stdin_row = QHBoxLayout()
        stdin_row.addWidget(self.label('label.prompt'))
        self.stdin_entry = self.entry('placeholder.stdin', secret=True)
        self.stdin_entry.returnPressed.connect(self.send_input)
        stdin_row.addWidget(self.stdin_entry, 1)
        stdin_row.addWidget(self.button('button.send', self.send_input))
        root.addLayout(stdin_row)
        self.setStyleSheet('''
            QMainWindow, QWidget { background: #171b26; color: #e6eaf5; }
            QTabWidget::pane, QGroupBox { border: 1px solid #353e55; border-radius: 9px; }
            QTabWidget::pane { background: #1d2331; }
            QTabBar::tab { background: #242b3d; color: #c4cee2; padding: 10px 16px;
                border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 4px; }
            QTabBar::tab:selected { background: #314461; color: white; }
            QGroupBox { margin-top: 13px; padding: 12px; font-weight: 600; }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 5px; color: #b4d6ff; }
            QLineEdit, QSpinBox, QComboBox, QPlainTextEdit { border: 1px solid #414b62;
                background: #111722; border-radius: 6px; padding: 7px; selection-background-color: #2776ab; }
            QComboBox::drop-down { border: 0; width: 22px; }
            QPushButton { background: #303d54; border: 1px solid #50607b;
                border-radius: 7px; padding: 9px 13px; font-weight: 500; }
            QPushButton:hover { background: #405270; }
            QPushButton:pressed { background: #25344c; }
            QPushButton:disabled { color: #818b9d; background: #252c3c; }
            QPushButton[role="primary"] { background: #096d92; border-color: #25a6bd; color: white; }
            QPushButton[role="danger"] { background: #63333d; border-color: #99525d; }
            QPushButton#bigaction { background: #07769c; border: 1px solid #42c2d9;
                border-radius: 12px; color: white; font-size: 18px; font-weight: 700; padding: 16px 19px; }
            QPushButton#bigaction:disabled { background: #344256; border-color: #536078; }
            QLabel#heading { font-size: 23px; font-weight: 700; color: #f4f8ff; }
            QLabel#muted, QLabel#helper { color: #a2b0cb; }
            QLabel#status { background: #2b374d; border-radius: 11px;
                padding: 7px 11px; font-weight: 700; color: #9fe1f0; }
            QLabel#hint { background: #26354a; color: #d4effa;
                border-radius: 9px; padding: 11px; }
            QPlainTextEdit#logview { background: #0d131d; color: #c6e3e4; }
            QScrollArea { border: 0; background: transparent; }
        ''')

    def build_easy_tab(self) -> QWidget:
        page, layout = self.page()
        layout.addWidget(self.label('easy.heading', name='heading'))
        layout.addWidget(self.label('easy.intro', name='helper', wrap=True))
        receiver = self.group('easy.step1')
        receive_layout = QVBoxLayout(receiver)
        self.easy_target = self.entry('placeholder.easy_target')
        receive_layout.addWidget(self.easy_target)
        receive_layout.addWidget(self.label('easy.target_help', name='helper', wrap=True))
        layout.addWidget(receiver)
        encoder = self.group('easy.step2')
        encoder_layout = QVBoxLayout(encoder)
        self.easy_encoder = QComboBox()
        for key, data in [
            ('encoder.auto', 'auto'), ('encoder.nvenc', 'nvenc'),
            ('encoder.vaapi', 'vaapi'), ('encoder.custom', 'custom'),
        ]:
            self.combo_item(self.easy_encoder, key, data)
        encoder_layout.addWidget(self.easy_encoder)
        encoder_layout.addWidget(self.label('easy.encoder_help', name='helper', wrap=True))
        layout.addWidget(encoder)
        action = self.group('easy.step3')
        action_layout = QVBoxLayout(action)
        self.easy_code = self.entry('placeholder.code', secret=True)
        action_layout.addWidget(self.easy_code)
        buttons = QHBoxLayout()
        self.easy_start_button = self.button('button.start', self.easy_start)
        self.easy_start_button.setObjectName('bigaction')
        buttons.addWidget(self.easy_start_button, 3)
        self.easy_stop_button = self.button('button.stop', self.stop_stream, role='danger')
        buttons.addWidget(self.easy_stop_button, 1)
        action_layout.addLayout(buttons)
        self.easy_hint = QLabel()
        self.easy_hint.setObjectName('hint')
        self.easy_hint.setWordWrap(True)
        self.hint('hint.ready')
        action_layout.addWidget(self.easy_hint)
        helpers = QHBoxLayout()
        self.easy_pair_button = self.button('button.pair', self.easy_pair)
        helpers.addWidget(self.easy_pair_button)
        self.easy_video_button = self.button('button.video', lambda: self.easy_start(video_only=True))
        helpers.addWidget(self.easy_video_button)
        action_layout.addLayout(helpers)
        layout.addWidget(action)
        layout.addStretch()
        return page

    def build_settings_tab(self) -> QWidget:
        page, layout = self.page()
        box, form = self.form_group('settings.paths')
        self.binary = self.entry('placeholder.binary')
        self.ctl_binary = self.entry('placeholder.ctl_binary')
        for name, edit in [('doubletake', self.binary), ('doubletake-ctl', self.ctl_binary)]:
            wrap = QWidget()
            row = QHBoxLayout(wrap)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(edit, 1)
            row.addWidget(self.button('button.browse', lambda checked=False, e=edit: self.browse_binary(e)))
            form.addRow(QLabel(name), wrap)
        controls = QHBoxLayout()
        controls.addWidget(self.button('button.find_empty', self.auto_detect))
        controls.addWidget(self.button('button.verify', lambda: self.check_paths(silent=False)))
        controls.addWidget(self.button('button.save', self.save_config, role='primary'))
        form.addRow(controls)
        layout.addWidget(box)
        about = self.group('settings.info')
        about_layout = QVBoxLayout(about)
        info = self.label('settings.info_text', name='helper', wrap=True)
        info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        about_layout.addWidget(info)
        location = QLabel(f'{APP_DIR}\n{CONFIG}')
        location.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        about_layout.addWidget(location)
        link = self.label('settings.upstream', name='helper', wrap=True)
        link.setTextFormat(Qt.TextFormat.RichText)
        link.setOpenExternalLinks(True)
        about_layout.addWidget(link)
        layout.addWidget(about)
        layout.addStretch()
        return page

    def build_mirror_tab(self) -> QWidget:
        page, layout = self.page()
        actions = self.group('advanced.presets')
        row = QHBoxLayout(actions)
        for key, callback in [
            ('button.automatic', lambda: self.start_stream([])),
            ('button.video_short', lambda: self.start_stream(self.target_args() + ['-no-audio'])),
            ('button.pair_short', self.easy_pair),
            ('button.debug', lambda: self.start_stream(self.target_args() + ['-debug'])),
        ]:
            row.addWidget(self.button(key, callback))
        layout.addWidget(actions)
        basic, form = self.form_group('advanced.main')
        self.target = self.entry('placeholder.target')
        self.form_row(form, 'label.target', self.target)
        self.code = self.entry('placeholder.code', secret=True)
        self.form_row(form, 'label.code', self.code)
        flags = QWidget()
        checks = QHBoxLayout(flags)
        checks.setContentsMargins(0, 0, 0, 0)
        self.pair = QCheckBox()
        self.no_audio = QCheckBox()
        self.debug = QCheckBox()
        for widget, key in [(self.pair, 'flag.pair'), (self.no_audio, 'flag.no_audio'), (self.debug, 'flag.debug')]:
            self.bind(widget.setText, key)
            checks.addWidget(widget)
        checks.addStretch()
        self.form_row(form, 'label.quick_flags', flags)
        layout.addWidget(basic)

        advanced, settings = self.form_group('advanced.encoder')
        video = QWidget()
        vrow = QHBoxLayout(video)
        vrow.setContentsMargins(0, 0, 0, 0)
        self.fps = spin(1, 240, 30)
        self.bitrate = spin(0, 200000, 0)
        self.latency = spin(0, 10000, 0)
        for key, widget in [('label.fps', self.fps), ('label.bitrate', self.bitrate), ('label.latency', self.latency)]:
            vrow.addWidget(self.label(key))
            vrow.addWidget(widget, 1)
        self.form_row(settings, 'label.video', video)
        codecs = QWidget()
        crow = QHBoxLayout(codecs)
        crow.setContentsMargins(0, 0, 0, 0)
        self.hw = QComboBox()
        self.hw.addItems(['auto', 'nvenc', 'vaapi', 'openh264', 'none'])
        self.codec = QComboBox()
        self.codec.addItems(['auto', 'h264', 'hevc'])
        self.airplay_port = spin(1, 65535, 7000)
        for key, widget in [('label.encoder', self.hw), ('label.codec', self.codec), ('label.port', self.airplay_port)]:
            crow.addWidget(self.label(key))
            crow.addWidget(widget, 1)
        self.form_row(settings, 'label.codec_network', codecs)
        self.ports = self.entry('placeholder.udp')
        self.form_row(settings, 'label.udp', self.ports)
        creds = QWidget()
        c_row = QHBoxLayout(creds)
        c_row.setContentsMargins(0, 0, 0, 0)
        self.credentials = self.entry('placeholder.creds')
        c_row.addWidget(self.credentials, 1)
        c_row.addWidget(self.button('button.browse', self.browse_creds))
        self.form_row(settings, 'label.creds', creds)
        self.cred_backend = QComboBox()
        self.cred_backend.addItems(['file', 'keyring'])
        self.form_row(settings, 'label.cred_backend', self.cred_backend)
        flags = QWidget()
        row = QHBoxLayout(flags)
        row.setContentsMargins(0, 0, 0, 0)
        self.test = QCheckBox()
        self.no_encrypt = QCheckBox()
        self.direct_key = QCheckBox()
        for widget, key in [(self.test, 'flag.test'), (self.no_encrypt, 'flag.no_encrypt'), (self.direct_key, 'flag.direct_key')]:
            self.bind(widget.setText, key)
            row.addWidget(widget)
        row.addStretch()
        self.form_row(settings, 'label.diagnostics', flags)
        self.extra = self.entry('placeholder.extra')
        self.form_row(settings, 'label.extra', self.extra)
        layout.addWidget(advanced)
        preview = self.group('advanced.command')
        command_layout = QVBoxLayout(preview)
        self.preview = QLineEdit()
        self.preview.setReadOnly(True)
        command_layout.addWidget(self.preview)
        controls = QHBoxLayout()
        self.start_custom = self.button('button.start_custom', self.start_custom_stream, role='primary')
        controls.addWidget(self.start_custom)
        self.stop_button = self.button('button.stop_process', self.stop_stream, role='danger')
        controls.addWidget(self.stop_button)
        controls.addWidget(self.button('button.copy', lambda: QApplication.clipboard().setText(self.preview.text())))
        command_layout.addLayout(controls)
        layout.addWidget(preview)
        layout.addStretch()
        for widget in (self.target, self.ports, self.credentials, self.extra):
            widget.textChanged.connect(self.refresh_preview)
        for widget in (self.fps, self.bitrate, self.latency, self.airplay_port):
            widget.valueChanged.connect(self.refresh_preview)
        for widget in (self.hw, self.codec, self.cred_backend):
            widget.currentIndexChanged.connect(self.refresh_preview)
        for widget in (self.pair, self.no_audio, self.debug, self.test, self.no_encrypt, self.direct_key):
            widget.toggled.connect(self.refresh_preview)
        return page

    def build_daemon_tab(self) -> QWidget:
        page, layout = self.page()
        layout.addWidget(self.label('daemon.intro', name='helper', wrap=True))
        daemon, form = self.form_group('daemon.launch')
        self.daemon_ports = self.entry('placeholder.daemon_ports')
        self.form_row(form, 'label.udp', self.daemon_ports)
        self.daemon_socket = self.entry('placeholder.daemon_socket')
        self.form_row(form, 'label.socket', self.daemon_socket)
        row = QHBoxLayout()
        row.addWidget(self.button('button.start_daemon', self.start_daemon, role='primary'))
        row.addWidget(self.button('button.stop_owned', self.stop_stream, role='danger'))
        form.addRow(row)
        layout.addWidget(daemon)
        commands, form = self.form_group('daemon.commands')
        self.ctl_target = self.entry('placeholder.ctl_target')
        self.form_row(form, 'label.target', self.ctl_target)
        self.ctl_code = self.entry('placeholder.ctl_code', secret=True)
        self.form_row(form, 'label.code', self.ctl_code)
        self.ctl_socket = self.entry('placeholder.ctl_socket')
        self.form_row(form, 'label.socket', self.ctl_socket)
        row = QHBoxLayout()
        for key, command in [('button.status', 'status'), ('button.discover', 'discover'), ('button.devices', 'devices')]:
            row.addWidget(self.button(key, lambda checked=False, c=command: self.run_ctl(c)))
        form.addRow(row)
        grid = QGridLayout()
        ctl_buttons = [
            ('button.connect', self.connect_ctl),
            ('button.disconnect', lambda: self.run_ctl('disconnect', need_target=True)),
            ('button.disconnect_all', lambda: self.run_ctl('disconnect', all_targets=True)),
            ('button.mute', lambda: self.run_ctl('mute')),
            ('button.unmute', lambda: self.run_ctl('unmute')),
            ('button.pin', self.pin_ctl),
        ]
        for i, (key, callback) in enumerate(ctl_buttons):
            grid.addWidget(self.button(key, callback), i // 3, i % 3)
        form.addRow(grid)
        layout.addWidget(commands)
        layout.addWidget(self.label('daemon.warning', name='helper', wrap=True))
        layout.addStretch()
        return page

    def sync_easy_target(self, value: str) -> None:
        if self.target.text() != value:
            self.target.setText(value)

    def sync_advanced_target(self, value: str) -> None:
        if self.easy_target.text() != value:
            self.easy_target.setText(value)

    def sync_easy_encoder(self, _index: int) -> None:
        key = self.easy_encoder.currentData()
        if key == 'custom':
            if self.hw.currentText() in ('auto', 'nvenc', 'vaapi'):
                self.easy_encoder.setCurrentIndex(self.easy_encoder.findData(self.hw.currentText()))
            return
        if self.hw.currentText() != key:
            self.hw.setCurrentText(key)

    def sync_advanced_encoder(self, _index: int) -> None:
        key = self.hw.currentText()
        index = self.easy_encoder.findData(key)
        if index < 0:
            index = self.easy_encoder.findData('custom')
        if self.easy_encoder.currentIndex() != index:
            self.easy_encoder.setCurrentIndex(index)
        self.cfg.setValue('stream/hw', key)
        self.cfg.sync()

    def sync_easy_code(self, value: str) -> None:
        if self.code.text() != value:
            self.code.setText(value)

    def sync_advanced_code(self, value: str) -> None:
        if self.easy_code.text() != value:
            self.easy_code.setText(value)

    def target_args(self, required: bool = False) -> list[str]:
        target = self.target.text().strip()
        if required and not target:
            raise ValueError('error.target_required')
        return ['-target', target] if target else []

    def easy_args(self, *, pair: bool = False, video_only: bool = False) -> list[str]:
        args = self.target_args(required=pair)
        if pair:
            args.append('-pair')
        if video_only:
            args.append('-no-audio')
        hw = self.hw.currentText()
        if hw != 'auto':
            args.extend(['-hwaccel', hw])
        return args

    def easy_start(self, *unused, video_only: bool = False) -> None:
        try:
            self.start_stream(self.easy_args(video_only=video_only))
        except ValueError as error:
            self.fail(str(error))

    def easy_pair(self) -> None:
        try:
            self.start_stream(self.easy_args(pair=True))
        except ValueError as error:
            self.fail(str(error))

    def custom_args(self) -> list[str]:
        args = self.target_args()
        for checkbox, flag in [
            (self.pair, '-pair'), (self.no_audio, '-no-audio'),
            (self.debug, '-debug'), (self.test, '-test'),
            (self.no_encrypt, '-no-encrypt'), (self.direct_key, '-direct-key'),
        ]:
            if checkbox.isChecked():
                args.append(flag)
        for widget, default, flag in [
            (self.fps, 30, '-fps'), (self.bitrate, 0, '-bitrate'),
            (self.latency, 0, '-target-latency-ms'), (self.airplay_port, 7000, '-port'),
        ]:
            if widget.value() != default:
                args.extend([flag, str(widget.value())])
        if self.hw.currentText() != 'auto':
            args.extend(['-hwaccel', self.hw.currentText()])
        if self.codec.currentText() != 'auto':
            args.extend(['-video-codec', self.codec.currentText()])
        ports = self.ports.text().strip()
        validate_port_range(ports)
        if ports:
            args.extend(['-port-range', ports])
        if self.credentials.text().strip():
            args.extend(['-creds', os.path.expanduser(self.credentials.text().strip())])
        if self.cred_backend.currentText() != 'file':
            args.extend(['-cred-backend', self.cred_backend.currentText()])
        if self.extra.text().strip():
            try:
                extras = shlex.split(self.extra.text())
            except ValueError:
                raise ValueError('error.extra_quotes') from None
            if any(value in ('-code', '--code') or value.startswith(('-code=', '--code=')) for value in extras):
                raise ValueError('error.no_code_arg')
            args.extend(extras)
        return args

    def refresh_preview(self, *unused) -> None:
        try:
            self.preview.setText(shlex.join(['doubletake'] + self.custom_args()))
        except ValueError as error:
            self.preview.setText(self.t('error.preview', reason=self.t(str(error))))

    def resolved_executable(self, widget: QLineEdit, name: str) -> str:
        raw = widget.text().strip()
        value = executable_path(raw)
        if not value:
            raise ValueError(self.t('error.binary', name=name, path=raw or self.t('label.empty')))
        return value

    def launch(self, process: QProcess, name: str, path: str, args: list[str],
               code: str = '', *, ctl_credential: bool = False) -> bool:
        if process.state() != QProcess.ProcessState.NotRunning:
            self.log(self.t('log.busy', name=name), warning=True)
            return False
        env = QProcessEnvironment.systemEnvironment()
        if code and not ctl_credential:
            env.insert('DOUBLETAKE_CODE', code)
        process.setProcessEnvironment(env)
        process.setProgram(path)
        process.setArguments(args)
        shown = list(args)
        if ctl_credential and code:
            shown[-1] = '********'
        self.log('$ ' + shlex.join([path] + shown))
        if code and not ctl_credential:
            self.log(self.t('log.env_code'))
        process.start()
        return True

    def start_stream(self, args: list[str]) -> None:
        try:
            path = self.resolved_executable(self.binary, 'doubletake')
            if self.stream.state() != QProcess.ProcessState.NotRunning:
                self.log(self.t('log.stream_busy'), warning=True)
                return
            self._stream_mode = 'mirror'
            self._stop_requested = False
            if self.launch(self.stream, 'doubletake', path, args, self.code.text()):
                self.code.clear()
                self.hint('hint.starting')
                self.refresh_status()
        except ValueError as error:
            self.fail(str(error))

    def start_custom_stream(self) -> None:
        try:
            self.start_stream(self.custom_args())
        except ValueError as error:
            self.fail(str(error))

    def start_daemon(self) -> None:
        try:
            path = self.resolved_executable(self.binary, 'doubletake')
            args = ['-daemonize']
            ports = self.daemon_ports.text().strip()
            validate_port_range(ports)
            if ports:
                args += ['-port-range', ports]
            if self.daemon_socket.text().strip():
                args += ['-socket', os.path.expanduser(self.daemon_socket.text().strip())]
            if self.stream.state() != QProcess.ProcessState.NotRunning:
                self.log(self.t('log.stream_busy'), warning=True)
                return
            self._stream_mode = 'daemon'
            self._stop_requested = False
            if self.launch(self.stream, 'daemon', path, args):
                self.refresh_status()
        except ValueError as error:
            self.fail(str(error))

    def stop_stream(self) -> None:
        if self.stream.state() == QProcess.ProcessState.NotRunning:
            self.log(self.t('log.no_running'))
            return
        self._stop_requested = True
        self.hint('hint.stopping')
        self.log(self.t('log.sigterm'))
        pid = self.stream.processId()
        self.stream.terminate()
        # Do not accidentally kill a new session if the old one ended quickly.
        QTimer.singleShot(2500, lambda old_pid=pid: self.force_stop(old_pid))

    def force_stop(self, old_pid: int) -> None:
        if (self.stream.state() != QProcess.ProcessState.NotRunning
                and self.stream.processId() == old_pid):
            self.log(self.t('log.sigkill'), warning=True)
            self.stream.kill()

    def run_ctl(self, command: str, *, need_target: bool = False, all_targets: bool = False,
                code: str = '') -> None:
        try:
            path = self.resolved_executable(self.ctl_binary, 'doubletake-ctl')
            target = self.ctl_target.text().strip()
            if need_target and not target:
                raise ValueError('error.ctl_target')
            args = []
            if self.ctl_socket.text().strip():
                args += ['-socket', os.path.expanduser(self.ctl_socket.text().strip())]
            args.append(command)
            if command in ('connect', 'disconnect', 'mute', 'unmute') and target and not all_targets:
                args.append(target)
            if command == 'connect' and code:
                if not target:
                    raise ValueError('error.ctl_connect_target')
                args.append(code)
            if command == 'pin' and code:
                args.append(code)
            if self.launch(self.ctl, 'doubletake-ctl', path, args, code, ctl_credential=bool(code)):
                self.ctl_code.clear()
        except ValueError as error:
            self.fail(str(error))

    def connect_ctl(self) -> None:
        self.run_ctl('connect', code=self.ctl_code.text())

    def pin_ctl(self) -> None:
        if not self.ctl_code.text():
            self.fail('error.pin_required')
            return
        self.run_ctl('pin', code=self.ctl_code.text())

    def send_input(self) -> None:
        if self.stream.state() != QProcess.ProcessState.Running:
            self.fail('error.no_prompt')
            return
        value = self.stdin_entry.text()
        self.stream.write((value + '\n').encode('utf-8'))
        self.log(self.t('log.stdin_sent'))
        self.stdin_entry.clear()

    def read_output(self, process: QProcess) -> None:
        data = bytes(process.readAllStandardOutput()).decode('utf-8', errors='replace')
        if data:
            self.output.moveCursor(QTextCursor.MoveOperation.End)
            self.output.insertPlainText(data)
            scrollbar = self.output.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def stream_started(self) -> None:
        self.log(self.t('log.process_started', pid=self.stream.processId(), mode=self._stream_mode))
        if self._stream_mode == 'mirror':
            self.hint('hint.running')
        self.refresh_status()

    def stream_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        self.read_output(self.stream)
        self.log(self.t('log.process_finished', name='doubletake', code=code, status=status.name))
        self.hint('hint.stopped' if self._stop_requested or code == 0 else 'hint.failed')
        self._stop_requested = False
        self.refresh_status()

    def ctl_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        self.read_output(self.ctl)
        self.log(self.t('log.process_finished', name='doubletake-ctl', code=code, status=status.name))
        self.refresh_status()

    def process_error(self, name: str, process: QProcess, error: QProcess.ProcessError) -> None:
        self.log(self.t('log.process_error', name=name, error=process.errorString(), kind=error.name), warning=True)
        if process is self.stream:
            self.hint('hint.failed')
        self.refresh_status()

    def refresh_status(self) -> None:
        busy = self.stream.state() != QProcess.ProcessState.NotRunning
        self.status_label.setText('● ' + self.t('status.daemon' if busy and self._stream_mode == 'daemon'
                                                else 'status.running' if busy else 'status.ready'))
        for widget in (self.easy_stop_button, self.stop_button):
            widget.setEnabled(busy)
        for widget in (self.easy_start_button, self.easy_pair_button, self.easy_video_button, self.start_custom):
            widget.setEnabled(not busy)

    def log(self, message: str, warning: bool = False) -> None:
        stamp = datetime.now().strftime('%H:%M:%S')
        mark = self.t('log.warning') if warning else ''
        self.output.appendPlainText(f'[{stamp}] {mark}{message}')
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def fail(self, key_or_text: str) -> None:
        message = self.t(key_or_text)
        self.log(message, warning=True)
        QMessageBox.warning(self, 'Doubletake GUI', message)

    def save_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, self.t('dialog.save_log'),
                                              str(Path.home() / 'doubletake-gui.log'),
                                              self.t('dialog.text_files'))
        if path:
            try:
                Path(path).write_text(self.output.toPlainText(), encoding='utf-8')
                self.log(self.t('log.saved_log', path=path))
            except OSError as error:
                self.fail(self.t('error.save_log', error=error))

    def browse_creds(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, self.t('dialog.creds'), str(Path.home()))
        if path:
            self.credentials.setText(path)

    def browse_binary(self, edit: QLineEdit) -> None:
        raw = edit.text().strip() or '/opt/apple/bin'
        candidate = Path(os.path.expandvars(os.path.expanduser(raw)))
        folder = candidate if candidate.is_dir() else candidate.parent
        while not folder.exists() and folder != folder.parent:
            folder = folder.parent
        path, _ = QFileDialog.getOpenFileName(self, self.t('dialog.binary'), str(folder))
        if path:
            edit.setText(path)
            self.save_config()

    def auto_detect(self) -> None:
        main = self.binary.text()
        found = detect_only_if_empty(main, 'doubletake', base=APP_DIR)
        if found != main:
            self.binary.setText(found)
            self.log(self.t('log.found', name='doubletake', path=found))
        elif main.strip():
            self.log(self.t('log.path_preserved', name='doubletake'))
        else:
            self.log(self.t('log.not_found', name='doubletake'), warning=True)
        ctl = self.ctl_binary.text()
        sibling = Path(self.binary.text()).parent / 'doubletake-ctl' if self.binary.text().strip() else None
        preferred = str(sibling) if sibling and executable_path(str(sibling)) else ''
        found = detect_only_if_empty(ctl, 'doubletake-ctl', preferred, base=APP_DIR)
        if found != ctl:
            self.ctl_binary.setText(found)
            self.log(self.t('log.found', name='doubletake-ctl', path=found))
        elif ctl.strip():
            self.log(self.t('log.path_preserved', name='doubletake-ctl'))
        else:
            self.log(self.t('log.optional_not_found'))
        self.save_config()
        self.check_paths(silent=False)

    def check_paths(self, silent: bool = False) -> None:
        found, missing = [], []
        for edit, name in ((self.binary, 'doubletake'), (self.ctl_binary, 'doubletake-ctl')):
            path = executable_path(edit.text().strip())
            if path:
                found.append(path)
                self.log(self.t('log.valid_path', path=path))
            else:
                missing.append(name)
        if 'doubletake' in missing:
            self.log(self.t('log.main_missing'), warning=True)
        if 'doubletake-ctl' in missing:
            self.log(self.t('log.optional_not_found'))
        if not silent:
            details = self.t('dialog.verify_body', count=len(found), found='\n'.join(found) or '—',
                             missing=', '.join(missing) or '—')
            QMessageBox.information(self, self.t('dialog.verify_title'), details)

    def restore_config(self) -> None:
        main_saved = str(self.cfg.value('binaries/doubletake', ''))
        main = main_saved if main_saved.strip() else find_binary('doubletake', base=APP_DIR)
        ctl_saved = str(self.cfg.value('binaries/doubletake_ctl', ''))
        sibling = Path(main).parent / 'doubletake-ctl' if main.strip() else None
        preferred = str(sibling) if sibling and executable_path(str(sibling)) else ''
        ctl = ctl_saved if ctl_saved.strip() else find_binary('doubletake-ctl', preferred, base=APP_DIR)
        self.binary.setText(main)
        self.ctl_binary.setText(ctl)
        for key, edit in (
            ('stream/target', self.target), ('stream/ports', self.ports),
            ('stream/credentials', self.credentials), ('stream/extra', self.extra),
            ('daemon/ports', self.daemon_ports), ('daemon/socket', self.daemon_socket),
            ('daemon/ctl_socket', self.ctl_socket), ('daemon/target', self.ctl_target),
        ):
            edit.setText(str(self.cfg.value(key, '')))
        for key, widget, default in (
            ('stream/fps', self.fps, 30), ('stream/bitrate', self.bitrate, 0),
            ('stream/latency', self.latency, 0), ('stream/airplay_port', self.airplay_port, 7000),
        ):
            try:
                widget.setValue(int(self.cfg.value(key, default)))
            except (ValueError, TypeError):
                widget.setValue(default)
        for key, widget in (
            ('stream/hw', self.hw), ('stream/codec', self.codec),
            ('stream/cred_backend', self.cred_backend),
        ):
            value = str(self.cfg.value(key, widget.currentText()))
            if widget.findText(value) >= 0:
                widget.setCurrentText(value)
        for key, widget in (
            ('stream/pair', self.pair), ('stream/no_audio', self.no_audio),
            ('stream/debug', self.debug), ('stream/test', self.test),
            ('stream/no_encrypt', self.no_encrypt), ('stream/direct_key', self.direct_key),
        ):
            widget.setChecked(str(self.cfg.value(key, 'false')).lower() == 'true')
        geometry = self.cfg.value('window/geometry')
        if geometry is not None:
            self.restoreGeometry(geometry)

    def save_config(self) -> None:
        for key, widget in (
            ('binaries/doubletake', self.binary), ('binaries/doubletake_ctl', self.ctl_binary),
            ('stream/target', self.target), ('stream/ports', self.ports),
            ('stream/credentials', self.credentials), ('stream/extra', self.extra),
            ('daemon/ports', self.daemon_ports), ('daemon/socket', self.daemon_socket),
            ('daemon/ctl_socket', self.ctl_socket), ('daemon/target', self.ctl_target),
        ):
            self.cfg.setValue(key, widget.text())
        for key, widget in (
            ('stream/fps', self.fps), ('stream/bitrate', self.bitrate),
            ('stream/latency', self.latency), ('stream/airplay_port', self.airplay_port),
        ):
            self.cfg.setValue(key, widget.value())
        for key, widget in (
            ('stream/hw', self.hw), ('stream/codec', self.codec),
            ('stream/cred_backend', self.cred_backend),
        ):
            self.cfg.setValue(key, widget.currentText())
        for key, widget in (
            ('stream/pair', self.pair), ('stream/no_audio', self.no_audio),
            ('stream/debug', self.debug), ('stream/test', self.test),
            ('stream/no_encrypt', self.no_encrypt), ('stream/direct_key', self.direct_key),
        ):
            self.cfg.setValue(key, widget.isChecked())
        self.cfg.setValue('ui/language', self.locale.language)
        self.cfg.setValue('window/geometry', self.saveGeometry())
        self.cfg.sync()
        self.log(self.t('log.saved_config'))

    def closeEvent(self, event) -> None:
        self.save_config()
        for process, graceful_ms, force_ms in ((self.stream, 1200, 800), (self.ctl, 500, 500)):
            if process.state() != QProcess.ProcessState.NotRunning:
                process.terminate()
                if not process.waitForFinished(graceful_ms):
                    process.kill()
                    process.waitForFinished(force_ms)
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName('Doubletake GUI')
    app.setDesktopFileName('doubletake-gui')
    app.setWindowIcon(QIcon(str(ICON)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
