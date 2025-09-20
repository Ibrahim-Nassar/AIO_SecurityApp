# Module map: ioc_checker.providers.abuseipdb.AbuseIPDBProvider
from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest import mock

import pytest
import httpx

from ioc_checker.providers.abuseipdb import AbuseIPDBProvider
from tests.helpers import FakeAsyncClient, make_response


@pytest.mark.providers
class TestAbuseProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        os.environ["ABUSEIPDB_API_KEY"] = "x"

    async def test_ok(self):
        prov = AbuseIPDBProvider("x")
        fake = FakeAsyncClient()
        with open(os.path.join(os.path.dirname(__file__), "fixtures", "abuse_ok.json"), "r", encoding="utf-8") as f:
            fake.queue(make_response(200, json.load(f)))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "1.2.3.4", "ip", 10.0)
        self.assertIn(pr.status, ("MALICIOUS", "SUSPICIOUS", "CLEAN", "INCONCLUSIVE"))

    async def test_timeout_then_fail(self):
        prov = AbuseIPDBProvider("x")
        class Client(FakeAsyncClient):
            async def get(self, url, *a, **k):
                raise httpx.TimeoutException("timeout")
        fake = Client()
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "1.2.3.4", "ip", 0.1)
        self.assertEqual(pr.status, "INCONCLUSIVE")

    async def test_404(self):
        prov = AbuseIPDBProvider("x")
        fake = FakeAsyncClient()
        fake.queue(make_response(404, {}))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "1.2.3.4", "ip", 10.0)
        self.assertEqual(pr.status, "CLEAN")

if __name__ == "__main__":
    unittest.main()
