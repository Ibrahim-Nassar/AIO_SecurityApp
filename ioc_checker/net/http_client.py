from __future__ import annotations

import httpx

# Deprecated: prefer using httpx.AsyncClient directly via ioc_core.services

def create_async_client(timeout_seconds: float = 10.0) -> httpx.AsyncClient:
    # Centralized client: no HTTP/2 to avoid extra deps; follow redirects by default
    timeout = httpx.Timeout(timeout_seconds, connect=5.0)
    return httpx.AsyncClient(timeout=timeout, follow_redirects=True)


