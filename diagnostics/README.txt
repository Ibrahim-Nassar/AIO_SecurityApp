AUDIT SUMMARY (IOC Checker: GUI + CLI)

1) Providers in GUI
- Providers wired: VirusTotal, AbuseIPDB, OTX, urlscan (URL-only). The GUI builds provider list from checkboxes and config, and columns are created dynamically per selected providers. Urlscan is used only for IOC enrichment (URLs), not for Sandbox.

2) CSV mirror export
- Single-file GUI path: _write_mirrored_csv(...) writes the original CSV columns plus one column per enabled provider (order matches grid), with values like "STATUS [score]". A separate simple exporter writes minimal CSV for non-CSV runs.

3) Sandbox (removed)

4) Result widgets and buttons
- IOC view: summary Text is editable (by design for copy/annotate). Sandbox Result Text is read-only (state=disabled) with helper methods enforcing write/append pattern. Submit buttons are re-enabled via finally blocks.

5) Concurrency + Mode
- Enrichment uses a batch-scoped semaphore and a single AsyncClient per batch. Mode toggle (Normal/Fast/Deep) adjusts timeouts and cache/refresh flags; applied in the async run loop.

Notes
- No API keys are logged or displayed; secrets are masked. All network I/O occurs off the Tk thread; UI updates via root.after.
