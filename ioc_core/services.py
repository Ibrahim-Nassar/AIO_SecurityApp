from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Callable, cast

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
        t0 = now_utc()
        try:
            try:
                get_logger().info("provider start name=%s ep=%s", self.name, url.split("/api/")[-1] if "/api/" in url else url)
            except Exception:
                pass
            r = await client.get(url, headers=headers, timeout=timeout)
            latency = int((now_utc() - t0) * 1000)
            try:
                get_logger().info("provider http name=%s status=%s", self.name, r.status_code)
            except Exception:
                pass
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
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [str(e)], url, None, False)


class AbuseIPDBProvider(BaseProvider):
    name = "abuseipdb"
    supported = {"ip"}

    async def query(self, client: httpx.AsyncClient, ioc: str, ioc_type: str, timeout: float) -> ProviderResult:
        if not self.available() or not self.supports(ioc_type):
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [], None, None, False)
        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {"Key": self.api_key or "", "Accept": "application/json"}
        params = {"ipAddress": ioc, "maxAgeInDays": "90"}
        t0 = now_utc()
        try:
            try:
                get_logger().info("provider start name=%s ep=%s", self.name, "/api/v2/check")
            except Exception:
                pass
            r = await client.get(url, headers=headers, params=params, timeout=timeout)
            latency = int((now_utc() - t0) * 1000)
            try:
                get_logger().info("provider http name=%s status=%s", self.name, r.status_code)
            except Exception:
                pass
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
                f"totalReports={total}",
                f"isPublic={is_public}",
            ]
            for k in ("countryCode", "usageType", "isp", "domain", "lastReportedAt"):
                val = d.get(k)
                if val:
                    ev.append(f"{k}={val}")
            return ProviderResult(self.name, status, float(score), ev, f"https://www.abuseipdb.com/check/{ioc}", latency, False)
        except Exception as e:
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [str(e)], "https://www.abuseipdb.com", None, False)


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
        t0 = now_utc()
        try:
            try:
                get_logger().info("provider start name=%s ep=%s", self.name, url.split("/api/")[-1] if "/api/" in url else url)
            except Exception:
                pass
            r = await client.get(url, headers=headers, timeout=timeout)
            latency = int((now_utc() - t0) * 1000)
            try:
                get_logger().info("provider http name=%s status=%s", self.name, r.status_code)
            except Exception:
                pass
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
            ev: List[str] = [f"pulses={pulses}"] + [f"pulse:{n}" for n in names[:5]]
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
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [str(e)], url, None, False)


