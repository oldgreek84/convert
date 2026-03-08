"""Unit tests for UI implementations.

Tests UI classes with mocked format service to ensure proper separation.
"""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from formats.metadata import FormatMetadata
from src import exceptions
from src.config import ConverterStatus, ViewSelections
from uis.cli_ui import CLIView


class TestCLIView(unittest.TestCase):
    """Test cases for CLIView class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cli = CLIView()

    def test_init_creates_cli_instance(self):
        """Test that __init__ creates CLI interface."""
        self.assertIsNotNone(self.cli)
        self.assertIsNone(self.cli._selections)
        self.assertIsNone(self.cli._on_convert)

    @patch("uis.cli_ui.get_format_service")
    @patch("builtins.input")
    @patch("sys.argv", ["test.py", "book.fb2"])
    def test_get_selections_uses_format_service(self, mock_input, mock_get_service):
        """Test that _get_selections uses format service to list targets."""
        mock_format_service = Mock()
        mock_get_service.return_value = mock_format_service

        mock_source_format = Mock()
        mock_source_format.name = "fb2"

        mock_metadata = FormatMetadata("mobi", ".mobi", "MOBI", "Kindle format")

        mock_format_service.get_source_format.return_value = mock_source_format
        mock_format_service.list_available_targets.return_value = [mock_metadata]

        mock_input.return_value = "1"

        with patch("utils.common_utils.parse_command", return_value={}):
            result = self.cli._get_selections(["test.py", "book.fb2"])

            self.assertIsInstance(result, ViewSelections)
            self.assertEqual(result.path_to_file, "book.fb2")
            self.assertEqual(result.source_format, "fb2")
            self.assertEqual(result.target_format, "mobi")

            mock_format_service.get_source_format.assert_called()
            mock_format_service.list_available_targets.assert_called()

    @patch("uis.cli_ui.get_format_service")
    @patch("sys.argv", ["test.py", "book.fb2"])
    def test_get_selections_displays_available_formats(self, mock_get_service):
        """Test that _get_selections displays available target formats."""
        mock_format_service = Mock()
        mock_get_service.return_value = mock_format_service

        mock_source = Mock()
        mock_source.name = "fb2"

        metadata1 = FormatMetadata("mobi", ".mobi", "MOBI", "Kindle format")
        metadata2 = FormatMetadata("pdf", ".pdf", "PDF", "PDF format")

        mock_format_service.get_source_format.return_value = mock_source
        mock_format_service.list_available_targets.return_value = [metadata1, metadata2]

        with (
            patch("builtins.input", return_value="1"),
            patch("utils.common_utils.parse_command", return_value={}),
            patch.object(self.cli, "show_message") as mock_show,
        ):
            self.cli._get_selections(["test.py", "book.fb2"])

            calls = [str(call) for call in mock_show.call_args_list]
            self.assertTrue(any("Available conversion formats" in str(call) for call in calls))

    @patch("uis.cli_ui.get_format_service")
    @patch("sys.argv", ["test.py", "book.unknown"])
    def test_get_selections_handles_format_error(self, mock_get_service):
        """Test that _get_selections handles FormatError from service."""
        mock_format_service = Mock()
        mock_get_service.return_value = mock_format_service

        mock_format_service.get_source_format.side_effect = exceptions.FormatError(
            "Unsupported format"
        )

        with (
            patch("utils.common_utils.parse_command", return_value={}),
            self.assertRaises(exceptions.FormatError),
        ):
            self.cli._get_selections(["test.py", "book.unknown"])

    @patch("uis.cli_ui.get_format_service")
    @patch("builtins.input")
    @patch("sys.argv", ["test.py", "book.fb2"])
    def test_get_selections_validates_user_choice(self, mock_input, mock_get_service):
        """Test that _get_selections validates user input and re-prompts on invalid choice."""
        mock_format_service = Mock()
        mock_get_service.return_value = mock_format_service

        mock_source = Mock()
        mock_source.name = "fb2"

        metadata = FormatMetadata("mobi", ".mobi", "MOBI", "Kindle format")

        mock_format_service.get_source_format.return_value = mock_source
        mock_format_service.list_available_targets.return_value = [metadata]

        # First input invalid, second valid
        mock_input.side_effect = ["99", "1"]

        with (
            patch("utils.common_utils.parse_command", return_value={}),
            patch.object(self.cli, "show_message") as mock_show,
        ):
            self.cli._get_selections(["test.py", "book.fb2"])

            calls = [str(call) for call in mock_show.call_args_list]
            self.assertTrue(any("Invalid choice" in str(call) for call in calls))

    def test_show_message_prints_message(self):
        """Test that show_message outputs message."""
        test_message = "Test message"

        with patch.object(self.cli, "_print") as mock_print:
            self.cli.show_message(test_message)

            mock_print.assert_called_once()
            args = mock_print.call_args[0][0]
            self.assertIn(test_message, args)

    def test_show_status_prints_status(self):
        """Test that show_status outputs status."""
        with patch.object(self.cli, "_print") as mock_print:
            self.cli.show_status(ConverterStatus.COMPLETED)

            mock_print.assert_called_once()
            args = mock_print.call_args[0][0]
            self.assertIn("completed", args.lower())


if __name__ == "__main__":
    unittest.main()
