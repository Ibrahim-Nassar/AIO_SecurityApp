import os
import sys
import types
import asyncio
import contextlib
import builtins

import pytest

# Force headless Qt for tests
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Ensure repo root on sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture()
def temp_cwd(tmp_path, monkeypatch):
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old)


@pytest.fixture()
def env_file(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    monkeypatch.setenv("PYTEST_ENV_PATH", str(env_path))
    yield env_path


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text="", headers=None):
        self.status_code = status_code
        self._json = json_data
        self.text = text
        self.headers = headers or {"content-type": "application/json"}
    def json(self):
        if isinstance(self._json, Exception):
            raise self._json
        return self._json


class FakeAsyncClient:
    def __init__(self, routes):
        self.routes = routes  # list of (method, url_suffix or path, response or callable)
        self.base_url = ""
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def get(self, url, *args, **kwargs):
        return await self._handle("GET", url)
    async def post(self, url, *args, **kwargs):
        return await self._handle("POST", url)
    async def _handle(self, method, url):
        for m, match, resp in self.routes:
            if m == method and (url.endswith(match) or match in url):
                if callable(resp):
                    return resp(method, url)
                return resp
        return FakeResponse(404, json_data={})


@pytest.fixture()
def fake_httpx(monkeypatch):
    calls = {"count": 0}
    routes = []
    def set_routes(r):
        routes.clear(); routes.extend(r)
    class _Timeout:
        def __init__(self, *a, **k):
            pass
    class _ClientFactory:
        def __init__(self, *a, **k):
            self._routes = list(routes)
        async def __aenter__(self):
            return FakeAsyncClient(self._routes)
        async def __aexit__(self, et, ev, tb):
            return False
    import httpx
    monkeypatch.setattr(httpx, "Timeout", _Timeout, raising=True)
    monkeypatch.setattr(httpx, "AsyncClient", _ClientFactory, raising=True)
    return {"set_routes": set_routes, "calls": calls}


@pytest.fixture()
def qt_flush(qapp):
    def _f(ms=10):
        QTest.qWait(ms)
    return _f 