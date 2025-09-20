import pytest
from unittest import mock

import httpx

from ioc_core import services as core_services
from ioc_core.cache import Cache


@pytest.mark.providers
@pytest.mark.asyncio
async def test_http_get_with_retries_uses_timeout_and_does_not_disable_verify(monkeypatch):
    calls = {"get": []}

    class FakeResponse:
        def __init__(self):
            self.status_code = 200
        def json(self):
            return {}

    async def fake_get(url, headers=None, params=None, timeout=None, **kwargs):
        calls["get"].append({"timeout": timeout, **kwargs})
        return FakeResponse()

    class FakeClient:
        async def get(self, *a, **k):
            return await fake_get(*a, **k)

    client = FakeClient()
    r = await core_services._http_get_with_retries(client, "https://example.com", headers=None, params=None, timeout=1.23)
    assert calls["get"], "GET was not called"
    assert calls["get"][0]["timeout"] == 1.23
    # Ensure no explicit verify=False passed
    assert "verify" not in calls["get"][0] or calls["get"][0]["verify"] is not False


@pytest.mark.providers
@pytest.mark.asyncio
async def test_enrich_one_applies_timeout_to_client(monkeypatch):
    # Ensure AsyncClient created with timeout parameter
    created = {"timeout": None}

    original = httpx.AsyncClient

    class DummyClient:
        def __init__(self, *a, **k):
            created["timeout"] = k.get("timeout")
        async def __aenter__(self):
            return self
        async def __aexit__(self, et, ev, tb):
            return False

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)
    try:
        cache = Cache(":memory:")
        res = await core_services.enrich_one("example.com", [], cache, {}, True, False, 2.5, 2)
        # No providers → INCONCLUSIVE, but creation timeout captured
        assert created["timeout"] == 2.5
    finally:
        monkeypatch.setattr(httpx, "AsyncClient", original) 