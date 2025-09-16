How to run diagnostics smoke tests (Windows / Python 3.11)

Prereqs:
- Only stdlib, httpx, python-dotenv are used by the app; tests will run with these.

Steps:
1) Optional: set env vars for provider keys (do NOT share real secrets)
   - VIRUSTOTAL_API_KEY, ABUSEIPDB_API_KEY, OTX_API_KEY
   
2) Enable diagnostics mode (optional):
   - set DIAGNOSTICS=1
   - optional for file debug logging: set IOC_GUI_DEBUG=1
3) Run the smoke tests:
   - python diagnostics/smoke_test.py

Output:
- The script prints single-line PASS/FAIL messages per test, then a summary block:

===== SMOKE RESULTS =====
Providers: PASS/FAIL - <reason>
CSV Export: PASS/FAIL - <reason>
Sandbox: removed
UI Responsiveness: PASS/FAIL - <reason>
Mode Toggle: PASS/FAIL - <reason>
Cache: PASS/FAIL - <reason>

Notes:
- Network-dependent tests handle rate limits gracefully and will not crash the app.
- No API keys are logged; avoid using real keys on shared systems.
