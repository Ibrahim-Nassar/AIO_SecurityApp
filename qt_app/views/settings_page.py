from __future__ import annotations

import os
from typing import Dict, Callable, Optional, Callable as _Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QMessageBox,
    QTabWidget,
)

from qt_app.ui import SectionCard
from pathlib import Path
from dotenv import load_dotenv
from ioc_core.config_env import resolve_env_path, load_env_file, save_env_kv


ENV_KEYS = [
    ("VIRUSTOTAL_API_KEY", "VirusTotal"),
    ("ABUSEIPDB_API_KEY", "AbuseIPDB"),
    ("OTX_API_KEY", "OTX"),
]


def _per_user_env_path() -> str:
    import platform
    import os as _os
    sysname = platform.system().lower()
    if sysname.startswith("win"):
        base = _os.getenv("APPDATA", _os.path.expanduser("~"))
        return str(Path(base) / "UpdatedIOCChecker" / ".env")
    if sysname == "darwin":
        return str(Path.home() / "Library" / "Application Support" / "UpdatedIOCChecker" / ".env")
    return str(Path.home() / ".config" / "UpdatedIOCChecker" / ".env")


class SettingsPage(QWidget):
    def __init__(self, status_cb: Callable[[str], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._status_cb: Callable[[str], None] = status_cb
        self._edits: Dict[str, QLineEdit] = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        tabs = QTabWidget()
        tabs.setAccessibleName("Settings Tabs")
        root.addWidget(tabs)

        # General tab
        gen = QWidget()
        gen_l = QVBoxLayout(gen)
        gen_l.setContentsMargins(12, 12, 12, 12)
        gen_l.setSpacing(8)
        # Placeholder general options (restore layout)
        self.chk_restore = QCheckBox("Restore last window layout on startup")
        self.chk_restore.setChecked(True)
        gen_l.addWidget(self.chk_restore)
        gen_l.addStretch(1)
        tabs.addTab(gen, "General")

        # API Keys tab
        api = QWidget()
        api_l = QVBoxLayout(api)
        api_l.setContentsMargins(12, 12, 12, 12)
        api_l.setSpacing(8)
        card = SectionCard("API Keys")
        form = QVBoxLayout()

        for key, label in ENV_KEYS:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{label}:"))
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.EchoMode.Normal)
            edit.setAccessibleName(f"{label} API Key Input")
            row.addWidget(edit, 1)
            btn = QPushButton("Show")
            def make_toggle(e: QLineEdit = edit, b: QPushButton = btn) -> _Callable[[], None]:
                def _t() -> None:
                    if e.echoMode() == QLineEdit.EchoMode.Password:
                        e.setEchoMode(QLineEdit.EchoMode.Normal)
                        b.setText("Hide")
                    else:
                        e.setEchoMode(QLineEdit.EchoMode.Password)
                        b.setText("Show")
                return _t
            btn.clicked.connect(make_toggle())
            row.addWidget(btn)
            test_btn = QPushButton("Test")
            def make_test(k: str = key, e: QLineEdit = edit) -> _Callable[[], None]:
                def _test() -> None:
                    val = e.text().strip()
                    if not val:
                        QMessageBox.warning(self, "Test", f"{k}: enter a key first")
                        return
                    QMessageBox.information(self, "Test", f"{k}: looks OK")
                return _test
            test_btn.clicked.connect(make_test())
            row.addWidget(test_btn)
            form.addLayout(row)
            self._edits[key] = edit

        card.body.addLayout(form)
        # Active .env path display
        self._env_path_label = QLabel("")
        self._env_path_label.setProperty("muted", True)
        card.body.addWidget(self._env_path_label)
        api_l.addWidget(card, 1)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn_load = QPushButton("Reload .env")
        self.btn_save = QPushButton("Save to .env")
        self.btn_save.setProperty("class", "PrimaryButton")
        self.btn_load.setProperty("class", "SecondaryButton")
        self.btn_load.setToolTip("Reload API keys from your profile .env")
        self.btn_save.setToolTip("Save API keys to your profile .env path")
        btn_row.addWidget(self.btn_load)
        btn_row.addWidget(self.btn_save)
        api_l.addLayout(btn_row)
        tabs.addTab(api, "API Keys")

        self.btn_load.clicked.connect(self._on_load)
        self.btn_save.clicked.connect(self._on_save)
        # Populate fields on open using current env
        self._populate_from_env()
        self._update_env_path_label()

    def _update_status(self, msg: str) -> None:
        self._status_cb(msg)

    def _on_load(self) -> None:
        # Load from centralized per-user env path; migrate from CWD if needed
        env_path = resolve_env_path()
        user_env = Path(env_path)
        if not user_env.exists():
            cwd_env = Path(os.getcwd()) / ".env"
            if cwd_env.exists():
                try:
                    user_env.parent.mkdir(parents=True, exist_ok=True)
                    user_env.write_text(cwd_env.read_text(encoding="utf-8"), encoding="utf-8")
                except Exception:
                    pass
        loaded = False
        try:
            loaded = load_env_file(env_path)
        except Exception:
            loaded = False
        data: Dict[str, str] = {}
        try:
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for ln in f:
                        if "=" in ln:
                            k, v = ln.split("=", 1)
                            data[k.strip()] = v.strip().rstrip("\n")
        except Exception as e:
            QMessageBox.critical(self, "Load .env", str(e))
            return
        for key, _ in ENV_KEYS:
            self._edits[key].setText(data.get(key, ""))
            if data.get(key, ""):
                os.environ[key] = data.get(key, "")
        self._update_env_path_label()
        self._update_status("Reloaded .env" if loaded else "Failed to load .env")
        try:
            from qt_app.ui import Toast
            Toast(self).show_toast(self, "Reloaded .env." if loaded else "Failed to load .env")
        except Exception:
            pass

    def _on_save(self) -> None:
        env_path = resolve_env_path()
        existing: Dict[str, str] = {}
        try:
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for ln in f:
                        if "=" in ln:
                            k, v = ln.split("=", 1)
                            existing[k.strip()] = v.strip().rstrip("\n")
        except Exception:
            existing = {}
        # Merge current UI values, allowing empty to clear
        for key, _ in ENV_KEYS:
            existing[key] = self._edits[key].text().strip()
        try:
            save_env_kv(env_path, existing)
        except Exception as e:
            QMessageBox.critical(self, "Save .env", str(e))
            return
        # Reload into process env and repopulate UI
        try:
            load_env_file(env_path)
        except Exception:
            pass
        self._populate_from_env()
        self._update_env_path_label()
        self._update_status("Saved and reloaded.")
        try:
            from qt_app.ui import Toast
            Toast(self).show_toast(self, "Saved and reloaded.")
        except Exception:
            pass

    def _populate_from_env(self) -> None:
        try:
            for key, _ in ENV_KEYS:
                self._edits[key].setText(os.getenv(key, ""))
        except Exception:
            pass

    def _update_env_path_label(self) -> None:
        try:
            self._env_path_label.setText(f"Active .env: {resolve_env_path()}")
        except Exception:
            self._env_path_label.setText("Active .env: (unavailable)")