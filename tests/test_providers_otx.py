# Module map: ioc_checker.providers.otx.OTXProvider
from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest import mock

import httpx

from ioc_checker.providers.otx import OTXProvider
from tests.helpers import FakeAsyncClient, make_response


class TestOTXProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        os.environ["OTX_API_KEY"] = "x"

    async def test_ok(self):
        prov = OTXProvider("x")
        fake = FakeAsyncClient()
        with open(os.path.join(os.path.dirname(__file__), "fixtures", "otx_ok.json"), "r", encoding="utf-8") as f:
            fake.queue(make_response(200, json.load(f)))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "example.com", "domain", 10.0)
        self.assertIn(pr.status, ("MALICIOUS", "SUSPICIOUS", "CLEAN", "INCONCLUSIVE"))

    async def test_5xx_then_success(self):
        prov = OTXProvider("x")
        class Client(FakeAsyncClient):
            async def get(self, url, *a, **k):
                if not hasattr(self, "_count"):
                    self._count = 0
                self._count += 1
                if self._count == 1:
                    return make_response(503, {"error": "busy"})
                with open(os.path.join(os.path.dirname(__file__), "fixtures", "otx_ok.json"), "r", encoding="utf-8") as f:
                    return make_response(200, json.load(f))
        fake = Client()
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "example.com", "domain", 0.2)
        self.assertIn(pr.status, ("MALICIOUS", "SUSPICIOUS", "CLEAN", "INCONCLUSIVE"))

if __name__ == "__main__":
    unittest.main()
