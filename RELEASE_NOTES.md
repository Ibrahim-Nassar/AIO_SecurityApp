# Release Notes

Version: 0.9.0 (2025-09-20)

## Highlights
- Urlscan provider fully removed across codebase and test suite; providers now focus on VirusTotal, OTX, AbuseIPDB (and ThreatFox, if enabled).
- Provider robustness improved: standardized retries/backoff for 429, 503, and timeouts; consistent error handling and latency tracking.
- UI polish and startup hardening:
  - Headless-friendly startup; per-user .env auto-migration from CWD on first run.
  - Toast notification on environment load; consistent theme base size; resilient resource registration.
- Test architecture split into buckets to prevent GUI hiccups from blocking unit tests:
  - `providers` (pure unit): fast, deterministic, offline.
  - `gui` (headless smoke): self-terminating watchdog prevents hangs.
- CI updated to run buckets separately while keeping lint and type-check steps.
- Internal cleanup: removed duplicate/legacy module trees and tightened imports.

## Breaking changes
- Urlscan integration removed (previously deprecated).
  - Any direct references to Urlscan classes, CLI flags, or `URLSCAN_*` environment variables must be removed.

## Migration notes
- Urlscan: remove Urlscan-specific configuration/env and code paths. No replacement is required for core workflows; remaining providers cover common IOC checks.
- Tests/CI:
  - Use markers to run buckets: `-m providers` for unit providers, `-m gui` for headless smoke.
  - GUI smoke test is forced headless and fails fast on stalls; keep `QT_QPA_PLATFORM=offscreen` in CI and local headless runs.
- Environment file: the app now prefers a per-user `.env` location. On first run it auto-migrates from the project CWD if present; no manual action required in most cases.

## QA summary
- Providers bucket: green on Windows and Linux, fully offline via fakes/fixtures; covers 429/503/timeout and malformed JSON scenarios.
- GUI bucket: guarded smoke test completes under ~1s locally; watchdog hard-fails after 6s if blocked.
- Headless operation verified via `QT_QPA_PLATFORM=offscreen`.
- CI continues to run lint (ruff) and type check (mypy, warn-only) before test buckets. 