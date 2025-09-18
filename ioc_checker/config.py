from __future__ import annotations

# Compatibility shim: re-export defaults from core config
from ioc_core.config import DEFAULT_TTLS, DEFAULT_PROVIDERS, DEFAULT_TIMEOUTS  # noqa: F401

APP_TITLE = "IOC Checker (VT, AbuseIPDB, OTX, ThreatFox)"
CACHE_DB = ".ioc_enricher_cache.sqlite"


def load_env() -> None:  # no-op retained for compatibility
    try:
        import dotenv  # type: ignore
        dotenv.load_dotenv()
    except Exception:
        pass


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    v = str(value)
    if len(v) <= 4:
        return "*" * len(v)
    return "*" * (len(v) - 4) + v[-4:]


def validate_config(debug: bool = False) -> None:
    # no-op placeholder
    return None


