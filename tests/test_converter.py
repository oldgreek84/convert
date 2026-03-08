"""Unit tests for the Converter class.

Tests the core conversion orchestration logic with mocked dependencies.
"""

from __future__ import annotations

import io
import os
import unittest
from unittest.mock import Mock, patch

from src.config import ConverterStatus, JobConfig, Target
from src.conversion_service import ConversionService
from src.converter import Converter
from src.exceptions import ConverterError
from src.validator import Validator
from tests.common import DummyJobProcessor, DummySaver, DummyWorker


def _make_format(name: str) -> Mock:
    """Create a mock Format object for testing."""
    fmt = Mock()
    fmt.name = name
    return fmt


class EventCollector:
    """Collects events emitted by Converter for test assertions."""

    def __init__(self):
        self.statuses = []
        self.messages = []
        self.errors = []
        self.results = []

    def subscribe(self, converter: Converter) -> None:
        """Subscribe to all converter events."""
        converter.events.on("status", self.statuses.append)
        converter.events.on("message", self.messages.append)
        converter.events.on("error", self.errors.append)
        converter.events.on("result", self.results.append)


def _make_converter(processor=None, saver=None, worker=None, debug=False):
    """Helper to create a Converter with ConversionService."""
    processor = processor or DummyJobProcessor()
    saver = saver or DummySaver()
    service = ConversionService(
        processor=processor,
        saver=saver,
        validator=Validator(),
    )
    return Converter(service=service, worker=worker, debug=debug)


class ConverterTestCase(unittest.TestCase):
    """Test cases for Converter class."""

    def setUp(self):
        """Set up test fixtures with all required dependencies."""
        self.processor = DummyJobProcessor()
        self.saver = DummySaver()
        self.converter = _make_converter(processor=self.processor, saver=self.saver)
        self.events = EventCollector()
        self.events.subscribe(self.converter)

    def _make_config(self, path_to_file="/path/to/file.fb2", **kwargs):
        """Helper to create a JobConfig with mock formats."""
        return JobConfig(
            fmt_from=_make_format("fb2"),
            fmt_to=_make_format("mobi"),
            target=Target(target="mobi", category="ebook", options={}),
            path_to_file=path_to_file,
            **kwargs,
        )

    def test_init_creates_converter(self):
        """Test that __init__ creates converter with all dependencies."""
        self.assertIsNotNone(self.converter)
        self.assertIsNotNone(self.converter.service)
        self.assertIsNotNone(self.converter.events)

    def test_convert_calls_internal_convert(self):
        """Test that convert() calls _convert method."""
        config = self._make_config()

        with patch.object(self.converter, "_convert") as mocked:
            self.converter.convert(config)
            mocked.assert_called_once()

    def test_convert_sets_processing_status(self):
        """Test that convert() sets status to PROCESSING."""
        config = self._make_config()

        with patch.object(self.converter, "_convert"):
            self.converter.convert(config)

        self.assertIn(ConverterStatus.PROCESSING, self.events.statuses)

    @patch("src.validator.get_format_service")
    def test_convert_with_wrong_file_path_raises_error(self, mock_get_fs):
        """Test that _convert raises ConverterError for invalid file path."""
        mock_get_fs.return_value.validate_conversion.return_value = True
        config = self._make_config(path_to_file="wrong/path/to/file")
        self.converter.config = config

        with self.assertRaises(ConverterError) as ex:
            self.converter._convert()
        self.assertIn("Invalid file path", str(ex.exception))

    def test_setup_converter_executor_returns_callable(self):
        """Test that setup_converter_executor returns a callable."""
        executor = self.converter.setup_converter_executor()
        self.assertTrue(callable(executor))

    def test_setup_converter_executor_with_worker(self):
        """Test that setup_converter_executor uses worker when available."""
        worker = DummyWorker()
        self.converter.worker = worker
        executor = self.converter.setup_converter_executor()
        self.assertTrue(callable(executor))

    def test_status_returns_current_status(self):
        """Test that status property returns the current converter status."""
        self.assertEqual(self.converter.status, ConverterStatus.READY)

    def test_error_handler_sets_failed_status(self):
        """Test that error_handler sets status to FAILED and emits error event."""
        self.converter.error_handler(Exception("test error"))

        self.assertTrue(any("failed" in str(s) for s in self.events.statuses))
        self.assertTrue(any("test error" in str(e) for e in self.events.errors))

    def test_error_handler_debug_mode(self):
        """Test that error_handler includes context when debug=True."""
        converter = _make_converter(
            processor=self.processor, saver=self.saver, debug=True
        )
        events = EventCollector()
        events.subscribe(converter)
        converter.error_handler(Exception("test error"))

        self.assertTrue(any("failed" in str(s) for s in events.statuses))
        self.assertTrue(any("Context:" in str(e) for e in events.errors))

    @patch("src.validator.get_format_service")
    def test_full_conversion_flow(self, mock_get_fs):
        """Test complete conversion flow with all components."""
        mock_get_fs.return_value.validate_conversion.return_value = True
        path_to_file = os.path.abspath(__file__)
        config = self._make_config(path_to_file=path_to_file, path_to_save="/output")

        service = self.converter.service
        with (
            patch.object(service.processor, "send_job", return_value="job123"),
            patch.object(service.processor, "get_job_status", return_value=["Processing"]),
            patch.object(
                service.processor,
                "get_job_result",
                return_value=("result.mobi", io.BytesIO(b"data")),
            ),
        ):
            self.converter.convert(config)

        self.assertTrue(any("completed" in str(s) for s in self.events.statuses))
        self.assertTrue(len(self.events.results) > 0)

    @patch("src.validator.get_format_service")
    def test_full_conversion_emits_messages(self, mock_get_fs):
        """Test that conversion emits message events for job ID and status."""
        mock_get_fs.return_value.validate_conversion.return_value = True
        path_to_file = os.path.abspath(__file__)
        config = self._make_config(path_to_file=path_to_file, path_to_save="/output")

        service = self.converter.service
        with (
            patch.object(service.processor, "send_job", return_value="job123"),
            patch.object(service.processor, "get_job_status", return_value=["Processing"]),
            patch.object(
                service.processor,
                "get_job_result",
                return_value=("result.mobi", io.BytesIO(b"data")),
            ),
        ):
            self.converter.convert(config)

        self.assertTrue(any("Job ID" in str(m) for m in self.events.messages))
        self.assertTrue(any("Processing" in str(m) for m in self.events.messages))


if __name__ == "__main__":
    unittest.main()
