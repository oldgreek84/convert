"""Unit tests for exception classes and utility functions."""

from __future__ import annotations

import unittest

from src.exceptions import (
    ConfigurationError,
    ConverterError,
    FormatError,
    ParamsError,
    ProcessorError,
    create_error_context,
    handle_exception_chain,
)


class TestConverterError(unittest.TestCase):
    """Test cases for ConverterError base class."""

    def test_str_without_error_code(self):
        err = ConverterError("something failed")
        self.assertEqual(str(err), "something failed")

    def test_str_with_error_code(self):
        err = ConverterError("something failed", error_code="E001")
        self.assertEqual(str(err), "[E001] something failed")

    def test_attributes(self):
        err = ConverterError("msg", error_code="E001", details={"key": "val"})
        self.assertEqual(err.message, "msg")
        self.assertEqual(err.error_code, "E001")
        self.assertEqual(err.details, {"key": "val"})

    def test_details_defaults_to_empty_dict(self):
        err = ConverterError("msg")
        self.assertEqual(err.details, {})


class TestExceptionHierarchy(unittest.TestCase):
    """Test that exception hierarchy is correct."""

    def test_configuration_error_is_converter_error(self):
        self.assertIsInstance(ConfigurationError("x"), ConverterError)

    def test_params_error_is_configuration_error(self):
        self.assertIsInstance(ParamsError("x"), ConfigurationError)

    def test_processor_error_is_converter_error(self):
        self.assertIsInstance(ProcessorError("x"), ConverterError)

    def test_format_error_is_converter_error(self):
        self.assertIsInstance(FormatError("x"), ConverterError)


class TestCreateErrorContext(unittest.TestCase):
    """Test cases for create_error_context utility."""

    def test_returns_dict_with_standard_keys(self):
        ctx = create_error_context()
        self.assertIn("timestamp", ctx)
        self.assertIn("python_version", ctx)
        self.assertIn("traceback", ctx)

    def test_includes_custom_kwargs(self):
        ctx = create_error_context(error=ValueError("test"), custom="data")
        self.assertIn("error", ctx)
        self.assertIn("custom", ctx)
        self.assertEqual(ctx["custom"], "data")


class TestHandleExceptionChain(unittest.TestCase):
    """Test cases for handle_exception_chain utility."""

    def test_single_exception(self):
        err = ValueError("root cause")
        messages = handle_exception_chain(err)
        self.assertEqual(messages, ["root cause"])

    def test_chained_exceptions(self):
        try:
            try:
                raise ValueError("original")
            except ValueError as e:
                raise RuntimeError("wrapper") from e
        except RuntimeError as e:
            messages = handle_exception_chain(e)

        self.assertEqual(messages, ["wrapper", "original"])


if __name__ == "__main__":
    unittest.main()
