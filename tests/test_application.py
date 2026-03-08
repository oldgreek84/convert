"""Unit tests for AppPresenter class."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from src.application import AppPresenter, Application
from src.config import ViewSelections
from src.conversion_service import ConversionService
from src.converter import Converter
from src.validator import Validator
from tests.common import DummyJobProcessor, DummySaver


class TestAppPresenter(unittest.TestCase):
    """Test cases for AppPresenter."""

    def setUp(self):
        self.processor = DummyJobProcessor()
        self.saver = DummySaver()
        service = ConversionService(
            processor=self.processor,
            saver=self.saver,
            validator=Validator(),
        )
        self.converter = Converter(service=service)
        self.view = Mock()
        self.view.get_config.return_value = ViewSelections(
            source_format="fb2",
            target_format="mobi",
            path_to_file="/path/to/file.fb2",
        )
        self.presenter = AppPresenter(self.converter, self.view)

    def test_init_stores_converter_and_view(self):
        self.assertIs(self.presenter.converter, self.converter)
        self.assertIs(self.presenter.view, self.view)

    def test_init_registers_convert_callback_on_view(self):
        self.view.set_on_convert.assert_called_once()
        callback = self.view.set_on_convert.call_args[0][0]
        self.assertTrue(callable(callback))

    def test_init_subscribes_to_converter_events(self):
        """Verify that converter events are wired to view methods."""
        self.converter.events.emit("status", "processing")
        self.converter.events.emit("message", "hello")
        self.converter.events.emit("error", "oops")
        self.converter.events.emit("result", "/path/result.mobi")

        self.view.show_status.assert_called_with("processing")
        self.view.show_message.assert_called_with("hello")
        self.view.show_error.assert_called_with("oops")
        self.view.show_result.assert_called_with("/path/result.mobi")

    def test_run_delegates_to_view(self):
        self.presenter.run()
        self.view.run.assert_called_once()

    @patch("src.application.get_format_service")
    def test_handle_convert_builds_config_and_calls_converter(self, mock_get_fs):
        """Simulate the view triggering conversion."""
        mock_fs = mock_get_fs.return_value
        mock_fs.get_source_format.return_value = Mock(name="fb2")
        mock_fs.get_target_format.return_value = Mock(name="mobi")
        mock_fs.create_target_object.return_value = Mock()

        callback = self.view.set_on_convert.call_args[0][0]

        with patch.object(self.converter, "convert") as mock_convert:
            callback()
            mock_convert.assert_called_once()

        mock_fs.get_source_format.assert_called_with("fb2")
        mock_fs.get_target_format.assert_called_with("mobi")
        mock_fs.create_target_object.assert_called_with("mobi")

    @patch("src.application.get_format_service")
    def test_handle_convert_error_calls_error_handler(self, mock_get_fs):
        """Test that errors in get_config are routed to error_handler."""
        self.view.get_config.side_effect = ValueError("bad input")

        callback = self.view.set_on_convert.call_args[0][0]

        with patch.object(self.converter, "error_handler") as mock_handler:
            callback()
            mock_handler.assert_called_once()

    def test_backward_compatibility_alias(self):
        self.assertIs(Application, AppPresenter)


if __name__ == "__main__":
    unittest.main()
