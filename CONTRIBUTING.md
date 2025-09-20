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

## Reproduce env

```bash
# Fresh clone
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
```

## Regenerate lock

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pip freeze > requirements-lock.txt
```

## Optional: local precommit hook

```bash
# Use repo-managed hooks
git config core.hooksPath .githooks

# On Windows, PowerShell script will run; on *nix, bash fallback is used
# Bypass for a commit (e.g., when adding test fixtures):
# PowerShell
$env:SKIP_SECRET_CHECK='1'; git commit -m "..."; Remove-Item Env:SKIP_SECRET_CHECK
# Bash
SKIP_SECRET_CHECK=1 git commit -m "..."
```

## Local checks

```bash
# Lint
ruff .

# Type check (may report warnings)
mypy .

# Run tests (headless Qt if needed)
# Providers only
$env:QT_QPA_PLATFORM='offscreen'; pytest -q -m providers
# GUI only
$env:QT_QPA_PLATFORM='offscreen'; pytest -q -m gui
# Linux/macOS examples
QT_QPA_PLATFORM=offscreen pytest -q -m providers
QT_QPA_PLATFORM=offscreen pytest -q -m gui
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


