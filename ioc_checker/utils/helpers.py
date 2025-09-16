from __future__ import annotations

# Compatibility shim: re-export helpers from core
from ioc_core.models import classify_ioc, vt_url_id, now_utc  # noqa: F401

# Keep normalize_target_url as it is specific to CLI/tests under legacy path
from urllib.parse import urlparse

def normalize_target_url(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        raise ValueError("Empty URL")
    if "://" not in s:
        s = "http://" + s
    u = urlparse(s)
    if not u.netloc:
        raise ValueError("Invalid URL: missing host")
    return s


