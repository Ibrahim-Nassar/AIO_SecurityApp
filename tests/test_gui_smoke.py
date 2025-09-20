import pytest
import os

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from qt_app.views.main_window import MainWindow


@pytest.mark.gui
def test_gui_smoke(qapp):
    done = {"ok": False}

    def bail():
        if not done["ok"]:
            pytest.fail("GUI smoke timed out")

    # Hard timeout watchdog: fail fast instead of hanging
    QTimer.singleShot(6000, bail)

    w = MainWindow()
    try:
        w.show()
        QTest.qWait(50)

        # Navigate to IOC Checker
        w._sidebar.setCurrentRow(0)
        QTest.qWait(20)

        page = w.page_ioc
        # Uncheck all providers to avoid any worker/network
        for box in (page.chk_vt, page.chk_ab, page.chk_otx, page.chk_tf):
            box.setChecked(False)
        page.txt_in.setPlainText("example.com")
        QTest.qWait(20)

        done["ok"] = True
    finally:
        try:
            w.close()
        except Exception:
            pass
        QTest.qWait(30)


