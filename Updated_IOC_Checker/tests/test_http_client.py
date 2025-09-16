# Module map: ioc_checker.net.http_client -> create_async_client
from __future__ import annotations

import asyncio
import unittest

from ioc_checker.net.http_client import create_async_client


class TestHttpClient(unittest.TestCase):
    def test_create_async_client(self):
        c = create_async_client(5.0)
        self.assertTrue(getattr(c, "follow_redirects", False))
        async def _close():
            await c.aclose()
        asyncio.run(_close())

if __name__ == "__main__":
    unittest.main()
