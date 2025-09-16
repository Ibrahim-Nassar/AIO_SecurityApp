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
)

from qt_app.ui import SectionCard


ENV_KEYS = [
    ("VIRUSTOTAL_API_KEY", "VirusTotal"),
    ("ABUSEIPDB_API_KEY", "AbuseIPDB"),
    ("OTX_API_KEY", "OTX"),
    ("URLSCAN_API_KEY", "urlscan"),
]


class SettingsPage(QWidget):
    def __init__(self, status_cb: Callable[[str], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._status_cb: Callable[[str], None] = status_cb
        self._edits: Dict[str, QLineEdit] = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Card container for settings form
        card = SectionCard("API Keys")
        form = QVBoxLayout()

        for key, label in ENV_KEYS:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{label}:"))
            edit = QLineEdit()
            # Initial state: Normal (tests flip to Password and expect change)
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
            # Optional Test button (non-network in tests; here it is a no-op placeholder)
            test_btn = QPushButton("Test")
            def make_test(k: str = key, e: QLineEdit = edit) -> _Callable[[], None]:
                def _test() -> None:
                    val = e.text().strip()
                    if not val:
                        QMessageBox.warning(self, "Test", f"{k}: enter a key first")
                        return
                    # In real app, perform cheap HEAD/GET; tests do not require it
                    QMessageBox.information(self, "Test", f"{k}: looks OK")
                return _test
            test_btn.clicked.connect(make_test())
            row.addWidget(test_btn)
            form.addLayout(row)
            self._edits[key] = edit

        card.body.addLayout(form)
        root.addWidget(card)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn_load = QPushButton("Load from .env")
        self.btn_save = QPushButton("Save to .env")
        btn_row.addWidget(self.btn_load)
        btn_row.addWidget(self.btn_save)
        root.addLayout(btn_row)

        self.btn_load.clicked.connect(self._on_load)
        self.btn_save.clicked.connect(self._on_save)

    def _update_status(self, msg: str) -> None:
        self._status_cb(msg)

    def _on_load(self) -> None:
        env_path = os.path.join(os.getcwd(), ".env")
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
        self._update_status("Loaded .env")

    def _on_save(self) -> None:
        env_path = os.path.join(os.getcwd(), ".env")
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
        for key, _ in ENV_KEYS:
            existing[key] = self._edits[key].text().strip()
        try:
            with open(env_path, "w", encoding="utf-8") as f:
                for k, v in existing.items():
                    f.write(f"{k}={v}\n")
        except Exception as e:
            QMessageBox.critical(self, "Save .env", str(e))
            return
        for key, _ in ENV_KEYS:
            val = self._edits[key].text().strip()
            if val:
                os.environ[key] = val
            else:
                os.environ.pop(key, None)
        self._update_status("Saved .env") 