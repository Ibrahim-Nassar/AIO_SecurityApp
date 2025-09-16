from __future__ import annotations

import contextlib
import io
import json
import os
import time as _time
import types
from typing import Any, Dict, Optional
from unittest import mock

import httpx


def make_response(status: int = 200, json_obj: Any | None = None, headers: Dict[str, str] | None = None, url: str = "/") -> httpx.Response:
    req = httpx.Request("GET", url)
    content: bytes
    if json_obj is None:
        content = b""
    else:
        content = json.dumps(json_obj).encode("utf-8")
    resp = httpx.Response(status_code=status, headers=headers or {}, content=content, request=req)
    return resp


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self._queue: list[httpx.Response] = []
        self.base_url = kwargs.get("base_url")
        self.timeout = kwargs.get("timeout")
        self.follow_redirects = kwargs.get("follow_redirects", False)

    def queue(self, response: httpx.Response) -> None:
        self._queue.append(response)

    async def get(self, url: str, *args, **kwargs) -> httpx.Response:
        if not self._queue:
            raise RuntimeError("FakeAsyncClient queue empty for GET")
        return self._queue.pop(0)

    async def post(self, url: str, *args, **kwargs) -> httpx.Response:
        if not self._queue:
            raise RuntimeError("FakeAsyncClient queue empty for POST")
        return self._queue.pop(0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@contextlib.contextmanager
def block_network():
    def _raise(*args, **kwargs):
        raise AssertionError("Real network usage is forbidden in tests")
    with mock.patch("httpx.get", _raise), mock.patch("httpx.post", _raise), mock.patch("httpx.Client", _raise):
        yield


@contextlib.contextmanager
def freeze_time(ts: float):
    class _T:
        @staticmethod
        def time():
            return ts
    with mock.patch("time.time", _T.time):
        yield


class TempDir(contextlib.AbstractContextManager):
    def __init__(self):
        import tempfile
        self._dir = tempfile.mkdtemp(prefix="ioc_tests_")

    def __enter__(self):
        return self._dir

    def __exit__(self, exc_type, exc, tb):
        import shutil
        try:
            shutil.rmtree(self._dir, ignore_errors=True)
        except Exception:
            pass
        return False
