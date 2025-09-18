# Contributing

Thank you for contributing to IOC Checker. This project uses Conventional Commits and enforces basic quality gates (lint, type check, tests).

## Conventional Commits

Use one of the following types in your commit messages:
- feat: a new feature (e.g., `feat(providers): add retry logic`)
- fix: a bug fix
- chore: repo chores (deps, scripts, config)
- refactor: code refactor without behavior change
- style: code style, formatting (no logic changes)
- docs: documentation only changes
- test: add or improve tests
- ci: CI-related changes

Scope is optional but recommended (e.g., `(ui)`, `(providers)`).

## Local checks

```bash
# Lint
ruff .

# Type check (may report warnings)
mypy .

# Run tests (headless Qt if needed)
# Windows PowerShell
$env:QT_QPA_PLATFORM='offscreen'; pytest -q
# Linux/macOS
QT_QPA_PLATFORM=offscreen pytest -q
```

## Secrets and Environment

- Do not commit real API keys. The app reads keys from a per-user `.env` file:
  - Windows: %LOCALAPPDATA%/UpdatedIOCChecker/.env
  - macOS:   $HOME/Library/Application Support/UpdatedIOCChecker/.env
  - Linux:   $HOME/.config/UpdatedIOCChecker/.env
- Tests must not use the network. Use the provided `FakeAsyncClient`.

## Pull Requests

- Keep changes focused and reviewable.
- Include or update tests as appropriate.
- Ensure `pytest -q` passes locally (headless).


