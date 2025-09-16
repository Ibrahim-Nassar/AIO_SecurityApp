"""Core services, models, cache, and exports for IOC Checker.

This package exposes provider/network/cache/export APIs for reuse by Tk and Qt UIs.
"""

from __future__ import annotations

import logging
import re
from typing import Match


class _ApiKeyRedactor(logging.Filter):
    _pattern = re.compile(r"(?i)(api[_-]?key|authorization)[=:]\s*([A-Za-z0-9._-]{6,})")

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = str(record.getMessage())
            if not msg:
                return True
            def _repl(m: Match[str]) -> str:
                key = m.group(1)
                return f"{key}=***REDACTED***"
            record.msg = self._pattern.sub(_repl, msg)
        except Exception:
            pass
        return True


def setup_logging_redaction() -> None:
    root = logging.getLogger()
    for h in list(root.handlers):
        h.addFilter(_ApiKeyRedactor())

from . import config, models, cache, services, export  # noqa: F401

__all__ = [
    "setup_logging_redaction",
    "config",
    "models",
    "cache",
    "services",
    "export",
] 