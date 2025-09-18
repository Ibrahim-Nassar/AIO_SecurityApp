import sys

from PySide6.QtCore import QResource
from PySide6.QtWidgets import QApplication

from qt_app.views.main_window import MainWindow
from qt_app.ui import apply_app_styles, Toast
from ioc_core import setup_logging_redaction
from ioc_core.logger import setup_diagnostics_logger
from qt_app.ui.theme import FONT_SIZE_BASE
from pathlib import Path
import os
import platform
from dotenv import load_dotenv
from ioc_core.config_env import resolve_env_path, load_env_file


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
    setup_diagnostics_logger()
    # Load per-user .env on startup (migrate from CWD if needed)
    env_path = Path(resolve_env_path())
    try:
        if not env_path.exists():
            cwd_env = Path.cwd() / ".env"
            if cwd_env.exists():
                env_path.parent.mkdir(parents=True, exist_ok=True)
                env_path.write_text(cwd_env.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass
    _register_resources()
    app = QApplication(sys.argv)
    apply_app_styles(app)
    w = MainWindow()
    # Attempt to load env and show a lightweight toast
    try:
        loaded = load_env_file(str(env_path))
        try:
            if loaded:
                Toast(w).show_toast(w, "Environment loaded.")
            else:
                Toast(w).show_toast(w, "Failed to load environment.")
        except Exception:
            pass
    except Exception:
        pass
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 