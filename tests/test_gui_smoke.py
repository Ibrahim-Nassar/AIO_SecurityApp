import os

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from qt_app.views.main_window import MainWindow


def test_gui_smoke(qapp):
    # Ensure offscreen in CI; local runs may have a display
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    w = MainWindow()
    w.show()
    QTest.qWait(20)

    # Navigate to IOC Checker (index 0) and interact
    w._sidebar.setCurrentRow(0)
    QTest.qWait(10)

    page = w.page_ioc
    # Uncheck all providers to keep fully offline
    page.chk_vt.setChecked(False)
    page.chk_ab.setChecked(False)
    page.chk_otx.setChecked(False)
    page.chk_tf.setChecked(False)
    QTest.qWait(5)

    # Input a dummy IOC and press Check; overlay should show briefly and not crash
    page.txt_in.setPlainText("example.com")
    QTest.qWait(5)
    page._on_check()
    QTest.qWait(30)

    assert w.isVisible()


