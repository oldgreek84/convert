"""Unit tests for config classes."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from src.config import ConverterStatus, JobConfig, SetupConfig, Target
from src.exceptions import ConfigurationError


class TestConverterStatus(unittest.TestCase):
    """Test cases for ConverterStatus enum."""

    def test_values(self):
        self.assertEqual(ConverterStatus.READY, "ready")
        self.assertEqual(ConverterStatus.PROCESSING, "processing")
        self.assertEqual(ConverterStatus.FAILED, "failed")
        self.assertEqual(ConverterStatus.COMPLETED, "completed")

    def test_is_str(self):
        self.assertIsInstance(ConverterStatus.READY, str)


class TestTarget(unittest.TestCase):
    """Test cases for Target dataclass."""

    def test_create_with_defaults(self):
        target = Target(target="mobi", category="ebook")
        self.assertEqual(target.target, "mobi")
        self.assertEqual(target.category, "ebook")
        self.assertEqual(target.options, {})

    def test_create_with_options(self):
        target = Target(target="pdf", category="ebook", options={"dpi": 150})
        self.assertEqual(target.options, {"dpi": 150})


class TestJobConfig(unittest.TestCase):
    """Test cases for JobConfig dataclass."""

    def setUp(self):
        self.target = Target(target="mobi", category="ebook", options={"quality": 90})
        self.config = JobConfig(self.target, "/path/to/file.fb2", path_to_save="/output")

    def test_properties(self):
        self.assertEqual(self.config.job_target, "mobi")
        self.assertEqual(self.config.job_category, "ebook")
        self.assertEqual(self.config.job_options, {"quality": 90})

    def test_default_path_to_save(self):
        config = JobConfig(self.target, "/path/to/file.fb2")
        self.assertEqual(config.path_to_save, "books")

    def test_get_config(self):
        result = self.config.get_config()
        self.assertEqual(result, {
            "category": "ebook",
            "target": "mobi",
            "options": {"quality": 90},
        })


class TestSetupConfig(unittest.TestCase):
    """Test cases for SetupConfig."""

    def test_check_direction_valid(self):
        format_from = Mock()
        format_from.name = "fb2"
        format_to = Mock()
        format_to.get_allowed_formats.return_value = ["fb2", "mobi"]

        config = SetupConfig(format_from, format_to)
        config.check_direction()  # should not raise

    def test_check_direction_invalid(self):
        format_from = Mock()
        format_from.name = "fb2"
        format_from.extension = ".fb2"
        format_to = Mock()
        format_to.get_allowed_formats.return_value = ["mobi", "pdf"]
        format_to.extension = ".txt"

        config = SetupConfig(format_from, format_to)
        with self.assertRaises(ConfigurationError) as ctx:
            config.check_direction()
        self.assertIn("Wrong direction", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