class UrlscanProvider(BaseProvider):
    name = "urlscan"
    supported = {"url"}

    def __init__(self, api_key: Optional[str]):
        super().__init__(api_key)
        import os

        self.base = os.getenv("URLSCAN_BASE", "https://urlscan.io").rstrip("/")
        self.timeout = float(os.getenv("URLSCAN_TIMEOUT", "10"))
        self.retries = int(os.getenv("URLSCAN_RETRIES", "2"))
        # Centralized feature flag in config
        self.submit_enabled = config.URLSCAN_SUBMIT
        self.mock = os.getenv("URLSCAN_MOCK", "0").strip() in ("1", "true", "yes")

    def available(self) -> bool:
        if self.mock:
            return True
        return bool(self.api_key)

    async def _request_json(self, client: httpx.AsyncClient, method: str, url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        attempt = 0
        backoff = 0.75
        last_exc: Optional[Exception] = None
        while attempt <= self.retries:
            t0 = now_utc()
            try:
                if method == "GET":
                    r = await client.get(url, headers=headers, params=params)
                else:
                    r = await client.post(url, headers=headers, json=data)
                if r.status_code == 429 or r.status_code >= 500:
                    last_exc = Exception(f"http {r.status_code}")
                else:
                    try:
                        return cast(Dict[str, Any], r.json())
                    except Exception:
                        raise Exception((r.text or "").strip()[:200] or "invalid json")
            except (httpx.TimeoutException, httpx.RequestError) as e:
                last_exc = e
            except Exception as e:
                last_exc = e
            attempt += 1
            await asyncio.sleep(min(6.0, backoff))
            backoff *= 2
        raise last_exc or Exception("request failed")

    def _classify(self, tags: List[str], verdicts: Dict[str, Any]) -> Tuple[str, float]:
        tg = [str(t).lower() for t in (tags or [])]
        v = verdicts or {}
        overall = str(v.get("overall") or "").lower()
        malicious = bool(v.get("malicious"))
        score = float(v.get("score", 0))
        if malicious or overall == "malicious" or ("malicious" in tg):
            return "MALICIOUS", max(80.0, score)
        if overall in ("suspicious",) or ("phishing" in tg or "suspicious" in tg):
            return "SUSPICIOUS", max(40.0, score)
        if overall in ("benign", "clean") or ("benign" in tg or "clean" in tg):
            return "CLEAN", min(10.0, score)
        return "INCONCLUSIVE", score

    async def query(self, client: httpx.AsyncClient, ioc: str, ioc_type: str, timeout: float) -> ProviderResult:
        if not self.supports(ioc_type):
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [], None, None, False)
        if not self.available():
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, ["missing API key (set URLSCAN_API_KEY or enable URLSCAN_MOCK=1)"], None, None, False)
        headers = {"Accept": "application/json"}
        if not self.mock:
            headers["API-Key"] = self.api_key or ""
        search_url = f"{self.base}/api/v1/search/"
        params = {"q": f"url:\"{ioc}\"", "size": 5}
        try:
            js = await self._request_json(client, "GET", search_url, headers, params=params)
            results = (js or {}).get("results") or []
            if results:
                rec = results[0]
                tags = rec.get("tags") or []
                verdicts = rec.get("verdicts") or {}
                status, score = self._classify(tags, verdicts)
                link = rec.get("result") or rec.get("task", {}).get("reportURL") or rec.get("task", {}).get("url")
                ev: List[str] = []
                if tags:
                    ev.append("tags=" + ",".join([str(t) for t in tags][:6]))
                if isinstance(verdicts, dict) and verdicts:
                    ev.append("verdicts=" + ",".join([f"{k}:{v}" for k, v in list(verdicts.items())[:5]]))
                return ProviderResult(self.name, status, float(score), ev, link, None, False)
        except Exception:
            pass
        if not self.submit_enabled and not self.mock:
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, ["no prior scan"], None, None, False)
        if self.mock:
            ev = ["mock=1", "submitted=true"]
            return ProviderResult(self.name, "SUSPICIOUS", 55.0, ev, "https://urlscan.io/result/mock", 1000, False)
        try:
            submit_url = f"{self.base}/api/v1/scan"
            body = {"url": ioc, "visibility": "unlisted"}
            sj = await self._request_json(client, "POST", submit_url, headers, data=body)
            uuid = (sj or {}).get("uuid") or (sj or {}).get("scanid")
            if not uuid:
                return ProviderResult(self.name, "INCONCLUSIVE", 0.0, ["submit missing uuid"], None, None, False)
            poll = f"{self.base}/api/v1/result/{uuid}"
            delay = 2.0
            total_wait = 0.0
            jsr: Dict[str, Any] = {}
            async with httpx.AsyncClient(timeout=timeout) as poll_client:
                while total_wait < max(15.0, self.timeout):
                    await asyncio.sleep(delay)
                    total_wait += delay
                    delay = min(15.0, delay * 1.8)
                    try:
                        jsr = await self._request_json(poll_client, "GET", poll, headers)
                    except Exception:
                        continue
                    if str(jsr.get("status") or jsr.get("state") or "").lower() in ("done", "finished", "ready"):
                        break
            page = jsr.get("page") or {}
            verdicts = jsr.get("verdicts") or {}
            tags = jsr.get("tags") or []
            link = jsr.get("result") or jsr.get("task", {}).get("reportURL")
            status, score = self._classify(tags, verdicts)
            ev2: List[str] = []
            if tags:
                ev2.append("tags=" + ",".join([str(t) for t in tags][:6]))
            if isinstance(verdicts, dict) and verdicts:
                ev2.append("verdicts=" + ",".join([f"{k}:{v}" for k, v in list(verdicts.items())[:5]]))
            title = page.get("title")
            if title:
                ev2.append(f"title={title}")
            return ProviderResult(self.name, status, float(score), ev2, link, None, False)
        except Exception as e:
            return ProviderResult(self.name, "INCONCLUSIVE", 0.0, [str(e)], None, None, False)


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
    return res


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