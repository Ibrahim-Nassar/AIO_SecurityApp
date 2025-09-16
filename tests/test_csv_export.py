# Module map: ioc_checker.io.csv_export -> export_results_csv
from __future__ import annotations

import os
import unittest

from ioc_checker.io.csv_export import export_results_csv
from ioc_core.models import AggregatedResult, ProviderResult
from ioc_core.cache import Cache
from tests.helpers import TempDir


class TestCSVExport(unittest.TestCase):
    def test_export(self):
        with TempDir() as d:
            path = os.path.join(d, "out.csv")
            ar = AggregatedResult("https://e", "url", "CLEAN", 0.0, [ProviderResult("vt", "CLEAN", 0.0, [], None, None, False)])
            export_results_csv(path, [ar])
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                s = f.read()
                self.assertIn("vt", s)

    def test_export_bom_and_age_and_order(self):
        with TempDir() as d:
            path = os.path.join(d, "out_bom.csv")
            cache = Cache(os.path.join(d, "c.sqlite"))
            # Seed cache age
            cache.set("virustotal", "example.com", "domain", {"status": "CLEAN", "score": 0.0, "evidence": [], "raw_ref": None, "latency_ms": 0, "cached": True})
            res = [
                AggregatedResult("example.com", "domain", "INCONCLUSIVE", 0.0, [
                    ProviderResult("virustotal", "CLEAN", 0.0, [], None, None, True),
                    ProviderResult("otx", "INCONCLUSIVE", 0.0, [], None, None, True),
                ])
            ]
            export_results_csv(path, res, include_age=True, excel_bom=True, cache=cache)
            with open(path, "rb") as f:
                raw = f.read()
            # UTF-8 BOM present
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
            # Check order (virustotal before otx due to DEFAULT_PROVIDERS)
            txt = raw.decode("utf-8-sig")
            header = txt.splitlines()[0]
            self.assertTrue(header.index("virustotal") < header.index("otx"))
            # Age bucket column exists
            cols = header.split(",")
            self.assertIn("age_bucket", cols)

if __name__ == "__main__":
    unittest.main()
