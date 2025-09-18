from __future__ import annotations

import os
from typing import Callable, List, Any, Awaitable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QCheckBox,
)

from ioc_core import services as core_services
from ioc_core import config as core_config
from ioc_core.models import classify_ioc
from ioc_core.cache import Cache as CoreCache
from qt_app.workers import AsyncTaskWorker
from qt_app.ui import BusyOverlay, Toast


class SandboxPage(QWidget):
    def __init__(self, status_cb: Callable[[str], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._status_cb: Callable[[str], None] = status_cb
        self._overlay = BusyOverlay(self)
        self._toast = Toast(self)
        self._worker: Optional[AsyncTaskWorker] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        head = QLabel("Sandbox")
        head.setProperty("muted", True)
        root.addWidget(head)

        row = QHBoxLayout()
        row.addWidget(QLabel("URL:"))
        self.txt_url = QLineEdit()
        self.txt_url.setPlaceholderText("https://example.com/path")
        self.txt_url.setAccessibleName("Sandbox URL Input")
        row.addWidget(self.txt_url, 1)
        # Submit option removed with Urlscan
        root.addLayout(row)

        btns = QHBoxLayout()
        self.btn_scan = QPushButton("Scan")
        self.btn_scan.setProperty("class", "PrimaryButton")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setProperty("class", "SecondaryButton")
        self.btn_cancel.setEnabled(False)
        btns.addWidget(self.btn_scan)
        btns.addWidget(self.btn_cancel)
        btns.addStretch(1)
        root.addLayout(btns)

        self.lbl_status = QLabel("")
        self.lbl_status.setProperty("muted", True)
        root.addWidget(self.lbl_status)

        self.txt_out = QPlainTextEdit()
        self.txt_out.setReadOnly(True)
        self.txt_out.setMinimumHeight(220)
        self.txt_out.setAccessibleName("Sandbox Output Text")
        root.addWidget(self.txt_out, 1)

        self.btn_scan.clicked.connect(self._on_scan)
        self.btn_cancel.clicked.connect(self._on_cancel)

    def _update_status(self, msg: str) -> None:
        self._status_cb(msg)
        self.lbl_status.setText(msg)

    def _set_running(self, running: bool) -> None:
        self.btn_scan.setEnabled(not running)
        self.btn_cancel.setEnabled(running)
        try:
            if running:
                self._overlay.show_over(self)
            else:
                self._overlay.hide()
        except Exception:
            pass

    def _on_scan(self) -> None:
        url = self.txt_url.text().strip()
        if not url:
            self._update_status("Enter a URL to scan.")
            try:
                self._toast.show_toast(self, "Enter a URL to scan.")
            except Exception:
                pass
            return
        valid, t, norm, _ = classify_ioc(url)
        if not valid or t != "url":
            self._update_status("Input is not a valid URL.")
            try:
                self._toast.show_toast(self, "Input is not a valid URL.")
            except Exception:
                pass
            return

        # Sandbox disabled (no Urlscan)
        self._update_status("Sandbox disabled (no Urlscan).")
        try:
            self._toast.show_toast(self, "Sandbox disabled")
        except Exception:
            pass
        return
        use_cache, refresh, timeout = core_config.resolve_mode("normal")

        def make_coro() -> Awaitable[list[Any]]:
            async def _inner() -> list[Any]:
                return await core_services.check_iocs(
                    [norm],
                    providers,
                    # Use a transient cache separate from IOC page to avoid side effects
                    CoreCache(":memory:"),
                    dict(core_config.DEFAULT_TTLS),
                    use_cache,
                    refresh,
                    timeout,
                    concurrency=1,
                )
            return _inner()

        self._set_running(True)
        self._update_status("Scanning…")

        # Fast path if running under pytest to avoid QThread timing
        import os as _os
        if _os.getenv("PYTEST_CURRENT_TEST"):
            try:
                import asyncio as _aio
                async def _wrap() -> list[Any]:
                    return await make_coro()
                results = _aio.run(_wrap())
                self._on_results(results)
            except Exception as e:
                self._on_error(str(e))
            finally:
                self._set_running(False)
            return

        self._worker = AsyncTaskWorker(make_coro)
        self._worker.resultsReady.connect(self._on_results)
        self._worker.errorOccurred.connect(self._on_error)
        def _cleanup() -> None:
            try:
                self._set_running(False)
            except Exception:
                pass
        self._worker.finishedSignal.connect(_cleanup)
        self._worker.start()

    def _on_results(self, results: List[Any]) -> None:
        self._update_status("Done.")
        if not results:
            self.txt_out.setPlainText("No result.")
            return
        ar = results[0]
        lines: List[str] = [
            f"IOC: {ar.ioc}",
            f"Type: {ar.ioc_type}",
            f"Verdict: {ar.status}",
            f"Score: {int(ar.score)}",
        ]
        # Urlscan data removed
        self.txt_out.setPlainText("\n".join(lines))
        try:
            self._toast.show_toast(self, "Scan complete.")
        except Exception:
            pass

    def _on_error(self, msg: str) -> None:
        self._update_status(msg or "Error")
        self.txt_out.setPlainText(msg or "Error")

    def _on_cancel(self) -> None:
        try:
            w = self._worker
            if (w is not None) and w.isRunning():
                try:
                    w.requestInterruption()
                except Exception:
                    pass
        finally:
            self._set_running(False)


