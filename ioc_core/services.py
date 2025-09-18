from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Callable, cast
import random
import time

import httpx

from . import config
from .cache import Cache
from .models import AggregatedResult, ProviderResult, aggregate, vt_url_id, now_utc, classify_ioc
from .logger import get_logger


class BaseProvider:
    name = ""
    supported: set[str] = set()  # {"ip","domain","hash","url"}

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key

    def available(self) -> bool:
        return bool(self.api_key)

    def supports(self, t: str) -> bool:
        return t in self.supported

    async def query(self, client: httpx.AsyncClient, ioc: str, ioc_type: str, timeout: float) -> ProviderResult:
        return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [], None, None, False)


class VirusTotalProvider(BaseProvider):
    name = "virustotal"
    supported = {"ip", "domain", "hash", "url"}

    def _endpoint(self, ioc: str, t: str) -> str:
        if t == "ip":
            return f"https://www.virustotal.com/api/v3/ip_addresses/{ioc}"
        if t == "domain":
            return f"https://www.virustotal.com/api/v3/domains/{ioc}"
        if t == "hash":
            return f"https://www.virustotal.com/api/v3/files/{ioc}"
        if t == "url":
            return f"https://www.virustotal.com/api/v3/urls/{vt_url_id(ioc)}"
        return ""

    async def query(self, client: httpx.AsyncClient, ioc: str, ioc_type: str, timeout: float) -> ProviderResult:
        if not self.available() or not self.supports(ioc_type):
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [], None, None, False)
        url = self._endpoint(ioc, ioc_type)
        headers = {"x-apikey": self.api_key or ""}
        endpoint_kind = "reputation"
        t_resp = await _http_get_with_retries(client, url, headers=headers, params=None, timeout=timeout)
        r, latency, status_code, err = t_resp.response, t_resp.latency_ms, t_resp.status_code, t_resp.error
        try:
            log = get_logger()
            log.info(
                "provider=%s endpoint_kind=%s status_code=%s latency_ms=%s cache_hit=%s",
                self.name,
                endpoint_kind,
                (status_code if status_code is not None else ("timeout" if err else "unknown")),
                latency,
                False,
            )
        except Exception:
            pass
        try:
            if r.status_code in (429,) or r.status_code >= 500:
                return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [f"http {r.status_code}"], url, latency, False)
            if r.status_code == 404:
                return ProviderResult(self.name, "CLEAN", 0.0, ["not found"], url, latency, False)
            if r.status_code in (401, 403):
                return ProviderResult(self.name, "INCONCLUSIVE", 0.0, ["unauthorized/forbidden (check API key)"], url, latency, False)
            data = r.json()
            attributes = (((data or {}).get("data") or {}).get("attributes") or {})
            stats = attributes.get("last_analysis_stats") or {}
            mal = int(stats.get("malicious", 0))
            susp = int(stats.get("suspicious", 0))
            harmless = int(stats.get("harmless", 0))
            undetected = int(stats.get("undetected", 0))
            score = mal * 2 + susp * 1.0
            if mal >= 1:
                status = "MALICIOUS"
            elif susp >= 1:
                status = "SUSPICIOUS"
            elif harmless > 5 or undetected > 10:
                status = "CLEAN"
            else:
                status = "INCONCLUSIVE"
            ev: List[str] = [
                f"malicious={mal}",
                f"suspicious={susp}",
                f"harmless={harmless}",
                f"undetected={undetected}",
            ]
            rep = attributes.get("reputation")
            if isinstance(rep, (int, float)):
                ev.append(f"reputation={rep}")
            cats = attributes.get("categories")
            if isinstance(cats, dict) and cats:
                unique_categories = list({str(v) for v in cats.values()})
                ev.append("categories=" + ",".join(unique_categories[:5]))
            last_analysis = attributes.get("last_analysis_date")
            if isinstance(last_analysis, (int, float)) and last_analysis:
                try:
                    from datetime import datetime

                    ev.append(
                        "last_analysis="
                        + datetime.utcfromtimestamp(int(last_analysis)).isoformat()
                        + "Z"
                    )
                except Exception:
                    pass
            total_votes = attributes.get("total_votes")
            if isinstance(total_votes, dict) and total_votes:
                harmless_votes = int(total_votes.get("harmless", 0))
                malicious_votes = int(total_votes.get("malicious", 0))
                ev.append(f"votes=mal:{malicious_votes}/har:{harmless_votes}")
            if ioc_type == "ip":
                ref = f"https://www.virustotal.com/gui/ip-address/{ioc}"
            elif ioc_type == "domain":
                ref = f"https://www.virustotal.com/gui/domain/{ioc}"
            elif ioc_type == "hash":
                ref = f"https://www.virustotal.com/gui/file/{ioc}"
            elif ioc_type == "url":
                ref = f"https://www.virustotal.com/gui/url/{vt_url_id(ioc)}"
            else:
                ref = url
            return ProviderResult(self.name, status, float(score), ev, ref, latency, False)
        except Exception as e:
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [str(e)], url, latency if isinstance(latency, int) else None, False)


