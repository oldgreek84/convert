"""Unit tests for FormatService.

Tests the service layer implementation for format business logic.
Uses mocking to isolate service from repository.
"""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from src import exceptions
from formats.metadata import FormatMetadata
from formats.repository import FormatRepository, FormatRepositoryError
from formats.service import FormatService, create_format_service, get_format_service
from interfaces.format_instance import Format
from src import config


class MockFormat(Format):
    """Mock format for testing."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name)
        self._extension = ".mock"
        self.category = "test"
        self.kwargs = kwargs

    def get_allowed_formats(self) -> list[str]:
        return ["pdf", "txt"]

    def get_options(self) -> dict:
        return self.kwargs


class TestFormatService(unittest.TestCase):
    """Test cases for FormatService class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Arrange - Create mock repository and service
        self.mock_repository = Mock(spec=FormatRepository)
        self.service = FormatService(self.mock_repository)

    def test_init_stores_repository(self):
        """Test that __init__ stores repository reference."""
        # Arrange & Act (done in setUp)

        # Assert
        self.assertEqual(self.service._repository, self.mock_repository)

    def test_get_source_format_returns_instance_when_format_exists(self):
        """Test that get_source_format() returns format instance for valid format."""
        # Arrange
        mock_instance = MockFormat("fb2")
        self.mock_repository.exists.return_value = True
        self.mock_repository.create_instance.return_value = mock_instance

        # Act
        result = self.service.get_source_format("fb2")

        # Assert
        self.assertEqual(result, mock_instance)
        self.mock_repository.exists.assert_called_once_with("fb2")
        self.mock_repository.create_instance.assert_called_once_with("fb2")

    def test_get_source_format_raises_error_when_format_not_exists(self):
        """Test that get_source_format() raises FormatError for missing format."""
        # Arrange
        self.mock_repository.exists.return_value = False

        # Act & Assert
        with self.assertRaises(exceptions.FormatError) as context:
            self.service.get_source_format("nonexistent")

        self.assertIn("does not exist", str(context.exception))
        self.mock_repository.exists.assert_called_once_with("nonexistent")

    def test_get_target_format_returns_instance_with_options(self):
        """Test that get_target_format() creates instance with options."""
        # Arrange
        mock_instance = MockFormat("pdf", dpi=300, quality=95)
        self.mock_repository.create_instance.return_value = mock_instance

        # Act
        result = self.service.get_target_format("pdf", dpi=300, quality=95)

        # Assert
        self.assertEqual(result, mock_instance)
        self.mock_repository.create_instance.assert_called_once_with("pdf", dpi=300, quality=95)

    def test_get_target_format_raises_error_when_repository_fails(self):
        """Test that get_target_format() converts repository error to FormatError."""
        # Arrange
        self.mock_repository.create_instance.side_effect = FormatRepositoryError("Format not found")

        # Act & Assert
        with self.assertRaises(exceptions.FormatError) as context:
            self.service.get_target_format("invalid")

        self.assertIn("Format not found", str(context.exception))

    def test_validate_conversion_succeeds_for_valid_conversion(self):
        """Test that validate_conversion() returns True for allowed conversion."""
        # Arrange
        mock_target = MockFormat("mobi")
        mock_target.get_allowed_formats = Mock(return_value=["fb2", "txt", "pdf"])

        self.mock_repository.exists.return_value = True
        self.mock_repository.create_instance.return_value = mock_target

        # Act
        result = self.service.validate_conversion("fb2", "mobi")

        # Assert
        self.assertTrue(result)
        self.assertEqual(self.mock_repository.exists.call_count, 2)
        self.mock_repository.exists.assert_any_call("fb2")
        self.mock_repository.exists.assert_any_call("mobi")

    def test_validate_conversion_raises_error_for_missing_source(self):
        """Test that validate_conversion() raises error when source format missing."""
        # Arrange
        self.mock_repository.exists.side_effect = lambda name: name == "mobi"

        # Act & Assert
        with self.assertRaises(exceptions.FormatError) as context:
            self.service.validate_conversion("nonexistent", "mobi")

        self.assertIn("nonexistent", str(context.exception))
        self.assertIn("does not exist", str(context.exception))

    def test_validate_conversion_raises_error_for_missing_target(self):
        """Test that validate_conversion() raises error when target format missing."""
        # Arrange
        self.mock_repository.exists.side_effect = lambda name: name == "fb2"

        # Act & Assert
        with self.assertRaises(exceptions.FormatError) as context:
            self.service.validate_conversion("fb2", "nonexistent")

        self.assertIn("nonexistent", str(context.exception))
        self.assertIn("does not exist", str(context.exception))

    def test_validate_conversion_raises_error_for_disallowed_conversion(self):
        """Test that validate_conversion() raises error for disallowed conversion."""
        # Arrange
        mock_target = MockFormat("pdf")
        mock_target.get_allowed_formats = Mock(return_value=["mobi", "epub"])

        self.mock_repository.exists.return_value = True
        self.mock_repository.create_instance.return_value = mock_target

        # Act & Assert
        with self.assertRaises(exceptions.FormatError) as context:
            self.service.validate_conversion("fb2", "pdf")

        self.assertIn("fb2", str(context.exception))
        self.assertIn("pdf", str(context.exception))
        self.assertIn("not allowed", str(context.exception))

    def test_create_target_object_returns_target_config(self):
        """Test that create_target_object() returns Target object with correct values."""
        # Arrange
        mock_instance = MockFormat("mobi", quality=90)
        mock_instance.category = "ebook"
        mock_instance.get_options = Mock(return_value={"quality": 90})

        self.mock_repository.create_instance.return_value = mock_instance

        # Act
        result = self.service.create_target_object("mobi", quality=90)

        # Assert
        self.assertIsInstance(result, config.Target)
        self.assertEqual(result.target, "mobi")
        self.assertEqual(result.category, "ebook")
        self.assertEqual(result.options, {"quality": 90})
        self.mock_repository.create_instance.assert_called_once_with("mobi", quality=90)

    def test_create_target_object_raises_error_when_repository_fails(self):
        """Test that create_target_object() converts repository error."""
        # Arrange
        self.mock_repository.create_instance.side_effect = FormatRepositoryError("Invalid format")

        # Act & Assert
        with self.assertRaises(exceptions.FormatError) as context:
            self.service.create_target_object("invalid")

        self.assertIn("Invalid format", str(context.exception))

    def test_list_available_targets_returns_metadata_list(self):
        """Test that list_available_targets() returns list of FormatMetadata."""
        # Arrange
        mock_source = MockFormat("fb2")
        mock_source.get_allowed_formats = Mock(return_value=["mobi", "pdf", "txt"])

        metadata_mobi = FormatMetadata("mobi", ".mobi", "MOBI", "Kindle format")
        metadata_pdf = FormatMetadata("pdf", ".pdf", "PDF", "PDF format")
        metadata_txt = FormatMetadata("txt", ".txt", "TXT", "Text format")

        self.mock_repository.get_metadata.side_effect = [
            metadata_mobi,
            metadata_pdf,
            metadata_txt,
        ]

        # Act
        result = self.service.list_available_targets(mock_source)

        # Assert
        self.assertEqual(len(result), 3)
        self.assertIn(metadata_mobi, result)
        self.assertIn(metadata_pdf, result)
        self.assertIn(metadata_txt, result)
        self.assertEqual(self.mock_repository.get_metadata.call_count, 3)

    def test_list_available_targets_includes_all_valid_metadata(self):
        """Test that list_available_targets() includes all formats with metadata."""
        # Arrange
        mock_source = MockFormat("fb2")
        mock_source.get_allowed_formats = Mock(return_value=["mobi", "pdf", "txt"])

        metadata_mobi = FormatMetadata("mobi", ".mobi", "MOBI", "Kindle format")
        metadata_pdf = FormatMetadata("pdf", ".pdf", "PDF", "PDF format")
        metadata_txt = FormatMetadata("txt", ".txt", "TXT", "Text format")

        def get_metadata_side_effect(name):
            if name == "mobi":
                return metadata_mobi
            if name == "pdf":
                return metadata_pdf
            if name == "txt":
                return metadata_txt

            raise FormatRepositoryError(f"Metadata for {name} not found")

        self.mock_repository.get_metadata.side_effect = get_metadata_side_effect

        # Act
        result = self.service.list_available_targets(mock_source)

        # Assert
        self.assertEqual(len(result), 3)
        self.assertIn(metadata_mobi, result)
        self.assertIn(metadata_pdf, result)
        self.assertIn(metadata_txt, result)

    def test_list_available_targets_returns_empty_for_no_allowed_formats(self):
        """Test that list_available_targets() returns empty list when no formats allowed."""
        # Arrange
        mock_source = MockFormat("isolated")
        mock_source.get_allowed_formats = Mock(return_value=[])

        # Act
        result = self.service.list_available_targets(mock_source)

        # Assert
        self.assertEqual(result, [])
        self.mock_repository.get_metadata.assert_not_called()

    def test_list_available_targets_filters_unregistered_formats(self):
        """Test that list_available_targets() filters out unregistered formats."""
        # Arrange
        mock_source = MockFormat("fb2")
        mock_source.get_allowed_formats = Mock(return_value=["mobi", "unregistered", "pdf"])

        metadata_mobi = FormatMetadata("mobi", ".mobi", "MOBI", "Kindle format")
        metadata_pdf = FormatMetadata("pdf", ".pdf", "PDF", "PDF format")

        def get_metadata_side_effect(name):
            if name == "mobi":
                return metadata_mobi
            if name == "pdf":
                return metadata_pdf
            raise FormatRepositoryError(f"Metadata for {name} not found")

        self.mock_repository.get_metadata.side_effect = get_metadata_side_effect

        # Act
        result = self.service.list_available_targets(mock_source)

        # Assert - Should only include registered formats
        self.assertEqual(len(result), 2)
        self.assertIn(metadata_mobi, result)
        self.assertIn(metadata_pdf, result)

    def test_list_available_targets_logs_warning_for_unregistered_formats(self):
        """Test that list_available_targets() logs warning for unregistered formats."""
        # Arrange
        mock_source = MockFormat("fb2")
        mock_source.get_allowed_formats = Mock(return_value=["mobi", "unregistered"])

        metadata_mobi = FormatMetadata("mobi", ".mobi", "MOBI", "Kindle format")

        def get_metadata_side_effect(name):
            if name == "mobi":
                return metadata_mobi

            raise FormatRepositoryError(f"Metadata for {name} not found")

        self.mock_repository.get_metadata.side_effect = get_metadata_side_effect

        # Act & Assert
        with self.assertLogs("formats.service", level="WARNING") as log_context:
            result = self.service.list_available_targets(mock_source)

        # Should log warning about unregistered format
        self.assertTrue(any("unregistered" in message for message in log_context.output))
        self.assertEqual(len(result), 1)


