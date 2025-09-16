from __future__ import annotations

import json
import sqlite3
import threading
import time
from typing import Any, Dict, Optional, cast


class Cache:
    """Lightweight SQLite-backed cache.

    Table: cache(provider TEXT, ioc TEXT, type TEXT, fetched_at INTEGER, payload TEXT,
    PRIMARY KEY(provider,ioc))
    """

    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (provider TEXT, ioc TEXT, type TEXT, fetched_at INTEGER, payload TEXT, PRIMARY KEY(provider,ioc))"
        )
        self._migrate_schema_if_needed()
        self.conn.commit()
        self.lock = threading.Lock()

    def _migrate_schema_if_needed(self) -> None:
        try:
            cols = [r[1] for r in self.conn.execute("PRAGMA table_info(cache)").fetchall()]
            if "type" not in cols:
                self.conn.execute("ALTER TABLE cache ADD COLUMN type TEXT")
            self.conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_cache_provider_ioc ON cache(provider, ioc)"
            )
        except Exception:
            pass

    def get(self, provider: str, ioc: str, max_age: int) -> Optional[Dict[str, Any]]:
        with self.lock:
            cur = self.conn.execute("SELECT fetched_at, payload FROM cache WHERE provider=? AND ioc= ?", (provider, ioc))
            row = cur.fetchone()
        if not row:
            return None
        fetched_at, payload = row
        if int(time.time()) - int(fetched_at) > max_age:
            return None
        try:
            return cast(Dict[str, Any], json.loads(payload))
        except Exception:
            return None

    def get_age(self, provider: str, ioc: str) -> Optional[int]:
        """Return age in seconds for (provider,ioc) if present; otherwise None."""
        with self.lock:
            cur = self.conn.execute(
                "SELECT fetched_at FROM cache WHERE provider=? AND ioc=?",
                (provider, ioc),
            )
            row = cur.fetchone()
        if not row:
            return None
        fetched_at = int(row[0])
        age = int(time.time()) - fetched_at
        if age < 0:
            return 0
        return age

    def set(self, provider: str, ioc: str, ioc_type: str, payload: Dict[str, Any]) -> None:
        with self.lock:
            self.conn.execute(
                "REPLACE INTO cache (provider, ioc, type, fetched_at, payload) VALUES (?,?,?,?,?)",
                (provider, ioc, ioc_type, int(time.time()), json.dumps(payload)),
            )
            self.conn.commit()

    def clear(self) -> None:
        with self.lock:
            try:
                self.conn.execute("DELETE FROM cache")
                self.conn.commit()
            except Exception:
                pass


def age_bucket(age_seconds: Optional[int]) -> str:
    """Map age in seconds to bucket label.

    <1h, 1–24h, >24h; 'unknown' if None.
    """
    if age_seconds is None:
        return "unknown"
    if age_seconds < 3600:
        return "<1h"
    if age_seconds < 86400:
        return "1–24h"
    return ">24h" 