class AbuseIPDBProvider(BaseProvider):
    name = "abuseipdb"
    supported = {"ip"}

    async def query(self, client: httpx.AsyncClient, ioc: str, ioc_type: str, timeout: float) -> ProviderResult:
        if not self.available() or not self.supports(ioc_type):
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [], None, None, False)
        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {"Key": self.api_key or "", "Accept": "application/json"}
        params = {"ipAddress": ioc, "maxAgeInDays": "90"}
        endpoint_kind = "check"
        t_resp = await _http_get_with_retries(client, url, headers=headers, params=params, timeout=timeout)
        r, latency, status_code, err = t_resp.response, t_resp.latency_ms, t_resp.status_code, t_resp.error
        try:
            log = get_logger()
            log.info(
                "provider=%s endpoint_kind=%s status_code=%s latency_ms=%s cache_hit=%s",
                self.name,
                endpoint_kind,
                (status_code if status_code is not None else ("timeout" if err else "unknown")),
                latency,
                False,
            )
        except Exception:
            pass
        try:
            if r.status_code in (429,) or r.status_code >= 500:
                return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [f"http {r.status_code}"], url, latency, False)
            if r.status_code == 404:
                return ProviderResult(self.name, "CLEAN", 0.0, ["not found"], url, latency, False)
            if r.status_code in (401, 403):
                return ProviderResult(self.name, "INCONCLUSIVE", 0.0, ["unauthorized/forbidden (check API key)"], url, latency, False)
            data = r.json()
            d = (data or {}).get("data") or {}
            conf = float(d.get("abuseConfidenceScore", 0))
            total = int(d.get("totalReports", 0))
            is_public = bool(d.get("isPublic", True))
            score = conf
            if conf >= 75:
                status = "MALICIOUS"
            elif conf >= 25 or total >= 3:
                status = "SUSPICIOUS"
            elif total == 0 and is_public:
                status = "CLEAN"
            else:
                status = "INCONCLUSIVE"
            ev: List[str] = [
                f"confidence={int(conf)}",
                f"total_reports={total}",
                f"is_public={is_public}",
            ]
            for k in ("countryCode", "usageType", "isp", "domain", "lastReportedAt"):
                val = d.get(k)
                if val:
                    # Normalize to snake_case where applicable
                    if k == "countryCode":
                        ev.append(f"country_code={val}")
                    elif k == "usageType":
                        ev.append(f"usage_type={val}")
                    elif k == "lastReportedAt":
                        ev.append(f"last_reported_at={val}")
                    else:
                        ev.append(f"{k.lower()}={val}")
            return ProviderResult(self.name, status, float(score), ev, f"https://www.abuseipdb.com/check/{ioc}", latency, False)
        except Exception as e:
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [str(e)], "https://www.abuseipdb.com", latency if isinstance(latency, int) else None, False)


