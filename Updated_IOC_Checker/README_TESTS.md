# IOC Checker Test Suite

This suite uses only stdlib modules (`unittest`, `asyncio`, `unittest.mock`) and runs offline. No network calls are allowed.

## How to run

- Run all tests:

```
python -m unittest discover -s tests -p "test_*.py" -v
```

- Run a single module:

```
python -m unittest tests.test_utils -v
```

- Run selective tests using patterns:

```
# Sandbox-related tests have been removed.
```

## Network isolation

All external network is prohibited. `tests/helpers.py` provides `block_network()` to enforce this, and provider/service tests patch `httpx.AsyncClient` to a `FakeAsyncClient` that returns canned `httpx.Response` objects.

## Simulating redirects/timeouts

- 301 redirect test uses a prepared 301 response (with `Location` header) followed by a 200 JSON response.
- Polling/backoff tests are time-agnostic and do not sleep; they inject canned responses and short-circuit loops.

## Coverage via stdlib `trace`

You can generate a simple coverage report with:

```
python -m trace --count --summary -m unittest discover -s tests -p "test_*.py"
```

This prints a line/statement summary for modules imported during tests.

## Bundler smoke test

If present, build the single-file deliverable and perform a quick run:

```
python tools/make_single.py
python IOC_Checker_SINGLE.py --help
```

This should print usage or run the GUI without error. It must not launch the GUI in test mode.

## Notes

- No secrets are printed; set dummy env vars in your environment if needed.
- UI tests use PySide6 and avoid long sleeps.
- Non-UI modules aim at ≥85% coverage; UI modules are smoke tested only.
