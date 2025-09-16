# Module map: ioc_checker.models -> ProviderResult, AggregatedResult
from __future__ import annotations

import unittest

from ioc_checker.models import ProviderResult, AggregatedResult


class TestModels(unittest.TestCase):
    def test_provider_result_to_dict(self):
        pr = ProviderResult("vt", "CLEAN", 1.0, ["e1"], "ref", 50, False)
        d = pr.to_dict()
        self.assertEqual(d["provider"], "vt")
        self.assertEqual(d["status"], "CLEAN")

    def test_aggregated_result(self):
        prs = [ProviderResult("vt", "CLEAN", 1.0, [], None, 10, False)]
        ar = AggregatedResult("ioc", "url", "CLEAN", 1.0, prs)
        d = ar.to_dict()
        self.assertEqual(d["ioc"], "ioc")
        row = ar.to_row()
        self.assertIn("vt_status", row)

if __name__ == "__main__":
    unittest.main()
