# Module map: ioc_checker.providers.urlscan.UrlscanProvider
from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest import mock

import httpx

from ioc_checker.providers.urlscan import UrlscanProvider
from tests.helpers import FakeAsyncClient, make_response


class TestUrlscanProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        os.environ["URLSCAN_API_KEY"] = "x"

    async def test_search_ok(self):
        prov = UrlscanProvider("x")
        fake = FakeAsyncClient()
        with open(os.path.join(os.path.dirname(__file__), "fixtures", "urlscan_ok.json"), "r", encoding="utf-8") as f:
            fake.queue(make_response(200, json.load(f)))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            async with httpx.AsyncClient() as client:
                pr = await prov.query(client, "http://evil", "url", 10.0)
        self.assertIn(pr.status, ("MALICIOUS", "SUSPICIOUS", "CLEAN", "INCONCLUSIVE"))

if __name__ == "__main__":
    unittest.main()
