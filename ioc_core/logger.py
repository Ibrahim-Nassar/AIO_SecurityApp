from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler


_LOGGER_NAME = "ioc_diag"


def _ensure_log_dir() -> str:
    base = os.path.join(os.getcwd(), "logs")
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        pass
    return base


def setup_diagnostics_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_dir = _ensure_log_dir()
    path = os.path.join(log_dir, "app.log")
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(fmt)
    # Ensure redaction filter is applied to this handler as well
    try:
        from ioc_core import _ApiKeyRedactor  # type: ignore
        handler.addFilter(_ApiKeyRedactor())
    except Exception:
        pass
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger() -> logging.Logger:
    return setup_diagnostics_logger()


