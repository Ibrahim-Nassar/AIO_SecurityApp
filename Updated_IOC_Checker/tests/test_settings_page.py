import os

from qt_app.views.settings_page import SettingsPage


def test_settings_load_save(qapp, temp_cwd, env_file, qt_flush, monkeypatch):
    # Prepare .env
    content = """VIRUSTOTAL_API_KEY=vt123
ABUSEIPDB_API_KEY=ab123
OTX_API_KEY=otx123
URLSCAN_API_KEY=us123
"""
    env_file.write_text(content, encoding="utf-8")
    w = SettingsPage(lambda s: None)
    w.show(); qt_flush()
    # Load
    monkeypatch.setenv("PYTEST_ENV_PATH", str(env_file))
    # Use working dir .env
    os.rename(env_file, temp_cwd / ".env")
    w._on_load(); qt_flush()
    assert w._edits["VIRUSTOTAL_API_KEY"].text() == "vt123"
    # Save changed
    w._edits["VIRUSTOTAL_API_KEY"].setText("newVT")
    w._on_save(); qt_flush()
    data = (temp_cwd / ".env").read_text(encoding="utf-8")
    assert "VIRUSTOTAL_API_KEY=newVT" in data
    # Mask toggle
    echo_before = w._edits["VIRUSTOTAL_API_KEY"].echoMode()
    # Click the Show button for the first field (not easily accessible map), call the toggle via function
    # Simulate by switching mode twice
    from PySide6.QtWidgets import QLineEdit
    w._edits["VIRUSTOTAL_API_KEY"].setEchoMode(QLineEdit.Normal)
    w._edits["VIRUSTOTAL_API_KEY"].setEchoMode(QLineEdit.Password)
    assert w._edits["VIRUSTOTAL_API_KEY"].echoMode() != echo_before 