# Module map: ioc_checker.services.ioc_service -> enrich_one, aggregate
from __future__ import annotations

import asyncio
import unittest
from unittest import mock

import httpx

from ioc_checker.models import ProviderResult
from ioc_checker.services.ioc_service import enrich_one
from ioc_checker.utils.cache import Cache


class DummyProvider:
    def __init__(self, name, status="CLEAN", score=1.0, supports={"url"}, ok=True):
        self.name = name
        self._status = status
        self._score = score
        self._supports = set(supports)
        self._ok = ok

    def available(self):
        return True

    def supports(self, t: str) -> bool:
        return t in self._supports

    async def query(self, client, ioc, ioc_type, timeout):
        if not self._ok:
            raise RuntimeError("fail")
        return ProviderResult(self.name, self._status, self._score, [], None, None, False)


class TestIocService(unittest.IsolatedAsyncioTestCase):
    async def test_enrich_one_with_partial_failures(self):
        cache = Cache(":memory:")
        providers = [
            DummyProvider("a", "CLEAN", 0.0),
            DummyProvider("b", "INCONCLUSIVE", 0.0, ok=False),
        ]
        async with httpx.AsyncClient() as client:
            ar = await enrich_one("https://example.com", providers, cache, {"a": 10, "b": 10}, True, False, 5.0, 2)
        self.assertEqual(ar.ioc_type, "url")
        self.assertEqual(len(ar.providers), 2)

if __name__ == "__main__":
    unittest.main()