class TestFormatServiceIntegration(unittest.TestCase):
    """Integration tests with real repository (not mocked)."""

    def setUp(self):
        """Set up test fixtures with real repository."""
        self.repository = FormatRepository()
        self.service = FormatService(self.repository)

        # Register mock format
        self.repository.register("mock", MockFormat, "Mock Format", "Test format")

    def test_full_workflow_get_source_and_validate(self):
        """Test complete workflow: get source, validate conversion."""
        # Arrange - format already registered in setUp

        # Act - Get source format
        source = self.service.get_source_format("mock")

        # Assert
        self.assertIsInstance(source, MockFormat)
        self.assertEqual(source.name, "mock")

    def test_full_workflow_create_target_object(self):
        """Test creating target object with real repository."""
        # Arrange - format already registered

        # Act
        target = self.service.create_target_object("mock", option1="value")

        # Assert
        self.assertIsInstance(target, config.Target)
        self.assertEqual(target.target, "mock")
        self.assertEqual(target.options, {"option1": "value"})


class TestDependencyInjection(unittest.TestCase):
    """Test dependency injection patterns."""

    def test_service_accepts_any_repository_protocol_implementation(self):
        """Test that FormatService works with any protocol implementation."""

        # Arrange - Create a simple custom repository (duck typing)
        class CustomRepository:
            def exists(self, name: str) -> bool:
                return name == "custom"

            def create_instance(self, name: str, **kwargs):
                return MockFormat(name, **kwargs)

            def get_metadata(self, name: str):
                return FormatMetadata("custom", ".custom", "Custom", "Custom format")

            def get_all(self):
                return []

            def get_class(self, name: str):
                return MockFormat

            def register(self, *args, **kwargs):
                pass

        custom_repo = CustomRepository()

        # Act - Should work with any repository that implements the protocol
        service = FormatService(custom_repo)

        # Assert
        self.assertTrue(service._repository.exists("custom"))
        self.assertFalse(service._repository.exists("other"))

    def test_create_format_service_factory_with_default_repository(self):
        """Test create_format_service() uses global registry by default."""

        # Act
        service = create_format_service()

        # Assert - Service should be created with global registry
        self.assertIsInstance(service, FormatService)
        self.assertIsNotNone(service._repository)

    def test_create_format_service_factory_with_custom_repository(self):
        """Test create_format_service() accepts custom repository."""
        from formats.service import create_format_service

        # Arrange
        custom_repo = FormatRepository()
        custom_repo.register("test", MockFormat, "Test", "Test format")

        # Act
        service = create_format_service(custom_repo)

        # Assert
        self.assertEqual(service._repository, custom_repo)
        self.assertTrue(service._repository.exists("test"))

    def test_get_format_service_returns_singleton(self):
        """Test get_format_service() returns the same instance."""
        # Act
        service1 = get_format_service()
        service2 = get_format_service()

        # Assert - Should be the same instance
        self.assertIs(service1, service2)


if __name__ == "__main__":
    unittest.main()
