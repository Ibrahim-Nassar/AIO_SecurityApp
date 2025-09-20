from PySide6.QtWidgets import QWidget
from PySide6.QtTest import QTest

from qt_app.ui import ToastManager


def test_toast_shows_and_disposes(qapp):
    host = QWidget()
    host.resize(400, 300)
    host.show()
    QTest.qWait(10)

    manager = ToastManager.instance(host)
    manager.show("Hello", "info", 200)
    QTest.qWait(20)
    
    toast = manager._toast
    assert toast is not None
    assert toast.isVisible()

    # wait past fade-out
    QTest.qWait(600)
    # Widget should be hidden
    assert not toast.isVisible()


