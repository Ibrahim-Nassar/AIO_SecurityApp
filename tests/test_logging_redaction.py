from io import StringIO

from ioc_core.logger import get_logger
from ioc_core import setup_logging_redaction, _ApiKeyRedactor
import logging


def test_logging_redacts_api_keys(monkeypatch):
    setup_logging_redaction()
    logger = get_logger()
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(_ApiKeyRedactor())
    logger.addHandler(handler)
    try:
        logger.info("Testing API_KEY=abcdef123456 and Authorization=secrettoken")
        handler.flush()
        data = stream.getvalue()
        assert "API_KEY=***REDACTED***" in data
        assert "Authorization=***REDACTED***" in data
        assert "abcdef123456" not in data
        assert "secrettoken" not in data
    finally:
        logger.removeHandler(handler) 