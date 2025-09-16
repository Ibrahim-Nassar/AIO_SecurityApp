import sys

from PySide6.QtCore import QResource
from PySide6.QtWidgets import QApplication

from qt_app.views.main_window import MainWindow
from qt_app.ui import apply_app_styles
from ioc_core import setup_logging_redaction
from qt_app.ui.theme import FONT_SIZE_BASE


def _register_resources() -> None:
    # Best-effort registration; if pyrcc not used, try to register .qrc at runtime
    try:
        # PySide6 supports registering binary rcc, not .qrc; skip if not compiled
        # Users can compile via: pyside6-rcc qt_app/res/resources.qrc -o qt_app/res/resources_rc.py
        # If compiled module exists, import it to register
        from qt_app.res import resources_rc  # type: ignore
        _ = resources_rc  # pragma: no cover
    except Exception:
        # No precompiled resources; continue without icons
        pass


def main() -> None:
    setup_logging_redaction()
    _register_resources()
    app = QApplication(sys.argv)
    apply_app_styles(app)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 