class OTXProvider(BaseProvider):
    name = "otx"
    supported = {"ip", "domain", "hash", "url"}

    def _endpoint(self, ioc: str, t: str) -> str:
        if t == "ip":
            return f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ioc}/general"
        if t == "domain":
            return f"https://otx.alienvault.com/api/v1/indicators/domain/{ioc}/general"
        if t == "hash":
            return f"https://otx.alienvault.com/api/v1/indicators/file/{ioc}/general"
        if t == "url":
            from urllib.parse import quote

            return f"https://otx.alienvault.com/api/v1/indicators/url/{quote(ioc, safe='')}/general"
        return ""

    async def query(self, client: httpx.AsyncClient, ioc: str, ioc_type: str, timeout: float) -> ProviderResult:
        if not self.available() or not self.supports(ioc_type):
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [], None, None, False)
        url = self._endpoint(ioc, ioc_type)
        headers = {"X-OTX-API-KEY": self.api_key or ""}
        endpoint_kind = "reputation"
        t_resp = await _http_get_with_retries(client, url, headers=headers, params=None, timeout=timeout)
        r, latency, status_code, err = t_resp.response, t_resp.latency_ms, t_resp.status_code, t_resp.error
        try:
            log = get_logger()
            log.info(
                "provider=%s endpoint_kind=%s status_code=%s latency_ms=%s cache_hit=%s",
                self.name,
                endpoint_kind,
                (status_code if status_code is not None else ("timeout" if err else "unknown")),
                latency,
                False,
            )
        except Exception:
            pass
        try:
            if r.status_code in (429,) or r.status_code >= 500:
                return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [f"http {r.status_code}"], url, latency, False)
            if r.status_code == 404:
                return ProviderResult(self.name, "CLEAN", 0.0, ["not found"], url, latency, False)
            if r.status_code in (401, 403):
                return ProviderResult(self.name, "INCONCLUSIVE", 0.0, ["unauthorized/forbidden (check API key)"], url, latency, False)
            data = r.json()
            pulses = (((data or {}).get("pulse_info") or {}).get("count")) or 0
            refs = (((data or {}).get("pulse_info") or {}).get("pulses")) or []
            names = [p.get("name") for p in refs if isinstance(p, dict) and p.get("name")]
            score = float(pulses)
            status = "SUSPICIOUS" if pulses >= 1 else "INCONCLUSIVE"
            ev: List[str] = [f"pulses={pulses}"] + [f"pulse={n}" for n in names[:5]]
            general = (data or {})
            rep = general.get("reputation")
            if isinstance(rep, (int, float)):
                ev.append(f"reputation={int(rep)}")
            country = general.get("country_name") or general.get("country_code")
            if country:
                ev.append(f"country={country}")
            asn = general.get("asn") or (general.get("as") if isinstance(general.get("as"), str) else None)
            if asn:
                ev.append(f"asn={asn}")
            return ProviderResult(self.name, status, score, ev, url, latency, False)
        except Exception as e:
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [str(e)], url, latency if isinstance(latency, int) else None, False)




class ThreatFoxProvider(BaseProvider):
    name = "threatfox"
    supported = {"ip", "domain", "hash", "url"}

    def __init__(self) -> None:
        super().__init__(api_key=None)

    def available(self) -> bool:
        # public, keyless
        return True

    async def query(self, client: httpx.AsyncClient, ioc: str, ioc_type: str, timeout: float) -> ProviderResult:
        if not self.supports(ioc_type):
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [], None, None, False)
        url = "https://threatfox-api.abuse.ch/api/v1/"
        payload = {"query": "search_ioc", "search_term": ioc}
        # Minimal backoff on 429 (0.8s -> 1.6s), respect Retry-After up to 5s
        attempt = 0
        delay = 0.8
        t0 = now_utc()
        while True:
            try:
                r = await client.post(url, json=payload, timeout=timeout)
                latency = int((now_utc() - t0) * 1000)
                if r.status_code == 429:
                    if attempt >= 2:
                        return ProviderResult(self.name, "INCONCLUSIVE", 0.0, ["http 429"], url, latency, False)
                    ra = r.headers.get("retry-after")
                    try:
                        ra_s = min(5.0, float(ra)) if ra else delay
                    except Exception:
                        ra_s = delay
                    await asyncio.sleep(ra_s)
                    attempt += 1
                    delay *= 2
                    continue
                if r.status_code >= 500:
                    return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [f"http {r.status_code}"], url, latency, False)
                js = r.json()
                data = (js or {}).get("data") or []
                if not data:
                    return ProviderResult(self.name, "CLEAN", 0.0, ["not found"], url, latency, False)
                # Use the first matching record
                rec = data[0] if isinstance(data, list) else data
                tags = rec.get("tags") or []
                family = rec.get("malware") or rec.get("malware_printable")
                conf = int(rec.get("confidence_level") or 0)
                threat_type = (rec.get("threat_type") or rec.get("ioc_type") or "").lower()
                status = "MALICIOUS" if conf >= 80 else ("SUSPICIOUS" if conf >= 20 else "INCONCLUSIVE")
                ev: List[str] = []
                if family:
                    ev.append(f"family={family}")
                if tags:
                    try:
                        ev.append("tags=" + ",".join([str(t) for t in tags][:6]))
                    except Exception:
                        pass
                fs = rec.get("first_seen") or rec.get("first_seen_utc")
                ls = rec.get("last_seen") or rec.get("last_seen_utc")
                if fs:
                    ev.append(f"first_seen={fs}")
                if ls:
                    ev.append(f"last_seen={ls}")
                if threat_type:
                    ev.append(f"type={threat_type}")
                ref = rec.get("reference") or "https://threatfox.abuse.ch/"
                return ProviderResult(self.name, status, float(conf), ev, ref, latency, False)
            except Exception as e:
                return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [str(e)], url, None, False)


