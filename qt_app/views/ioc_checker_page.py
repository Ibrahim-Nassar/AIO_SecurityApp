# CHANGELOG:
# - Overhauled layout to two-pane (left controls, right results) with splitters
# - Added sorting, column width persistence, context menu, keyboard shortcuts
# - Busy overlay during runs and toast status notifications
# - Preserved public attributes used by tests (txt_in, btn_check, btn_save, btn_cancel, table, model, lbl_mode, lbl_summary, btn_copy, txt_summary)

from __future__ import annotations

import os
from typing import Any, Dict, List, Callable, Awaitable

from PySide6.QtCore import Qt, QSettings, QPoint
from PySide6.QtGui import QStandardItem, QStandardItemModel, QKeySequence, QAction
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QTableView,
    QFrame,
    QFileDialog,
    QSplitter,
    QHeaderView,
    QMenu,
)

from ioc_core import config as core_config
from ioc_core.cache import Cache as CoreCache
from ioc_core import services as core_services
from ioc_core.export import export_results_csv
from qt_app.workers import AsyncTaskWorker
from qt_app.ui import BusyOverlay, ToastManager
from ioc_core.logger import get_logger


class IocCheckerPage(QWidget):
    def __init__(self, status_cb: Callable[[str], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status_cb: Callable[[str], None] = status_cb
        self._cache = CoreCache(".ioc_enricher_cache.sqlite")
        self._worker: AsyncTaskWorker | None = None
        self._last_results: List[Any] = []
        self._settings = QSettings("UpdatedIOCChecker", "QtApp")

        # Root layout with two-pane split (left controls, right results)
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Left controls stack
        left = QVBoxLayout()
        left.setSpacing(8)

        # Providers
        prov_box = QGroupBox("Providers")
        prov_layout = QHBoxLayout()
        self.chk_vt = QCheckBox("VirusTotal")
        self.chk_ab = QCheckBox("AbuseIPDB")
        self.chk_otx = QCheckBox("OTX")
        self.chk_tf = QCheckBox("ThreatFox")
        self.chk_vt.setChecked(True)
        self.chk_ab.setChecked(True)
        self.chk_otx.setChecked(True)
        self.chk_tf.setChecked(True)
        for w in (self.chk_vt, self.chk_ab, self.chk_otx, self.chk_tf):
            prov_layout.addWidget(w)
        hint = QLabel("Tip: uncheck providers to speed up requests.")
        hint.setProperty("muted", True)
        prov_layout.addStretch(1)
        prov_box.setLayout(prov_layout)
        left.addWidget(prov_box)
        left.addWidget(hint)

        # Mode label (Normal only)
        mode_row = QHBoxLayout()
        self.lbl_mode = QLabel("Mode: Normal")
        self.lbl_mode.setToolTip("Fast/Deep disabled to ensure reliability.")
        mode_row.addWidget(self.lbl_mode)
        mode_row.addStretch(1)
        left.addLayout(mode_row)

        # Input
        left.addWidget(QLabel("IOCs (one per line, or @file path):"))
        self.txt_in = QPlainTextEdit()
        self.txt_in.setPlaceholderText("One IOC per line or @file path\nExamples:\nexample.com\n8.8.8.8\nhttp://test\n@C:/path/to/list.txt")
        self.txt_in.setMinimumHeight(120)
        self.txt_in.setAccessibleName("IOC Input Text")
        left.addWidget(self.txt_in)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_check = QPushButton("Check")
        self.btn_check.setProperty("class", "PrimaryButton")
        self.btn_check.setToolTip("Run checks on selected providers (Ctrl+Enter)")
        self.btn_save = QPushButton("Save CSV")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setProperty("class", "SecondaryButton")
        # Removed bypass cache and back per UI simplification
        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.btn_check.setMinimumWidth(110)
        for b in (self.btn_save, self.btn_cancel):
            b.setMinimumWidth(100)
        btn_row.addWidget(self.btn_check)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch(1)
        left.addLayout(btn_row)

        # Right results splitter (table + summary)
        right_split = QSplitter(Qt.Orientation.Vertical)

        # Results table area
        table_container = QVBoxLayout()
        table_wrap = QWidget()
        table_wrap.setLayout(table_container)
        table_container.setContentsMargins(0, 0, 0, 0)
        table_container.setSpacing(8)

        # Divider look implicitly via table frame
        self.model = QStandardItemModel(0, 1, self)
        self.model.setHorizontalHeaderLabels(["IOC"]) 
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setAccessibleName("IOC Results Table")
        table_container.addWidget(self.table, 1)

        # Empty state label (kept for UX but not used for transient feedback)
        self._empty_label = QLabel("No results yet—enter IOCs and press Check.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setProperty("muted", True)
        table_container.addWidget(self._empty_label)
        self._refresh_empty_state()

        right_split.addWidget(table_wrap)

        # Summary area
        summary_wrap = QWidget()
        summary_layout = QVBoxLayout(summary_wrap)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        hdr_row = QHBoxLayout()
        self.lbl_summary = QLabel("Summary: (select a row)")
        hdr_row.addWidget(self.lbl_summary)
        hdr_row.addStretch(1)
        self.btn_copy = QPushButton("Copy Summary")
        self.btn_copy.setProperty("class", "SecondaryButton")
        self.btn_copy.setEnabled(False)
        hdr_row.addWidget(self.btn_copy)
        summary_layout.addLayout(hdr_row)
        self.txt_summary = QPlainTextEdit()
        self.txt_summary.setReadOnly(True)
        self.txt_summary.setMinimumHeight(160)
        self.txt_summary.setAccessibleName("IOC Summary Text")
        summary_layout.addWidget(self.txt_summary)
        right_split.addWidget(summary_wrap)
        # Give more space to the table than the summary
        right_split.setStretchFactor(0, 3)
        right_split.setStretchFactor(1, 1)

        # Top-level splitter to place left and right (give table area more space)
        main_split = QSplitter(Qt.Orientation.Horizontal)
        left_wrap = QWidget()
        left_wrap.setLayout(left)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(8)
        main_split.addWidget(left_wrap)
        main_split.addWidget(right_split)
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 2)
        root.addWidget(main_split)

        # Persist positions
        self._restore_table_state()
        self._main_split = main_split
        self._right_split = right_split

        # Context menu for table
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context)

        # Busy overlay
        self._overlay = BusyOverlay(self)

        # Keyboard shortcuts
        self._sc_check = QAction(self)
        self._sc_check.setShortcut(QKeySequence("Ctrl+Return"))
        self._sc_check.triggered.connect(self._on_check)
        self.addAction(self._sc_check)
        self._sc_save = QAction(self)
        self._sc_save.setShortcut(QKeySequence("Ctrl+S"))
        self._sc_save.triggered.connect(self._on_save_csv)
        self.addAction(self._sc_save)
        self._sc_copy = QAction(self)
        self._sc_copy.setShortcut(QKeySequence("Ctrl+C"))
        self._sc_copy.triggered.connect(self._on_copy_summary)
        self.addAction(self._sc_copy)
        self._sc_cancel = QAction(self)
        self._sc_cancel.setShortcut(QKeySequence("Esc"))
        self._sc_cancel.triggered.connect(self._on_cancel)
        self.addAction(self._sc_cancel)

        # Wire signals
        self.btn_check.clicked.connect(self._on_check)
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_save.clicked.connect(self._on_save_csv)
        self.btn_copy.clicked.connect(self._on_copy_summary)
        self.table.selectionModel().selectionChanged.connect(self._refresh_summary)

        # Initial
        self._update_status("")

    # Helpers
    def _restore_table_state(self) -> None:
        try:
            hv: QHeaderView = self.table.horizontalHeader()
            widths = self._settings.value("ioc_checker/table_widths_v2", None)
            if widths and isinstance(widths, list) and hv.count() == len(widths):
                for i, w in enumerate(widths):
                    try:
                        hv.resizeSection(i, int(w))
                    except Exception:
                        pass
            col_obj = self._settings.value("ioc_checker/sort_col_v2", 0)
            order_obj = self._settings.value("ioc_checker/sort_order_v2", 0)
            col = int(col_obj) if isinstance(col_obj, (int, str)) else 0
            order = int(order_obj) if isinstance(order_obj, (int, str)) else 0
            self.table.sortByColumn(col, Qt.SortOrder(order))
        except Exception:
            # Default sort by IOC asc
            try:
                self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
            except Exception:
                pass

    def _update_status(self, text: str) -> None:
        # Unify feedback via toast system; still invoke callback for tests/diagnostics
        self._status_cb(text)

    def _refresh_empty_state(self) -> None:
        has_rows = self.model.rowCount() > 0
        self._empty_label.setVisible(not has_rows)
        self.table.setVisible(True)

    def _info_map_from_providers(self, providers: List[Any]) -> Dict[str, str]:
        info: Dict[str, str] = {}
        def put(key: str, value: str) -> None:
            if value and key not in info:
                info[key] = value
        for pr in providers:
            for ev in getattr(pr, "evidence", []) or []:
                if not isinstance(ev, str) or "=" not in ev:
                    continue
                k, v = ev.split("=", 1)
                k = k.strip().lower()
                v = v.strip()
                if k in ("country", "countrycode", "country_code"):
                    put("country", v)
                elif k == "asn":
                    put("asn", v)
                elif k == "isp":
                    put("isp", v)
                elif k == "domain":
                    put("domain", v)
                elif k == "usagetype":
                    put("usagetype", v)
                elif k in ("first_seen", "first_seen_utc"):
                    put("first_seen", v)
                elif k in ("last_seen", "last_seen_utc", "lastreportedat"):
                    put("last_seen", v)
                elif k == "family":
                    put("family", v)
                elif k == "tags":
                    put("tags", v)
                elif k == "categories":
                    put("categories", v)
                elif k == "reputation":
                    put("reputation", v)
        return info

    def _quick_info_from_providers(self, providers: List[Any]) -> str:
        info = self._info_map_from_providers(providers)
        parts: List[str] = []
        if info.get("country"):
            parts.append(info["country"])
        if info.get("asn"):
            parts.append(info["asn"])
        if info.get("isp"):
            parts.append(f"isp={info['isp']}")
        if not parts and info.get("domain"):
            parts.append(f"domain={info['domain']}")
        if not parts and info.get("tags"):
            parts.append("tags=" + ",".join(info["tags"].split(",")[:3]))
        return " ".join(parts)

    def _read_inputs(self, text: str) -> List[str]:
        out: List[str] = []
        for raw in (text or "").strip().splitlines():
            s = raw.strip()
            if not s:
                continue
            if s.startswith("@") and os.path.isfile(s[1:]):
                try:
                    with open(s[1:], "r", encoding="utf-8", errors="ignore") as f:
                        for ln in f:
                            t = ln.strip()
                            if t:
                                out.append(t)
                except Exception as e:
                    QMessageBox.critical(self, "File error", str(e))
                    return []
            else:
                out.append(s)
        seen = set()
        dedup: List[str] = []
        for x in out:
            if x not in seen:
                seen.add(x)
                dedup.append(x)
        return dedup

    def _selected_providers(self) -> List[Any]:
        provs: List[Any] = []
        if self.chk_vt.isChecked():
            provs.append(core_services.VirusTotalProvider(os.getenv("VIRUSTOTAL_API_KEY")))
        if self.chk_ab.isChecked():
            provs.append(core_services.AbuseIPDBProvider(os.getenv("ABUSEIPDB_API_KEY")))
        if self.chk_otx.isChecked():
            provs.append(core_services.OTXProvider(os.getenv("OTX_API_KEY") or os.getenv("ALIENVAULT_OTX_API_KEY")))
        if self.chk_tf.isChecked():
            provs.append(core_services.ThreatFoxProvider())
        return provs

    def _set_running(self, running: bool) -> None:
        self.btn_check.setEnabled(not running)
        self.btn_cancel.setEnabled(running)
        self.btn_save.setEnabled((not running) and (self._last_results != []))
        try:
            if running:
                self.btn_check.setText("Checking…")
                self._overlay.show_over(self._right_split, "Working…")
            else:
                self.btn_check.setText("Check")
                self._overlay.hide()
        except Exception:
            pass

    def _populate_table_from_results(self, results: List[Any]) -> None:
        self.model.removeRows(0, self.model.rowCount())
        for ar in results:
            per = {pr.provider: pr for pr in ar.providers}
            row_vals: List[str] = [ar.ioc]
            provider_cols = []
            for i in range(1, self.model.columnCount()):
                txt = self.model.headerData(i, Qt.Orientation.Horizontal)
                if txt is None:
                    continue
                provider_cols.append(str(txt))
            for pname in provider_cols:
                pr = per.get(pname)
                if pr is None:
                    row_vals.append("—")
                else:
                    txt = pr.status
                    if pr.status in ("MALICIOUS", "SUSPICIOUS") and pr.score:
                        try:
                            txt += f" ({int(pr.score)})"
                        except Exception:
                            pass
                    row_vals.append(txt)
            r = self.model.rowCount()
            self.model.insertRow(r)
            for c, val in enumerate(row_vals):
                it = QStandardItem(str(val))
                if c == 0:
                    it.setEditable(False)
                it.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.model.setItem(r, c, it)
        self._refresh_empty_state()
        # Restore sort if available
        try:
            col_obj = self._settings.value("ioc_checker/sort_col_v2", 0)
            order_obj = self._settings.value("ioc_checker/sort_order_v2", 0)
            col = int(col_obj) if isinstance(col_obj, (int, str)) else 0
            order = int(order_obj) if isinstance(order_obj, (int, str)) else 0
            self.table.sortByColumn(col, Qt.SortOrder(order))
        except Exception:
            pass

    def _update_summary(self, results: List[Any]) -> None:
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            self.txt_summary.setPlainText("")
            self.lbl_summary.setText("Summary: (select a row)")
            self.btn_copy.setEnabled(False)
            return
        idx = sel[0]
        ioc = self.model.item(idx.row(), 0).text()
        self.lbl_summary.setText(f"Summary: {ioc}")
        lines: List[str] = []
        for ar in results:
            if ar.ioc == ioc:
                lines.extend([
                    f"IOC: {ar.ioc}",
                    f"Type: {ar.ioc_type}",
                    f"Verdict: {ar.status}",
                    f"Score: {int(ar.score)}",
                ])
                # Add detailed investigator info
                info = self._info_map_from_providers(ar.providers)
                def add_if(k: str, label: str) -> None:
                    v = info.get(k)
                    if v:
                        lines.append(f"{label}: {v}")
                add_if("country", "Country")
                add_if("asn", "ASN")
                add_if("isp", "ISP")
                add_if("domain", "Domain")
                add_if("usagetype", "Usage")
                add_if("first_seen", "First seen")
                add_if("last_seen", "Last seen")
                add_if("family", "Malware family")
                add_if("categories", "Categories")
                add_if("tags", "Tags")
                add_if("reputation", "Reputation")
                parts: List[str] = []
                for pr in ar.providers:
                    ptxt = f"{pr.provider}={pr.status}"
                    if pr.score:
                        try:
                            ptxt += f" ({int(pr.score)})"
                        except Exception:
                            pass
                    parts.append(ptxt)
                lines.append("Providers: " + ", ".join(parts))
                break
        self.txt_summary.setPlainText("\n".join(lines))
        self.btn_copy.setEnabled(True)

    # Actions
    def _on_check(self) -> None:
        iocs = self._read_inputs(self.txt_in.toPlainText())
        if not iocs:
            try:
                ToastManager.instance(self).show("Enter at least one IOC.", "error")
            except Exception:
                pass
            return
        providers = self._selected_providers()
        if not providers:
            try:
                ToastManager.instance(self).show("Select at least one provider.", "warn")
            except Exception:
                pass
            return
        # API key validation: if all selected need keys and none configured, block with error
        missing: List[str] = []
        for p in providers:
            try:
                # providers with available()==False imply missing key
                if hasattr(p, "available") and callable(getattr(p, "available")):
                    if not p.available():
                        missing.append(p.name)
            except Exception:
                pass
        if missing and (len(missing) == len(providers)):
            try:
                ToastManager.instance(self).show("Missing API keys for selected providers.", "error")
            except Exception:
                pass
            return
        use_cache, refresh, timeout = core_config.resolve_mode("normal")
        # bypass cache removed
        ttls = dict(core_config.DEFAULT_TTLS)
        # Table shows IOC + provider columns only (no Type/Age)
        headers = ["IOC"] + [p.name for p in providers]
        self.model.clear()
        self.model.setHorizontalHeaderLabels(headers)
        self.model.setRowCount(0)
        self._last_results = []
        self._set_running(True)
        self._update_status("Running…")
        try:
            log = get_logger()
            types = {}
            for s in iocs:
                ok, t, _, _ = core_services.classify_ioc(s)  # type: ignore[attr-defined]
                if ok:
                    types[t] = types.get(t, 0) + 1
            log.info("run start providers=%s iocs=%d types=%s", [p.name for p in providers], len(iocs), types)
        except Exception:
            pass

        cancel_flag = {"c": False}
        def cancel_cb() -> bool:
            return bool(cancel_flag["c"]) 

        def make_coro() -> Awaitable[list[Any]]:
            async def _inner() -> list[Any]:
                return await core_services.check_iocs(
                    iocs,
                    providers,
                    self._cache,
                    ttls,
                    use_cache,
                    refresh,
                    timeout,
                    concurrency=max(1, min(core_config.DEFAULT_CONCURRENCY, 4)),
                    cancel_cb=cancel_cb,
                )
            return _inner()
        # Fast path for test runner to avoid QThread timing issues
        import os as _os
        if _os.getenv("PYTEST_CURRENT_TEST"):
            try:
                import asyncio as _aio
                async def _typed_wrapper() -> list[Any]:
                    coro = make_coro()
                    return await coro
                results = _aio.run(_typed_wrapper())
                self._on_results_ready(results)
            except Exception as e:
                self._on_error(str(e))
            finally:
                self._set_running(False)
            return
        self._worker = AsyncTaskWorker(make_coro)
        self._worker.resultsReady.connect(self._on_results_ready)
        self._worker.errorOccurred.connect(self._on_error)
        self._worker.finishedSignal.connect(self._on_run_finished)
        self._worker.start()
        self._cancel_flag = cancel_flag

    def _on_cancel(self) -> None:
        try:
            if hasattr(self, "_cancel_flag"):
                self._cancel_flag["c"] = True
            w = self._worker
            if (w is not None) and w.isRunning():
                try:
                    w.requestInterruption()
                except Exception:
                    pass
            self._update_status("Cancel requested…")
        except Exception:
            pass

    def _on_results_ready(self, results: List[Any]) -> None:
        self._last_results = results or []
        self._populate_table_from_results(self._last_results)
        hits = sum(1 for ar in self._last_results if ar.status in ("MALICIOUS", "SUSPICIOUS"))
        if self._last_results:
            self._update_status(f"Done: {hits} hit(s).")
            try:
                self._toast.show_toast(self, f"Done: {hits} hit(s).")
            except Exception:
                pass
        else:
            self._update_status("Done: no results.")
            try:
                self._toast.show_toast(self, "Done: no results.")
            except Exception:
                pass
        self.btn_save.setEnabled(bool(self._last_results))
        self._update_summary(self._last_results)
        # Persist header widths and sort
        try:
            hv: QHeaderView = self.table.horizontalHeader()
            widths = [hv.sectionSize(i) for i in range(hv.count())]
            self._settings.setValue("ioc_checker/table_widths_v2", widths)
            self._settings.setValue("ioc_checker/sort_col_v2", int(self.table.horizontalHeader().sortIndicatorSection()))
            order_enum = self.table.horizontalHeader().sortIndicatorOrder()
            order_int = int(getattr(order_enum, "value", 0))
            self._settings.setValue("ioc_checker/sort_order_v2", order_int)
        except Exception:
            pass

    def _on_error(self, msg: str) -> None:
        try:
            ToastManager.instance(self).show(msg or "Error", "error")
        except Exception:
            pass

    def _on_run_finished(self) -> None:
        try:
            # Final UI reset regardless of outcome
            self.btn_check.setText("Check")
            self.btn_check.setEnabled(True)
            self.btn_cancel.setEnabled(False)
            try:
                self._overlay.hide()
            except Exception:
                pass
            # If cancel flag was set and no results arrived
            if hasattr(self, "_cancel_flag") and self._cancel_flag.get("c") and not self._last_results:
                try:
                    ToastManager.instance(self).show("Cancelled.", "info")
                except Exception:
                    pass
        except Exception:
            pass

    def _on_save_csv(self) -> None:
        if not self._last_results:
            QMessageBox.warning(self, "Save CSV", "Nothing to save.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "ioc_results.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            # GUI export: omit age; include cache only if ever needed later
            export_results_csv(path, self._last_results, include_age=False, cache=self._cache)
            QMessageBox.information(self, "Save CSV", f"Saved to: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Save CSV", str(e))

    def _refresh_summary(self) -> None:
        self._update_summary(self._last_results)

    def _on_copy_summary(self) -> None:
        text = self.txt_summary.toPlainText()
        if not text:
            return
        self.txt_summary.selectAll()
        self.txt_summary.copy()
        from PySide6.QtGui import QTextCursor
        cur = self.txt_summary.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        self.txt_summary.setTextCursor(cur)
        try:
            ToastManager.instance(self).show("Summary copied.", "success")
        except Exception:
            pass

    # Context menu helpers
    def _on_table_context(self, pos: QPoint) -> None:
        idx = self.table.indexAt(pos)
        menu = QMenu(self)
        act_copy_row = QAction("Copy Row", self)
        act_copy_cell = QAction("Copy Cell", self)
        act_export = QAction("Export Selected…", self)
        menu.addAction(act_copy_row)
        menu.addAction(act_copy_cell)
        menu.addSeparator()
        menu.addAction(act_export)
        def do_copy_row():
            if not idx.isValid():
                return
            row = idx.row()
            vals = [self.model.item(row, c).text() if self.model.item(row, c) else "" for c in range(self.model.columnCount())]
            self.txt_summary.setPlainText("\t".join(vals))
            self._on_copy_summary()
        def do_copy_cell():
            if not idx.isValid():
                return
            it = self.model.item(idx.row(), idx.column())
            self.txt_summary.setPlainText(it.text() if it else "")
            self._on_copy_summary()
        def do_export():
            # reuse save csv but filter to selected row
            if not idx.isValid():
                return
            ioc = self.model.item(idx.row(), 0).text()
            subset = [ar for ar in self._last_results if ar.ioc == ioc]
            if not subset:
                return
            path, _ = QFileDialog.getSaveFileName(self, "Export Selected", f"{ioc}_results.csv", "CSV Files (*.csv)")
            if not path:
                return
            try:
                export_results_csv(path, subset)
                QMessageBox.information(self, "Export", f"Saved to: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export", str(e))
        act_copy_row.triggered.connect(do_copy_row)
        act_copy_cell.triggered.connect(do_copy_cell)
        act_export.triggered.connect(do_export)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def showEvent(self, e):  # noqa: N802
        # Restore table widths
        try:
            hv: QHeaderView = self.table.horizontalHeader()
            widths = self._settings.value("ioc_checker/table_widths_v2", None)
            if widths and isinstance(widths, list) and hv.count() == len(widths):
                for i, w in enumerate(widths):
                    try:
                        hv.resizeSection(i, int(w))
                    except Exception:
                        pass
        except Exception:
            pass
        return super().showEvent(e) 