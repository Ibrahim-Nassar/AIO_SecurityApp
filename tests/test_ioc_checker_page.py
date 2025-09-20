import os
import csv

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from qt_app.views.ioc_checker_page import IocCheckerPage
from ioc_core import services as core_services


def fake_httpx_response(code, data):
    from tests.conftest import FakeResponse
    return FakeResponse(code, json_data=data)


def test_ioc_checker_run_and_export(qapp, temp_cwd, fake_httpx, qt_flush, monkeypatch):
    # Ensure providers are available
    monkeypatch.setenv("VIRUSTOTAL_API_KEY", "k")
    monkeypatch.setenv("ABUSEIPDB_API_KEY", "k")
    monkeypatch.setenv("OTX_API_KEY", "k")
    # Fake provider responses
    vt_data = {"data": {"attributes": {"last_analysis_stats": {"malicious": 0, "suspicious": 1, "harmless": 3, "undetected": 10}}}}
    ab_data = {"data": {"abuseConfidenceScore": 0, "totalReports": 0, "isPublic": True}}
    otx_data = {"pulse_info": {"count": 1, "pulses": [{"name": "TestPulse"}]}}
    tf_body = {"query_status": "ok", "data": []}
    fake_httpx["set_routes"]([
        ("GET", "/api/v3/ip_addresses/1.1.1.1", fake_httpx_response(200, vt_data)),
        ("GET", "/api/v2/check", fake_httpx_response(200, ab_data)),
        ("GET", "/api/v1/indicators/IPv4/1.1.1.1/general", fake_httpx_response(200, otx_data)),
        ("POST", "/api/v1/", fake_httpx_response(200, tf_body)),
    ])
    status_msgs = []
    page = IocCheckerPage(lambda s: status_msgs.append(s))
    page.show(); qt_flush()
    page.txt_in.setPlainText("1.1.1.1")
    page.btn_check.click(); qt_flush(50)
    # wait for worker
    for _ in range(20):
        qt_flush(25)
        if page._last_results:
            break
    assert page._last_results
    # UI invariants
    assert page.lbl_mode.text().lower() == "mode: normal"
    assert page.btn_check.text() == "Check"
    page.show(); qt_flush()
    # Check button should have minimum width of 110, others 100
    assert page.btn_check.width() >= 110
    assert page.btn_save.width() >= 100
    assert page.btn_cancel.width() >= 100
    # Table populated
    assert page.model.rowCount() >= 1
    # Summary selection
    page.table.selectRow(0); qt_flush()
    assert "IOC:" in page.txt_summary.toPlainText()
    # Copy summary (content present)
    page._on_copy_summary(); qt_flush()
    # Export CSV
    out = temp_cwd / "out.csv"
    # Monkeypatch dialog to return path without UI
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(out), "CSV Files (*.csv)")))
    page._on_save_csv(); qt_flush()
    assert out.exists()
    with open(out, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0][0:2] == ["type", "ioc"]
    # Ensure no Clear Cache button exists
    from PySide6.QtWidgets import QPushButton
    def find_clear(widget):
        for btn in widget.findChildren(QPushButton):
            if btn.text().strip().lower() == "clear cache":
                return True
        return False
    assert not find_clear(page)


def test_ioc_checker_cancel(qapp, fake_httpx, qt_flush):
    # Long-running fake to allow cancel
    def slow_resp(method, url):
        from tests.conftest import FakeResponse
        return FakeResponse(200, json_data={"data": {"attributes": {"last_analysis_stats": {"malicious": 0, "suspicious": 0, "harmless": 0, "undetected": 0}}}})
    fake_httpx["set_routes"]([
        ("GET", "/api/v3/ip_addresses/9.9.9.9", slow_resp),
    ])
    status_msgs = []
    page = IocCheckerPage(lambda s: status_msgs.append(s))
    page.show(); qt_flush()
    page.txt_in.setPlainText("9.9.9.9")
    page.btn_check.click(); qt_flush(10)
    page._on_cancel(); qt_flush(50)
    # Buttons should re-enable once worker finishes; poll a bit
    for _ in range(20):
        qt_flush(25)
        if page.btn_check.isEnabled():
            break
    assert page.btn_check.isEnabled() 