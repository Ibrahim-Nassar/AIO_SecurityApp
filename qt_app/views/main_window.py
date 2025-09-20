# CHANGELOG:
# - Replaced tabs with sidebar navigation + toolbar + stacked pages inside a QSplitter
# - Persisted window geometry and sidebar width via QSettings
# - Toolbar actions proxy to current page methods without renaming existing page widgets
from PySide6.QtWidgets import QMainWindow, QApplication, QTabWidget, QStatusBar, QWidget, QListWidget, QStackedWidget, QVBoxLayout, QSplitter, QStyle, QListWidgetItem, QMessageBox
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon, QAction

from .ioc_checker_page import IocCheckerPage
from .settings_page import SettingsPage
from .assistant_page import AssistantPage
from ioc_core.version import __version__
from datetime import datetime


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"IOC Checker (Qt) v{__version__}")
        try:
            QApplication.setStyle("Fusion")
        except Exception:
            pass
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._settings = QSettings("UpdatedIOCChecker", "QtApp")

        # Pages
        self.page_ioc = IocCheckerPage(self.set_status_text, self)
        self.page_settings = SettingsPage(self.set_status_text, self)
        self.page_assistant = AssistantPage(self.set_status_text, self)

        # Sidebar navigation
        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(200)
        self._sidebar.setAlternatingRowColors(False)
        self._sidebar.setStyleSheet("QListWidget::item{height:32px;} QListWidget::item:selected{background:#e0f2f1; font-weight:600;}")
        self._sidebar.addItem(self._make_item("Home/IOC Checker", QIcon(":/icons/home.svg")))
        self._sidebar.addItem(self._make_item("Assistant", QIcon(":/icons/search.svg")))
        self._sidebar.addItem(self._make_item("Settings", QIcon(":/icons/settings.svg")))
        # Restore last page
        try:
            last_obj = self._settings.value("main/lastPage", 0)
            last_idx = int(last_obj) if isinstance(last_obj, (int, str)) else 0
        except Exception:
            last_idx = 0
        self._sidebar.setCurrentRow(max(0, min(3, last_idx)))

        # Stack
        self._stack = QStackedWidget()
        self._stack.addWidget(self.page_ioc)
        self._stack.addWidget(self.page_assistant)
        self._stack.addWidget(self.page_settings)

        # Splitter
        self._split = QSplitter()
        self._split.addWidget(self._sidebar)
        self._split.addWidget(self._stack)
        self._split.setStretchFactor(1, 1)
        self._restore_splitter()

        # Central widget
        cw = QWidget()
        lay = QVBoxLayout(cw)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._split)
        self.setCentralWidget(cw)

        # Signals
        self._sidebar.currentRowChanged.connect(self._on_navigate)
        # Initialize enablement state
        self._on_navigate(self._sidebar.currentRow())

        # About action (minimal)
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        self._status.addPermanentWidget(QWidget())  # spacer
        self._status.addAction(about_action)

    def _make_item(self, text: str, icon: QIcon) -> QListWidgetItem:
        it = QListWidgetItem(icon, text)
        it.setTextAlignment(int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
        return it

    def _restore_splitter(self) -> None:
        try:
            geo = self._settings.value("main/geometry", None)
            if geo:
                self.restoreGeometry(geo)  # type: ignore[arg-type]
            state = self._settings.value("main/windowState", None)
            if state:
                self.restoreState(state)  # type: ignore[arg-type]
            sizes = self._settings.value("main/sidebar", None)
            if sizes and isinstance(sizes, list):
                try:
                    sizes = [int(x) for x in sizes]
                except Exception:
                    sizes = None
            if sizes:
                self._split.setSizes(sizes)  # type: ignore[arg-type]
            else:
                self._split.setSizes([200, 900])
        except Exception:
            self._split.setSizes([200, 900])

    def closeEvent(self, e):  # noqa: N802
        try:
            self._settings.setValue("main/geometry", self.saveGeometry())
            self._settings.setValue("main/windowState", self.saveState())
            self._settings.setValue("main/sidebar", self._split.sizes())
            self._settings.setValue("main/lastPage", self._sidebar.currentRow())
        except Exception:
            pass
        return super().closeEvent(e)

    def set_status_text(self, text: str) -> None:
        self.statusBar().showMessage(text or "", 5000)

    def _on_navigate(self, idx: int) -> None:
        try:
            self._stack.setCurrentIndex(idx)
        except Exception:
            pass

    def _show_about(self) -> None:
        try:
            build_date = datetime.utcnow().strftime("%Y-%m-%d")
            providers = "VirusTotal, OTX, AbuseIPDB"
            QMessageBox.information(
                self,
                "About IOC Checker",
                f"IOC Checker\nVersion: {__version__}\nBuild date: {build_date}\nProviders: {providers}"
            )
        except Exception:
            pass 