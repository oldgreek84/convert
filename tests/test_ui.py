"""Unit tests for UI implementations.

Tests UI classes with mocked format service to ensure proper separation.
"""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from uis.cli_ui import ConverterInterfaceCLI
from formats.metadata import FormatMetadata
from config import Target
import exceptions


class TestConverterInterfaceCLI(unittest.TestCase):
    """Test cases for ConverterInterfaceCLI class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cli = ConverterInterfaceCLI()

    def test_init_creates_cli_instance(self):
        """Test that __init__ creates CLI interface."""
        # Arrange & Act (done in setUp)

        # Assert
        self.assertIsNotNone(self.cli)
        self.assertIsNone(self.cli.converter)

    def test_yes_no_returns_true_for_yes(self):
        """Test yes_no() returns True for 'y' input."""
        # Arrange
        from uis.cli_ui import yes_no

        # Act & Assert
        with patch("builtins.input", return_value="y"):
            self.assertTrue(yes_no())

        with patch("builtins.input", return_value="yes"):
            self.assertTrue(yes_no())

    def test_yes_no_returns_false_for_no(self):
        """Test yes_no() returns False for non-yes input."""
        # Arrange
        from uis.cli_ui import yes_no

        # Act & Assert
        with patch("builtins.input", return_value="n"):
            self.assertFalse(yes_no())

        with patch("builtins.input", return_value="no"):
            self.assertFalse(yes_no())

        with patch("builtins.input", return_value=""):
            self.assertFalse(yes_no())

    @patch("uis.cli_ui.format_service")
    @patch("builtins.input")
    @patch("sys.argv", ["test.py", "book.fb2"])
    def test_get_params_uses_format_service(self, mock_input, mock_format_service):
        """Test that _get_params uses format service to get formats."""
        # Arrange
        mock_source_format = Mock()
        mock_source_format.name = "fb2"

        mock_metadata = FormatMetadata("mobi", ".mobi", "MOBI", "Kindle format")

        mock_format_service.get_source_format.return_value = mock_source_format
        mock_format_service.list_available_targets.return_value = [mock_metadata]
        mock_format_service.get_target_format.return_value = Mock(name="mobi")
        mock_format_service.validate_conversion.return_value = True

        mock_target = Target(target="mobi", category="ebook", options={})
        mock_format_service.create_target_object.return_value = mock_target

        mock_input.return_value = "1"  # Choose first option

        with patch("utils.common_utils.parse_command", return_value={}):
            # Act
            result = self.cli._get_params(["test.py", "book.fb2"])

            # Assert
            target_object, file_path = result
            self.assertEqual(file_path, "book.fb2")
            self.assertIsInstance(target_object, Target)

            # Verify service was used
            mock_format_service.get_source_format.assert_called()
            mock_format_service.list_available_targets.assert_called()

    @patch("uis.cli_ui.format_service")
    @patch("sys.argv", ["test.py", "book.fb2"])
    def test_get_params_displays_available_formats(self, mock_format_service):
        """Test that _get_params displays available target formats."""
        # Arrange
        mock_source = Mock()
        mock_source.name = "fb2"

        metadata1 = FormatMetadata("mobi", ".mobi", "MOBI", "Kindle format")
        metadata2 = FormatMetadata("pdf", ".pdf", "PDF", "PDF format")

        mock_format_service.get_source_format.return_value = mock_source
        mock_format_service.list_available_targets.return_value = [metadata1, metadata2]
        mock_format_service.get_target_format.return_value = Mock(name="mobi")

        mock_target = Target(target="mobi", category="ebook", options={})
        mock_format_service.create_target_object.return_value = mock_target

        with patch("builtins.input", return_value="1"):
            with patch("utils.common_utils.parse_command", return_value={}):
                with patch.object(self.cli, "display_common_info") as mock_display:
                    # Act
                    self.cli._get_params(["test.py", "book.fb2"])

                    # Assert - Should display available formats
                    calls = [str(call) for call in mock_display.call_args_list]
                    self.assertTrue(
                        any("Available conversion formats" in str(call) for call in calls)
                    )

    @patch("uis.cli_ui.format_service")
    @patch("sys.argv", ["test.py", "book.unknown"])
    def test_get_params_handles_format_error(self, mock_format_service):
        """Test that _get_params handles FormatError from service."""
        # Arrange
        mock_format_service.get_source_format.side_effect = exceptions.FormatError(
            "Unsupported format"
        )

        with patch("utils.common_utils.parse_command", return_value={}):
            # Act & Assert
            with self.assertRaises(exceptions.FormatError):
                self.cli._get_params(["test.py", "book.unknown"])

    @patch("uis.cli_ui.format_service")
    @patch("builtins.input")
    @patch("sys.argv", ["test.py", "book.fb2"])
    def test_get_params_validates_user_choice(self, mock_input, mock_format_service):
        """Test that _get_params validates user input and re-prompts on invalid choice."""
        # Arrange
        mock_source = Mock()
        mock_source.name = "fb2"

        metadata = FormatMetadata("mobi", ".mobi", "MOBI", "Kindle format")

        mock_format_service.get_source_format.return_value = mock_source
        mock_format_service.list_available_targets.return_value = [metadata]
        mock_format_service.get_target_format.return_value = Mock(name="mobi")

        mock_target = Target(target="mobi", category="ebook", options={})
        mock_format_service.create_target_object.return_value = mock_target

        # First input invalid, second valid
        mock_input.side_effect = ["99", "1"]

        with patch("utils.common_utils.parse_command", return_value={}):
            with patch.object(self.cli, "display_common_info") as mock_display:
                # Act
                self.cli._get_params(["test.py", "book.fb2"])

                # Assert - Should show invalid choice message
                calls = [str(call) for call in mock_display.call_args_list]
                self.assertTrue(any("Invalid choice" in str(call) for call in calls))

    def test_display_common_info_prints_message(self):
        """Test that display_common_info outputs message."""
        # Arrange
        test_message = "Test message"

        with patch.object(self.cli, "_print") as mock_print:
            # Act
            self.cli.display_common_info(test_message)

            # Assert
            mock_print.assert_called_once()
            args = mock_print.call_args[0][0]
            self.assertIn(test_message, args)

    def test_display_job_status_prints_status(self):
        """Test that display_job_status outputs status."""
        # Arrange
        from config import ConverterStatus

        with patch.object(self.cli, "_print") as mock_print:
            # Act
            self.cli.display_job_status(ConverterStatus.COMPLETED)

            # Assert
            mock_print.assert_called_once()
            args = mock_print.call_args[0][0]
            # Status is lowercase in output
            self.assertIn("completed", args.lower())


if __name__ == "__main__":
    unittest.main()
