# Module map: ioc_checker.utils.helpers -> classify_ioc, normalize_target_url, vt_url_id, now_utc
from __future__ import annotations

import base64
import unittest

from ioc_checker.utils.helpers import classify_ioc, normalize_target_url, vt_url_id, now_utc
from ioc_core.cache import age_bucket


class TestUtils(unittest.TestCase):
    def test_classify_ioc(self):
        ok, t, norm, err = classify_ioc("https://example.com")
        self.assertTrue(ok); self.assertEqual(t, "url"); self.assertEqual(norm, "https://example.com")
        ok, t, norm, err = classify_ioc("1.2.3.4")
        self.assertTrue(ok); self.assertEqual(t, "ip")
        ok, t, norm, err = classify_ioc("test.example.com")
        self.assertTrue(ok); self.assertEqual(t, "domain")
        ok, t, norm, err = classify_ioc("a"*64)
        self.assertTrue(ok); self.assertEqual(t, "hash")
        ok, t, norm, err = classify_ioc("bad input!!")
        self.assertFalse(ok); self.assertEqual(t, "invalid")

    def test_normalize_target_url(self):
        self.assertEqual(normalize_target_url("example.com"), "http://example.com")
        self.assertEqual(normalize_target_url("  https://x  "), "https://x")
        with self.assertRaises(ValueError):
            normalize_target_url(" ")

    def test_vt_url_id(self):
        enc = vt_url_id("http://x")
        # Confirm padding stripped and reversible
        raw = base64.urlsafe_b64decode((enc + "===").encode("ascii")).decode("utf-8")
        self.assertEqual(raw, "http://x")

    def test_now_utc(self):
        n = now_utc()
        self.assertIsInstance(n, int)

    def test_age_bucket(self):
        self.assertEqual(age_bucket(None), "unknown")
        self.assertEqual(age_bucket(10), "<1h")
        self.assertEqual(age_bucket(3600), "1–24h")
        self.assertEqual(age_bucket(86000), "1–24h")
        self.assertEqual(age_bucket(90000), ">24h")

if __name__ == "__main__":
    unittest.main()
