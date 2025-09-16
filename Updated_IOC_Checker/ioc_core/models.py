from __future__ import annotations

import base64
import datetime as dt
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ProviderResult:
    provider: str
    status: str  # MALICIOUS | SUSPICIOUS | CLEAN | INCONCLUSIVE
    score: float
    evidence: List[str]
    raw_ref: Optional[str]
    latency_ms: Optional[int]
    cached: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status,
            "score": self.score,
            "evidence": self.evidence,
            "raw_ref": self.raw_ref,
            "latency_ms": self.latency_ms,
            "cached": self.cached,
        }


@dataclass
class AggregatedResult:
    ioc: str
    ioc_type: str
    status: str
    score: float
    providers: List[ProviderResult]

    def to_row(self) -> Dict[str, Any]:
        d = {"ioc": self.ioc, "type": self.ioc_type, "status": self.status, "score": round(self.score, 2)}
        for pr in self.providers:
            d[f"{pr.provider}_status"] = pr.status
            d[f"{pr.provider}_score"] = pr.score
            d[f"{pr.provider}_cached"] = pr.cached
        return d

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ioc": self.ioc,
            "type": self.ioc_type,
            "status": self.status,
            "score": round(self.score, 2),
            "providers": [p.to_dict() for p in self.providers],
        }


def classify_ioc(raw: str) -> tuple[bool, str, str, Optional[str]]:
    s = (raw or "").strip()
    if not s:
        return False, "invalid", s, "Empty line"
    if s.lower().startswith(("http://", "https://")):
        return True, "url", s.strip(), None
    if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", s):
        octs = [int(x) for x in s.split(".")]
        if all(0 <= o <= 255 for o in octs):
            return True, "ip", s, None
        return False, "invalid", s, "Invalid IPv4 octet range"
    if re.fullmatch(r"[A-Fa-f0-9]{32}", s) or re.fullmatch(r"[A-Fa-f0-9]{40}", s) or re.fullmatch(r"[A-Fa-f0-9]{64}", s):
        return True, "hash", s.lower(), None
    if re.fullmatch(r"(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,63}", s):
        return True, "domain", s.lower(), None
    return False, "invalid", s, "Unrecognized IOC format"


def vt_url_id(u: str) -> str:
    b = base64.urlsafe_b64encode(u.encode("utf-8")).decode("ascii")
    return b.strip("=")


def now_utc() -> int:
    return int(dt.datetime.utcnow().timestamp())


def aggregate(ioc: str, ioc_type: str, provider_results: List[ProviderResult]) -> AggregatedResult:
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