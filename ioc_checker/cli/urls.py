from __future__ import annotations

import asyncio
import json
import os
from typing import List
import httpx

from ioc_core.config import DEFAULT_TTLS
from ioc_core.models import AggregatedResult, aggregate
from ioc_core.services import AbuseIPDBProvider, OTXProvider, VirusTotalProvider, fetch_with_cache
from ioc_core.cache import Cache


async def run_cli(urls: List[str], providers: List[str], out_path: str = "", timeout: float = 15.0, concurrency: int = 4) -> None:
    provs = []
    for n in providers:
        if n == "virustotal":
            provs.append(VirusTotalProvider(os.getenv("VIRUSTOTAL_API_KEY")))
        elif n == "abuseipdb":
            provs.append(AbuseIPDBProvider(os.getenv("ABUSEIPDB_API_KEY")))
        elif n == "otx":
            provs.append(OTXProvider(os.getenv("OTX_API_KEY") or os.getenv("ALIENVAULT_OTX_API_KEY")))
        # urlscan removed

    results: List[AggregatedResult] = []
    cache = Cache(".ioc_enricher_cache.sqlite")
    sem = asyncio.Semaphore(max(1, int(concurrency)))
    async with httpx.AsyncClient(timeout=timeout) as client:
        async def run_one(u: str) -> AggregatedResult:
            tasks = [
                fetch_with_cache(p, cache, client, u, "url", DEFAULT_TTLS.get(p.name, 3600), True, False, timeout)
                for p in provs
                if p.supports("url") and p.available()
            ]
            got = await asyncio.gather(*tasks)
            return aggregate(u, "url", got)

        for i in range(0, len(urls), sem._value):
            chunk = urls[i : i + sem._value]
            part = await asyncio.gather(*[run_one(u) for u in chunk])
            results.extend(part)

    header = ["type", "ioc"] + [p.name for p in provs]
    lines = [",".join(header)]
    for r in results:
        per = {pr.provider: pr for pr in r.providers}
        row = [r.ioc_type, r.ioc]
        for p in provs:
            pr = per.get(p.name)
            row.append((pr.status if pr else ""))
        lines.append(",".join(row))
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            f.write("\n".join(lines))
        print(f"Wrote {out_path}")
    else:
        print("\n".join(lines))


