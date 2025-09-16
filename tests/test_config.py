# Module map: ioc_checker.config -> load_env, validate_config, mask_secret
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from ioc_checker import config


class TestConfig(unittest.TestCase):
    def test_mask_secret(self):
        # <=4 characters: fully masked
        self.assertEqual(config.mask_secret("abcd"), "****")
        # >4 characters: all but last 4 masked
        masked = config.mask_secret("abcdef")
        self.assertTrue(masked.endswith("cdef"))
        self.assertEqual(masked[:-4], "**")

    def test_load_env_no_file(self):
        with mock.patch("dotenv.load_dotenv", side_effect=Exception("nope")):
            # Should not raise
            config.load_env()

    def test_validate_config_noop(self):
        # Should not raise
        config.validate_config()


