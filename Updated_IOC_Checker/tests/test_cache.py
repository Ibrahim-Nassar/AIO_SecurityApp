# Module map: ioc_checker.utils.cache -> Cache
from __future__ import annotations

import os
import time
import unittest

from ioc_checker.utils.cache import Cache
from tests.helpers import TempDir, freeze_time


class TestCache(unittest.TestCase):
    def test_set_get_and_ttl(self):
        with TempDir() as d:
            path = os.path.join(d, "c.sqlite")
            c = Cache(path)
            with freeze_time(1000):
                c.set("p", "ioc", "url", {"status": "CLEAN", "score": 1.0, "evidence": [], "raw_ref": None, "latency_ms": 1, "cached": True})
                got = c.get("p", "ioc", max_age=60)
                self.assertIsNotNone(got)
            with freeze_time(2000):
                miss = c.get("p", "ioc", max_age=60)
                self.assertIsNone(miss)

if __name__ == "__main__":
    unittest.main()
