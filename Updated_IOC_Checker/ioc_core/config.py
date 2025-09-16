import os
from typing import Tuple, Dict, List

# Provider registry (single source of truth)
# types: set of supported IOC kinds; needs_key: whether an API key is required
PROVIDERS: Dict[str, Dict[str, object]] = {
    "virustotal":  {"types": {"ip", "domain", "url", "hash"}, "needs_key": True,  "rate": "≈4/min"},
    "abuseipdb":   {"types": {"ip"},                         "needs_key": True,  "rate": "1000/day"},
    "otx":         {"types": {"ip", "domain", "url", "hash"}, "needs_key": True,  "rate": "~60/min"},
    "urlscan":     {"types": {"domain", "url"},             "needs_key": True,  "rate": "60/day"},
    # New free-tier providers
    "threatfox":   {"types": {"ip", "domain", "url", "hash"}, "needs_key": False, "rate": "public"},
    # Optional extras (wire in only if implemented and key present)
    # "securitytrails": {"types": {"domain", "ip"},          "needs_key": True,  "rate": "community"},
    # "circl_pdns":     {"types": {"domain", "ip"},          "needs_key": False, "rate": "public"},
}

# Defaults
# Order also used for CSV export sorting
DEFAULT_PROVIDERS: List[str] = [
    "virustotal",
    "abuseipdb",
    "otx",
    "threatfox",
    "urlscan",
]
DEFAULT_TTLS: Dict[str, int] = {
    "virustotal": 86400,     # 24h
    "abuseipdb": 43200,      # 12h
    "otx": 43200,            # 12h
    "urlscan": 43200,        # 12h
    "threatfox": 28800,      # 8h (6–12h window)
}
DEFAULT_TIMEOUTS: Dict[str, float] = {"normal": 15.0, "fast": 8.0, "deep": 25.0}
DEFAULT_CONCURRENCY = 6

# Conservative per-provider concurrency minima
PROVIDER_MIN_CAPS = {
    "virustotal": 2,
    "abuseipdb": 2,
    "otx": 3,
    "urlscan": 3,
    "threatfox": 4,
}


def _env_flag(name: str, default: bool = False) -> bool:
    v = str(os.getenv(name, "")).strip().lower()
    if v == "":
        return default
    return v in ("1", "true", "yes", "on")

# Centralized feature flags
URLSCAN_SUBMIT: bool = _env_flag("URLSCAN_SUBMIT", False)


def resolve_mode(mode: str) -> Tuple[bool, bool, float]:
    """Return (use_cache, refresh, timeout_seconds).

    Centralized shim: regardless of requested mode, enforce Normal semantics.
    """
    timeout = DEFAULT_TIMEOUTS.get("normal", 15.0)
    return True, False, timeout


def enabled_providers(env: Dict[str, str]) -> List[str]:
    """Return the list of providers enabled given env vars.

    Includes providers with needs_key=False always, and those with needs_key=True only if a non-empty key exists in env.
    Keys expected:
      - VIRUSTOTAL_API_KEY, ABUSEIPDB_API_KEY, OTX_API_KEY, URLSCAN_API_KEY
    """
    names: List[str] = []
    key_map = {
        "virustotal": "VIRUSTOTAL_API_KEY",
        "abuseipdb": "ABUSEIPDB_API_KEY",
        "otx": "OTX_API_KEY",
        "urlscan": "URLSCAN_API_KEY",
        # "securitytrails": "SECURITYTRAILS_API_KEY",
    }
    for name, meta in PROVIDERS.items():
        needs_key = bool(meta.get("needs_key"))
        if not needs_key:
            names.append(name)
            continue
        env_key = key_map.get(name)
        if env_key and (env.get(env_key) or ""):
            names.append(name)
    return names 