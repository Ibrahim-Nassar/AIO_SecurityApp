from PySide6.QtWidgets import QWidget
from PySide6.QtTest import QTest

from qt_app.ui import Toast


def test_toast_shows_and_disposes(qapp):
    host = QWidget()
    host.resize(400, 300)
    host.show()
    QTest.qWait(10)

    toast = Toast(host)
    toast.show_toast(host, "Hello", msec=200)
    QTest.qWait(20)
    assert toast.isVisible()

    # wait past fade-out; allow time for deleteLater cleanup
    QTest.qWait(600)
    # Widget should be hidden and scheduled for deletion; isVisible should be False
    assert not toast.isVisible()


