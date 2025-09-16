from __future__ import annotations

# Compatibility shims to delegate to core services
from typing import Any, Dict, List

from ioc_core.models import AggregatedResult, ProviderResult  # noqa: F401
from ioc_core.cache import Cache  # noqa: F401
from ioc_core.services import fetch_with_cache as _fetch_with_cache_core
from ioc_core.services import enrich_one as _enrich_one_core


async def fetch_with_cache(provider, cache: Cache, client, ioc: str, ioc_type: str, ttl: int, use_cache: bool, refresh: bool, timeout: float) -> ProviderResult:
    return await _fetch_with_cache_core(provider, cache, client, ioc, ioc_type, ttl, use_cache, refresh, timeout)


def aggregate(ioc: str, ioc_type: str, provider_results: List[ProviderResult]) -> AggregatedResult:
    # Keep a small local aggregator to preserve import path; delegate via core models
    statuses = [pr.status for pr in provider_results]
    total = sum(pr.score for pr in provider_results) if provider_results else 0.0
    if any(s == "MALICIOUS" for s in statuses):
        status = "MALICIOUS"
    elif any(s == "SUSPICIOUS" for s in statuses):
        status = "SUSPICIOUS"
    elif statuses and all(s == "CLEAN" for s in statuses):
        status = "CLEAN"
    else:
        status = "INCONCLUSIVE"
    return AggregatedResult(ioc, ioc_type, status, float(total), provider_results)


async def enrich_one(ioc: str, providers: List[Any], cache: Cache, ttls: Dict[str, int], use_cache: bool, refresh: bool, timeout: float, concurrency: int) -> AggregatedResult:
    return await _enrich_one_core(ioc, providers, cache, ttls, use_cache, refresh, timeout, concurrency)


