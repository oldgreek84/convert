"""Unit tests for the Validator classes.

Tests validation logic independently from Converter, using fake
filesystem access (no real files needed).
"""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from src.config import JobConfig, Target
from src.exceptions import ConverterError, FormatError
from src.validator import (
    ConfigValidator,
    ConversionDirectionValidator,
    FilePathValidator,
    Validator,
)


def _make_format(name: str) -> Mock:
    """Create a mock Format object for testing."""
    fmt = Mock()
    fmt.name = name
    return fmt


def _make_config(**kwargs) -> JobConfig:
    """Create a JobConfig with mock formats for testing."""
    defaults = {
        "fmt_from": _make_format("fb2"),
        "fmt_to": _make_format("mobi"),
        "target": Target(target="mobi", category="ebook", options={}),
        "path_to_file": "/path/to/file.fb2",
    }
    defaults.update(kwargs)
    return JobConfig(**defaults)


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
        config = _make_config(target=Target(target="", category="", options={}))
        validator = ConfigValidator(config)
        validator.validate()  # should not raise — dict is truthy

    def test_passes_for_valid_config(self):
        config = _make_config()
        validator = ConfigValidator(config)
        validator.validate()  # should not raise


class ConversionDirectionValidatorTestCase(unittest.TestCase):
    """Tests for ConversionDirectionValidator."""

    def test_passes_for_valid_conversion(self):
        format_service = Mock()
        format_service.validate_conversion.return_value = True

        validator = ConversionDirectionValidator(
            fmt_from="fb2", fmt_to="mobi", format_service=format_service,
        )
        validator.validate()  # should not raise
        format_service.validate_conversion.assert_called_once_with("fb2", "mobi")

    def test_raises_for_invalid_conversion(self):
        format_service = Mock()
        format_service.validate_conversion.side_effect = FormatError(
            "Conversion from 'fb2' to 'mp3' is not allowed"
        )

        validator = ConversionDirectionValidator(
            fmt_from="fb2", fmt_to="mp3", format_service=format_service,
        )
        with self.assertRaises(FormatError) as ctx:
            validator.validate()
        self.assertIn("not allowed", str(ctx.exception))


class CompositeValidatorTestCase(unittest.TestCase):
    """Tests for the composite Validator."""

    def test_runs_all_validators_in_order(self):
        checker = FakeFileChecker({"/books/test.fb2"})
        config = _make_config(path_to_file="/books/test.fb2")

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
        config = _make_config()

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
