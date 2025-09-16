# Module map: ioc_checker.cli.urls.run_cli
from __future__ import annotations

import asyncio
import io
import sys
import unittest
from unittest import mock

from ioc_checker.cli.urls import run_cli


class TestCliUrls(unittest.IsolatedAsyncioTestCase):
    async def test_cli_run(self):
        # Patch providers to avoid network: run_cli builds providers internally, but they won't be used due to no API keys
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            await run_cli(["https://example.com"], ["virustotal"], out_path="", timeout=0.1, concurrency=1)
        s = out.getvalue().strip()
        self.assertTrue(s.startswith("type,ioc"))

if __name__ == "__main__":
    unittest.main()
