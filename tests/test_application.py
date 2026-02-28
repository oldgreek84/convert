"""Unit tests for AppPresenter class."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, call

from src.application import AppPresenter, Application
from src.config import JobConfig, Target
from src.converter import Converter
from tests.common import DummyJobProcessor, DummySaver


def _make_format(name: str) -> Mock:
    """Create a mock Format object for testing."""
    fmt = Mock()
    fmt.name = name
    return fmt


class TestAppPresenter(unittest.TestCase):
    """Test cases for AppPresenter."""

    def setUp(self):
        self.processor = DummyJobProcessor()
        self.saver = DummySaver()
        self.converter = Converter(processor=self.processor, saver=self.saver)
        self.view = Mock()
        self.view.get_config.return_value = JobConfig(
            fmt_from=_make_format("fb2"),
            fmt_to=_make_format("mobi"),
            target=Target(target="mobi", category="ebook", options={}),
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
        # Emit events and check that view methods are called
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

    def test_handle_convert_gets_config_and_calls_converter(self):
        """Simulate the view triggering conversion."""
        # Get the callback that was registered with set_on_convert
        callback = self.view.set_on_convert.call_args[0][0]

        with unittest.mock.patch.object(self.converter, "convert") as mock_convert:
            callback()
            mock_convert.assert_called_once_with(self.view.get_config())

    def test_backward_compatibility_alias(self):
        self.assertIs(Application, AppPresenter)


if __name__ == "__main__":
    unittest.main()
