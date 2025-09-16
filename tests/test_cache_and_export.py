import os
import csv
import time

from ioc_core.cache import Cache as CoreCache
from ioc_core.models import AggregatedResult, ProviderResult
from ioc_core.export import export_results_csv


def test_cache_set_get_ttl(tmp_path):
    db = tmp_path / "cache.sqlite"
    c = CoreCache(str(db))
    pr = ProviderResult("vt", "CLEAN", 0.0, [], None, 10, False)
    ar = {"provider": pr.provider, "status": pr.status, "score": pr.score, "evidence": [], "raw_ref": None, "latency_ms": 10, "cached": False}
    c.set("vt", "example.com", "domain", ar)
    got = c.get("vt", "example.com", 3600)
    assert got is not None and got.get("status") == "CLEAN"
    # TTL expiration
    # simulate old fetched_at by direct update
    with c.lock:
        c.conn.execute("UPDATE cache SET fetched_at=? WHERE provider=? AND ioc=?", (0, "vt", "example.com"))
        c.conn.commit()
    assert c.get("vt", "example.com", 1) is None


def test_export_csv_utf8_newlines(tmp_path):
    path = tmp_path / "out.csv"
    res = [
        AggregatedResult("example.com", "domain", "INCONCLUSIVE", 0.0, [
            ProviderResult("virustotal", "CLEAN", 0.0, [], None, None, False),
            ProviderResult("otx", "INCONCLUSIVE", 0.0, [], None, None, False),
        ])
    ]
    export_results_csv(str(path), res)
    # Verify file exists and basic columns
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    assert rows[0][0:2] == ["type", "ioc"]
    assert "virustotal" in rows[0]
    assert any("CLEAN" in cell for cell in rows[1]) 