async def fetch_with_cache(provider: BaseProvider, cache: Cache, client: httpx.AsyncClient, ioc: str, ioc_type: str, ttl: int, use_cache: bool, refresh: bool, timeout: float) -> ProviderResult:
    if use_cache and not refresh:
        cached = cache.get(provider.name, ioc, ttl)
        if cached is not None:
            try:
                get_logger().info(
                    "provider=%s endpoint_kind=%s status_code=%s latency_ms=%s cache_hit=%s",
                    provider.name,
                    "cache",
                    "cache",
                    cached.get("latency_ms"),
                    True,
                )
            except Exception:
                pass
            return ProviderResult(
                provider.name,
                cached.get("status", "INCONCLUSIVE"),
                float(cached.get("score", 0.0)),
                list(cached.get("evidence", [])),
                cached.get("raw_ref"),
                cached.get("latency_ms"),
                True,
            )
    res = await provider.query(client, ioc, ioc_type, timeout)
    cache.set(provider.name, ioc, ioc_type, res.to_dict())
    try:
        get_logger().info(
            "provider=%s endpoint_kind=%s status_code=%s latency_ms=%s cache_hit=%s",
            provider.name,
            "network",
            "n/a",
            res.latency_ms,
            False,
        )
    except Exception:
        pass
    return res


# Internal: HTTP GET with bounded retries/backoff and total budget cap
class _HttpAttemptResult:
    def __init__(self, response: httpx.Response, latency_ms: int, status_code: Optional[int], error: Optional[str]):
        self.response = response
        self.latency_ms = latency_ms
        self.status_code = status_code
        self.error = error


