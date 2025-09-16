# Module map: ioc_checker.providers.virustotal.VirusTotalProvider
from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest import mock

import httpx

from ioc_checker.providers.virustotal import VirusTotalProvider
from tests.helpers import FakeAsyncClient, make_response


class TestVTProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        os.environ["VIRUSTOTAL_API_KEY"] = "test"

    async def test_ok_parse(self):
        prov = VirusTotalProvider("k")
        fake = FakeAsyncClient()
        with open(os.path.join(os.path.dirname(__file__), "fixtures", "vt_ok.json"), "r", encoding="utf-8") as f:
            fake.queue(make_response(200, json.load(f)))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "1.2.3.4", "ip", 10.0)
        self.assertIn(pr.status, ("MALICIOUS", "SUSPICIOUS", "CLEAN", "INCONCLUSIVE"))
        self.assertTrue(isinstance(pr.score, float))

    async def test_429(self):
        prov = VirusTotalProvider("k")
        fake = FakeAsyncClient()
        fake.queue(make_response(429, {"error": "rate limit"}))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "1.2.3.4", "ip", 10.0)
        self.assertEqual(pr.status, "INCONCLUSIVE")

    async def test_404(self):
        prov = VirusTotalProvider("k")
        fake = FakeAsyncClient()
        fake.queue(make_response(404, {}))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "1.2.3.4", "ip", 10.0)
        self.assertEqual(pr.status, "CLEAN")

    async def test_malformed_json(self):
        prov = VirusTotalProvider("k")
        class BadClient(FakeAsyncClient):
            async def get(self, url, *a, **k):
                r = make_response(200, None)
                r._content = b"not json"
                return r
        fake = BadClient()
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "1.2.3.4", "ip", 10.0)
        self.assertEqual(pr.status, "INCONCLUSIVE")

if __name__ == "__main__":
    unittest.main()
