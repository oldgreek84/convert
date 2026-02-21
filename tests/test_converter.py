"""Unit tests for the Converter class.

Tests the core conversion orchestration logic with mocked dependencies.
"""

from __future__ import annotations

import io
import os
import unittest
from unittest.mock import patch

from src.config import JobConfig, Target
from src.converter import Converter
from src.exceptions import ConverterError
from tests.common import DummyJobProcessor, DummySaver, DummyWorker


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


class ConverterTestCase(unittest.TestCase):
    """Test cases for Converter class."""

    def setUp(self):
        """Set up test fixtures with all required dependencies."""
        self.processor = DummyJobProcessor()
        self.saver = DummySaver()
        self.converter = Converter(processor=self.processor, saver=self.saver)
        self.events = EventCollector()
        self.events.subscribe(self.converter)

    def test_init_creates_converter(self):
        """Test that __init__ creates converter with all dependencies."""
        self.assertIsNotNone(self.converter)
        self.assertEqual(self.converter.processor, self.processor)
        self.assertEqual(self.converter.saver, self.saver)
        self.assertIsNotNone(self.converter.events)

    def test_set_config(self):
        """Test that set_config stores the configuration."""
        target = Target(target="mobi", category="ebook", options={})
        config = JobConfig(target, "/path/to/file.fb2")
        self.converter.set_config(config)
        self.assertEqual(self.converter.config, config)

    def test_convert_calls_internal_convert(self):
        """Test that convert() calls _convert method."""
        target = Target(target="mobi", category="ebook", options={})
        config = JobConfig(target, "/path/to/file.fb2")

        with patch.object(self.converter, "_convert") as mocked:
            self.converter.convert(config)
            mocked.assert_called_once()

    def test_convert_without_config_raises_error(self):
        """Test that _convert raises ConverterError when config is not set."""
        with self.assertRaises(ConverterError) as ex:
            self.converter._convert()
        self.assertIn("config was not set", str(ex.exception))

    def test_convert_with_wrong_file_path_raises_error(self):
        """Test that _convert raises ConverterError for invalid file path."""
        target = Target(target="mobi", category="ebook", options={})
        config = JobConfig(target, "wrong/path/to/file")
        self.converter.set_config(config)

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

    def test_get_status_returns_current_status(self):
        """Test that get_status returns the current converter status."""
        self.assertEqual(self.converter.get_status(), "ready")

    def test_prepare_params_delegates_to_processor(self):
        """Test that prepare_params delegates to processor."""
        options = {"target": "mobi", "category": "ebook", "options": {}}
        result = self.converter.prepare_params(options)
        self.assertEqual(result, options)

    def test_get_file_path(self):
        """Test that get_file_path returns path from config."""
        target = Target(target="mobi", category="ebook", options={})
        config = JobConfig(target, "/path/to/file.fb2")
        self.converter.set_config(config)
        self.assertEqual(self.converter.get_file_path(), "/path/to/file.fb2")

    def test_get_job_options(self):
        """Test that get_job_options returns config options."""
        target = Target(target="mobi", category="ebook", options={"quality": 90})
        config = JobConfig(target, "/path/to/file.fb2")
        self.converter.set_config(config)

        options = self.converter.get_job_options()
        self.assertIn("target", options)
        self.assertIn("category", options)

    def test_send_job(self):
        """Test that send_job sends job to processor."""
        path_to_file = os.path.abspath(__file__)
        target = Target(target="mobi", category="ebook", options={})
        config = JobConfig(target, path_to_file)
        self.converter.set_config(config)

        job_id = self.converter.send_job()
        self.assertEqual(job_id, "test_job_id")

    def test_error_handler_sets_failed_status(self):
        """Test that error_handler sets status to FAILED and emits error event."""
        self.converter.error_handler(Exception("test error"))

        self.assertTrue(any("failed" in str(s) for s in self.events.statuses))
        self.assertTrue(any("test error" in str(e) for e in self.events.errors))

    def test_error_handler_debug_mode(self):
        """Test that error_handler includes context when debug=True."""
        converter = Converter(processor=self.processor, saver=self.saver, debug=True)
        events = EventCollector()
        events.subscribe(converter)
        converter.error_handler(Exception("test error"))

        self.assertTrue(any("failed" in str(s) for s in events.statuses))
        self.assertTrue(any("Context:" in str(e) for e in events.errors))

    def test_save_uses_saver(self):
        """Test that save method uses the saver properly."""
        target = Target(target="mobi", category="ebook", options={})
        config = JobConfig(target, "/path/to/file.fb2", path_to_save="/output")
        self.converter.set_config(config)

        source_data = io.BytesIO(b"test data")
        result = self.converter.save("result.mobi", source_data)

        self.assertIn("result.mobi", str(result))
        self.assertEqual(self.saver.source_name, "result.mobi")

    def test_full_conversion_flow(self):
        """Test complete conversion flow with all components."""
        # Use actual test file
        path_to_file = os.path.abspath(__file__)
        target = Target(target="mobi", category="ebook", options={})
        config = JobConfig(target, path_to_file, path_to_save="/output")

        # Mock the internal methods to avoid actual processing
        with (
            patch.object(self.converter.processor, "send_job", return_value="job123"),
            patch.object(self.converter.processor, "get_job_status", return_value=["Processing"]),
            patch.object(
                self.converter.processor,
                "get_job_result",
                return_value=("result.mobi", io.BytesIO(b"data")),
            ),
        ):
            self.converter.convert(config)

        # Verify flow completed via event emissions
        self.assertTrue(any("completed" in str(s) for s in self.events.statuses))


if __name__ == "__main__":
    unittest.main()