async def _http_get_with_retries(
    client: httpx.AsyncClient,
    url: str,
    headers: Optional[Dict[str, str]],
    params: Optional[Dict[str, Any]],
    timeout: float,
    max_extra_retries: int = 2,
) -> _HttpAttemptResult:
    start = time.monotonic()
    budget = max(timeout * 1.5, timeout + 0.5)
    attempt = 0
    backoff = 0.5
    last_exc: Optional[BaseException] = None
    last_resp: Optional[httpx.Response] = None
    status_code: Optional[int] = None
    latency_ms: int = 0
    while True:
        t0 = time.monotonic()
        try:
            r = await client.get(url, headers=headers or {}, params=params, timeout=timeout)
            latency_ms = int((time.monotonic() - t0) * 1000)
            last_resp = r
            status_code = r.status_code
            if r.status_code in (429, 502, 503, 504):
                if attempt < max_extra_retries and (time.monotonic() - start) < budget:
                    # sleep with jitter
                    delay = backoff * (1 + random.uniform(-0.25, 0.25))
                    delay = max(0.0, min(3.0, delay))
                    # respect remaining budget before sleeping
                    remaining = budget - (time.monotonic() - start)
                    if remaining <= 0.1:
                        break
                    await asyncio.sleep(min(delay, max(0.0, remaining)))
                    attempt += 1
                    backoff *= 2
                    continue
            # success or non-retriable
            break
        except (httpx.TimeoutException, httpx.RequestError) as e:
            latency_ms = int((time.monotonic() - t0) * 1000)
            last_exc = e
            status_code = None
            if attempt < max_extra_retries and (time.monotonic() - start) < budget:
                delay = backoff * (1 + random.uniform(-0.25, 0.25))
                delay = max(0.0, min(3.0, delay))
                remaining = budget - (time.monotonic() - start)
                if remaining <= 0.1:
                    break
                await asyncio.sleep(min(delay, max(0.0, remaining)))
                attempt += 1
                backoff *= 2
                continue
            break
        except BaseException as e:  # unexpected
            latency_ms = int((time.monotonic() - t0) * 1000)
            last_exc = e
            break
    # Prepare return
    if last_resp is None:
        # fabricate minimal response object for downstream code paths
        req = httpx.Request("GET", url)
        resp = httpx.Response(status_code=599, request=req)
        return _HttpAttemptResult(resp, latency_ms, status_code, "timeout" if isinstance(last_exc, httpx.TimeoutException) else "error")
    return _HttpAttemptResult(last_resp, latency_ms, status_code, None)


async def enrich_one(ioc: str, providers: List[BaseProvider], cache: Cache, ttls: Dict[str, int], use_cache: bool, refresh: bool, timeout: float, concurrency: int, client: Optional[httpx.AsyncClient] = None, sem: Optional[asyncio.Semaphore] = None) -> AggregatedResult:
    valid, t, norm, err = classify_ioc(ioc)
    if not valid:
        return AggregatedResult(ioc, "invalid", "INCONCLUSIVE", 0.0, [ProviderResult("validation", "INCONCLUSIVE", 0.0, [err or "invalid"], None, None, False)])
    _sem = sem or asyncio.Semaphore(max(1, concurrency))
    async with _sem:
        if client is None:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as c:
                tasks = [
                    fetch_with_cache(p, cache, c, norm, t, ttls.get(p.name, 3600), use_cache, refresh, timeout)
                    for p in providers
                    if p.available() and p.supports(t)
                ]
                if not tasks:
                    return AggregatedResult(norm, t, "INCONCLUSIVE", 0.0, [])
                results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            tasks = [
                fetch_with_cache(p, cache, client, norm, t, ttls.get(p.name, 3600), use_cache, refresh, timeout)
                for p in providers
                if p.available() and p.supports(t)
            ]
            if not tasks:
                return AggregatedResult(norm, t, "INCONCLUSIVE", 0.0, [])
            results = await asyncio.gather(*tasks, return_exceptions=True)
    prs: List[ProviderResult] = []
    for r in results:
        if isinstance(r, Exception):
            prs.append(ProviderResult("unknown", "INCONCLUSIVE", 0.0, [str(r)], None, None, False))
        else:
            # mypy: ensure r is ProviderResult
            prs.append(cast(ProviderResult, r))
    return aggregate(norm, t, prs)


async def check_iocs(
    iocs: List[str],
    providers: List[BaseProvider],
    cache: Cache,
    ttls: Dict[str, int],
    use_cache: bool,
    refresh: bool,
    timeout: float,
    concurrency: int,
    cancel_cb: Optional[Callable[[], bool]] = None,
) -> List[AggregatedResult]:
    """Batch-check IOCs with shared client/semaphore; optional cancel callback to stop early.

    cancel_cb: returns True to request cancellation between chunks.
    """
    results: List[AggregatedResult] = []
    chunk_size = max(1, concurrency)
    sem = asyncio.Semaphore(max(1, concurrency))
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for start in range(0, len(iocs), chunk_size):
            if cancel_cb and cancel_cb():
                break
            chunk = iocs[start:start + chunk_size]
            tasks = [
                enrich_one(ioc, providers, cache, ttls, use_cache, refresh, timeout, concurrency, client=client, sem=sem)
                for ioc in chunk
            ]
            part = await asyncio.gather(*tasks)
            results.extend(part)
    return results 