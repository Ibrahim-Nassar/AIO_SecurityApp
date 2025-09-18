# CLEANUP REPORT

## Removed (Hybrid Analysis and Sandbox)
- qt_app/views/sandbox_page.py — removed (deprecated HA sandbox UI)
- HA config and search helpers removed from `ioc_core.config` and `ioc_core.services`
- Settings: removed Hybrid Analysis key
- Tests: removed `tests/test_sandbox_page.py`

## Updated
- qt_app/__init__.py — Qt is the only UI
- tests/helpers.py — removed Tk harness remnants
- docs/ARCHITECTURE.md — updated to reflect provider registry and UI pages
- ioc_core/config.py — added provider registry, TTLs, defaults, `enabled_providers()`
- ioc_core/services.py — added ThreatFox provider; added 429 retry/backoff
- qt_app/views/ioc_checker_page.py — added ThreatFox checkbox (default on)
- qt_app/views/main_window.py — removed Sandbox page from navigation
- qt_app/views/settings_page.py — removed `GREYNOISE_API_KEY` field

## Providers
- Kept: VirusTotal, AbuseIPDB, OTX, ThreatFox (Urlscan removed)
- Added: ThreatFox (keyless, public)
- Optional (not implemented here): SecurityTrails, CIRCL PDNS

## Caching & Rate Handling
- Cache TTLs: ThreatFox ≈8h
- 429: up to 2 retries with backoff (0.8s → 1.6s); honor Retry-After (≤5s)

## Tests
- Updated core services and UI tests for new providers
- Removed sandbox tests

## Verification
- Launch GUI: `python -m qt_app.main`
- grep -i "hybrid|falcon|sandbox" → none
- All network calls are mocked in tests 