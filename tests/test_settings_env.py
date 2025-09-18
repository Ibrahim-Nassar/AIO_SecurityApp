import os
from pathlib import Path

from qt_app.views.settings_page import SettingsPage
from ioc_core.config_env import resolve_env_path


def test_settings_env_persist(qapp, tmp_path, monkeypatch, qt_flush):
    # Point per-user dir into tmp_path by patching HOME/LOCALAPPDATA
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    # Ensure clean start
    env_path = Path(resolve_env_path())
    if env_path.exists():
        env_path.unlink()

    w = SettingsPage(lambda s: None)
    w.show(); qt_flush()

    # Enter mock keys and save
    w._edits["VIRUSTOTAL_API_KEY"].setText("vt_key")
    w._edits["ABUSEIPDB_API_KEY"].setText("ab_key")
    w._edits["OTX_API_KEY"].setText("otx_key")
    w._on_save(); qt_flush()

    assert env_path.exists()
    data = env_path.read_text(encoding="utf-8")
    assert "VIRUSTOTAL_API_KEY=vt_key" in data
    assert "ABUSEIPDB_API_KEY=ab_key" in data
    assert "OTX_API_KEY=otx_key" in data

    # Clear fields, then reload via button and ensure repopulation
    for k in ("VIRUSTOTAL_API_KEY", "ABUSEIPDB_API_KEY", "OTX_API_KEY"):
        w._edits[k].setText("")
    w._on_load(); qt_flush()
    assert w._edits["VIRUSTOTAL_API_KEY"].text() == "vt_key"
    assert w._edits["ABUSEIPDB_API_KEY"].text() == "ab_key"
    assert w._edits["OTX_API_KEY"].text() == "otx_key"


