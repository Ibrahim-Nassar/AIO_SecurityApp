# Module map: ioc_checker.providers.virustotal.VirusTotalProvider
from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest import mock

import pytest
import httpx

from ioc_checker.providers.virustotal import VirusTotalProvider
from tests.helpers import FakeAsyncClient, make_response


@pytest.mark.providers
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
        # Queue 429 then success
        class Client(FakeAsyncClient):
            async def get(self, url, *a, **k):
                if not hasattr(self, "_count"):
                    self._count = 0
                self._count += 1
                if self._count == 1:
                    return make_response(429, {"error": "rate limit"})
                with open(os.path.join(os.path.dirname(__file__), "fixtures", "vt_ok.json"), "r", encoding="utf-8") as f:
                    return make_response(200, json.load(f))
        fake = Client()
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "1.2.3.4", "ip", 0.2)
        self.assertIn(pr.status, ("MALICIOUS", "SUSPICIOUS", "CLEAN", "INCONCLUSIVE"))
        # latency should be recorded as int
        self.assertTrue(isinstance(pr.latency_ms, int) or pr.latency_ms is None)

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
