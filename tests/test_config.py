"""Unit tests for config classes."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from src.config import ConverterStatus, JobConfig, Target


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


def _make_format(name: str) -> Mock:
    """Create a mock Format object for testing."""
    fmt = Mock()
    fmt.name = name
    return fmt


class TestJobConfig(unittest.TestCase):
    """Test cases for JobConfig dataclass."""

    def setUp(self):
        self.fmt_from = _make_format("fb2")
        self.fmt_to = _make_format("mobi")
        self.target = Target(target="mobi", category="ebook", options={"quality": 90})
        self.config = JobConfig(
            fmt_from=self.fmt_from,
            fmt_to=self.fmt_to,
            target=self.target,
            path_to_file="/path/to/file.fb2",
            path_to_save="/output",
        )

    def test_properties(self):
        self.assertEqual(self.config.job_target, "mobi")
        self.assertEqual(self.config.job_category, "ebook")
        self.assertEqual(self.config.job_options, {"quality": 90})

    def test_default_path_to_save(self):
        config = JobConfig(
            fmt_from=self.fmt_from,
            fmt_to=self.fmt_to,
            target=self.target,
            path_to_file="/path/to/file.fb2",
        )
        self.assertEqual(config.path_to_save, "books")

    def test_get_config(self):
        result = self.config.get_config()
        self.assertEqual(result, {
            "category": "ebook",
            "target": "mobi",
            "options": {"quality": 90},
        })

    def test_fmt_from_and_fmt_to(self):
        self.assertEqual(self.config.fmt_from.name, "fb2")
        self.assertEqual(self.config.fmt_to.name, "mobi")


if __name__ == "__main__":
    unittest.main()
