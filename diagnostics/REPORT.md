# IOC Checker Health Report

## Project status
The project runs as a single-file GUI/CLI with modular providers (VirusTotal, AbuseIPDB, OTX) and optional urlscan (URL-only). GUI stays responsive via background threads; Sandbox has been removed; Hybrid Analysis integration deprecated. Cache is SQLite-backed; CSV mirror export is available.

## Smoke test results
| Test | Result |
|---|---|
| Providers | TBD (run diagnostics/smoke_test.py) |
| CSV Export | TBD |
| Sandbox | TBD |
| UI Responsiveness | TBD |
| Mode Toggle | TBD |
| Cache | TBD |

## Immediate fixes (if any failures)
- Example: Sandbox finalization failed
  - Ensure `_run_coro_in_thread` timeout is applied (NEW_IOC_CHECKER.py)
  - Verify Result write uses `_result_write` and buttons re-enable in finally
- Example: CSV mirror header mismatch
  - Check `_write_mirrored_csv` header row composition (NEW_IOC_CHECKER.py)
- Example: Provider exception bubbles up
  - Wrap provider `.query` in try/except and convert to friendly ProviderResult (NEW_IOC_CHECKER.py)

## Next priorities
- Add optional provider-level retry/backoff telemetry and metrics (no secrets).
- Add a small in-app “Diagnostics” pane to surface mode, timeouts, and cache hits safely.
