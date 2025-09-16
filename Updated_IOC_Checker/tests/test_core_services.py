import asyncio
import json

import pytest

from ioc_core import services as core_services
from ioc_core.cache import Cache as CoreCache
from ioc_core import config as core_config


def test_check_iocs_basic(fake_httpx, tmp_path, monkeypatch):
    cache = CoreCache(str(tmp_path / ".cache.sqlite"))
    vt_data = {"data": {"attributes": {"last_analysis_stats": {"malicious": 1, "suspicious": 0, "harmless": 0, "undetected": 0}}}}
    ab_data = {"data": {"abuseConfidenceScore": 0, "totalReports": 0, "isPublic": True}}
    otx_data = {"pulse_info": {"count": 0, "pulses": []}}
    fake_httpx["set_routes"]([
        ("GET", "/api/v3/ip_addresses/8.8.8.8", fake_httpx_response(200, vt_data)),
        ("GET", "/api/v2/check", fake_httpx_response(200, ab_data)),
        ("GET", "/api/v1/indicators/IPv4/8.8.8.8/general", fake_httpx_response(200, otx_data)),
    ])
    providers = [
        core_services.VirusTotalProvider("k"),
        core_services.AbuseIPDBProvider("k"),
        core_services.OTXProvider("k"),
    ]
    use_cache, refresh, timeout = core_config.resolve_mode("normal")
    results = asyncio.run(core_services.check_iocs(
        ["8.8.8.8"], providers, cache, dict(core_config.DEFAULT_TTLS), use_cache, refresh, timeout, concurrency=2
    ))
    assert len(results) == 1
    ar = results[0]
    assert ar.ioc == "8.8.8.8"
    per = {p.provider: p for p in ar.providers}
    assert per["virustotal"].status == "MALICIOUS"
    assert per["abuseipdb"].status in ("CLEAN", "INCONCLUSIVE")
    assert per["otx"].status in ("INCONCLUSIVE", "SUSPICIOUS")


def test_new_provider_threatfox_only(fake_httpx, tmp_path, monkeypatch):
    cache = CoreCache(str(tmp_path / ".cache.sqlite"))
    # ThreatFox returns a match with confidence
    tf_body = {
        "query_status": "ok",
        "data": [
            {
                "confidence_level": 85,
                "malware_printable": "TestFamily",
                "tags": ["c2", "phishing"],
                "first_seen": "2024-01-01",
                "last_seen": "2024-02-01",
                "reference": "https://threatfox.abuse.ch/ioc/123/"
            }
        ]
    }
    fake_httpx["set_routes"]([
        ("POST", "/api/v1/", fake_httpx_response(200, tf_body)),
    ])
    providers = [
        core_services.ThreatFoxProvider(),
    ]
    use_cache, refresh, timeout = core_config.resolve_mode("normal")
    results = asyncio.run(core_services.check_iocs(
        ["1.1.1.1"], providers, cache, dict(core_config.DEFAULT_TTLS), use_cache, refresh, timeout, concurrency=2
    ))
    assert results and results[0].providers
    per = {p.provider: p for p in results[0].providers}
    assert per["threatfox"].status in ("MALICIOUS", "SUSPICIOUS")


# helpers

def fake_httpx_response(code, data):
    from tests.conftest import FakeResponse
    return FakeResponse(code, json_data=data) 