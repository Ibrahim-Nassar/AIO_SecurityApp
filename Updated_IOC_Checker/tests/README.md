# Tests

Run all tests:

```bash
pytest -q
```

The test suite creates a single QApplication instance, mocks all network calls via `httpx.AsyncClient` replacement, and pumps Qt events using `QTest.qWait`. 