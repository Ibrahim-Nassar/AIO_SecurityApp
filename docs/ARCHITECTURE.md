# Architecture Overview

## Modules
- ioc_core: core logic
  - config.py: central config (provider registry, defaults, feature flags like URLSCAN_SUBMIT)
  - models.py: data models and helpers (classify_ioc, vt_url_id, now_utc, aggregate)
  - cache.py: SQLite cache
  - services.py: providers (VirusTotal, AbuseIPDB, OTX, ThreatFox), enrich/check flows (Urlscan removed)
  - export.py: CSV/JSON exports and mirrored CSV writer
- qt_app: Qt UI (PySide6)
  - main.py: QApplication bootstrap + MainWindow
  - views/: pages (`ioc_checker_page.IocCheckerPage`, `settings_page.SettingsPage`, `main_window.MainWindow`)
  - ui/: theme, widgets (`BusyOverlay`, `Toast`, `SectionCard`)
  - res/: icons, resources.qrc compiled at runtime if available
- ioc_checker: legacy shim package for compatibility; new code should use `ioc_core` directly. GUI imports nothing from `ioc_checker`.

## Flow
- UI emits actions to workers calling `ioc_core.services` (no direct network in UI).
- All external HTTP uses `httpx` via core services.
- Provider registry and feature flags live in `ioc_core.config`.
- Config/secrets set via `.env` in Settings page; runtime uses env vars.
- Logging redaction in `ioc_core.setup_logging_redaction`; API keys never logged.

```mermaid
flowchart LR
    GUI[Qt UI (qt_app)] --> W[AsyncTaskWorker]
    W --> S[Service layer: ioc_core.services.check_iocs]
    S --> P[Providers: VT, AbuseIPDB, OTX, ThreatFox]
    S --> C[(SQLite Cache)]
    P --> H[(httpx AsyncClient)]
```

## Typing and linting
- `pyproject.toml` sets Python target to 3.10 and enables mypy strict for `ioc_core` and `qt_app`.
- PEP 561 markers (`py.typed`) are present in `ioc_core/` and `qt_app/`.
- Ruff and Black target 3.10 to match runtime.

## Workers + Signals
- `qt_app.workers.AsyncTaskWorker` runs coroutines in a thread and emits:
  - resultsReady(object)
  - errorOccurred(str)
  - finishedSignal()
- Pages connect to these signals to update UI safely. 