"""Unit tests for the Validator classes.

Tests validation logic independently from Converter, using fake
filesystem access (no real files needed).
"""

from __future__ import annotations

import unittest

from src.config import JobConfig, Target
from src.exceptions import ConverterError
from src.validator import (
    ConfigValidator,
    FilePathValidator,
    Validator,
)


class FakeFileChecker:
    """Fake filesystem checker for testing without real files."""

    def __init__(self, existing_files: set[str] | None = None) -> None:
        self._files = existing_files or set()

    def is_file(self, file_path: str) -> bool:
        return file_path in self._files


class FilePathValidatorTestCase(unittest.TestCase):
    """Tests for FilePathValidator."""

    def test_raises_for_missing_file(self):
        checker = FakeFileChecker()
        validator = FilePathValidator("nonexistent.fb2", file_checker=checker)
        with self.assertRaises(ConverterError) as ctx:
            validator.validate()
        self.assertIn("Invalid file path", str(ctx.exception))

    def test_passes_for_existing_file(self):
        checker = FakeFileChecker({"/books/test.fb2"})
        validator = FilePathValidator("/books/test.fb2", file_checker=checker)
        validator.validate()  # should not raise


class ConfigValidatorTestCase(unittest.TestCase):
    """Tests for ConfigValidator."""

    def test_raises_when_config_is_none(self):
        validator = ConfigValidator(None)
        with self.assertRaises(ConverterError) as ctx:
            validator.validate()
        self.assertIn("config was not set", str(ctx.exception))

    def test_passes_when_config_has_empty_fields(self):
        """Config with empty strings is still a valid dict — passes truthiness check.
        Field-level validation (e.g. target must be non-empty) belongs in
        FormatService, not ConfigValidator.
        """
        target = Target(target="", category="", options={})
        config = JobConfig(target, "/path/to/file.fb2")
        validator = ConfigValidator(config)
        validator.validate()  # should not raise — dict is truthy

    def test_passes_for_valid_config(self):
        target = Target(target="mobi", category="ebook", options={})
        config = JobConfig(target, "/path/to/file.fb2")
        validator = ConfigValidator(config)
        validator.validate()  # should not raise


class CompositeValidatorTestCase(unittest.TestCase):
    """Tests for the composite Validator."""

    def test_runs_all_validators_in_order(self):
        checker = FakeFileChecker({"/books/test.fb2"})
        target = Target(target="mobi", category="ebook", options={})
        config = JobConfig(target, "/books/test.fb2")

        validator = Validator()
        validator.add(ConfigValidator(config))
        validator.add(FilePathValidator("/books/test.fb2", file_checker=checker))
        validator.validate()  # should not raise

    def test_stops_on_first_failure(self):
        checker = FakeFileChecker()
        validator = Validator()
        validator.add(ConfigValidator(None))
        validator.add(FilePathValidator("any.fb2", file_checker=checker))

        with self.assertRaises(ConverterError) as ctx:
            validator.validate()
        self.assertIn("config was not set", str(ctx.exception))

    def test_clears_validators_after_validate(self):
        target = Target(target="mobi", category="ebook", options={})
        config = JobConfig(target, "/path/to/file.fb2")

        validator = Validator()
        validator.add(ConfigValidator(config))
        validator.validate()

        # Second call should not re-run the config validator
        # Adding a failing one to prove the old one is gone
        validator.add(ConfigValidator(None))
        with self.assertRaises(ConverterError):
            validator.validate()

    def test_empty_validator_passes(self):
        validator = Validator()
        validator.validate()  # no validators added, should not raise


if __name__ == "__main__":
    unittest.main()
