"""Unit tests for FormatRepository.

Tests the repository pattern implementation for format storage and retrieval.
"""

from __future__ import annotations

import unittest

from formats.repository import FormatRepository, FormatRepositoryError
from formats.metadata import FormatMetadata
from interfaces.format_instance import Format


class MockFormat(Format):
    """Mock format class for testing."""

    def __init__(self, name: str, option1: str = "default"):
        super().__init__(name)
        self._extension = ".mock"
        self.option1 = option1

    def get_allowed_formats(self) -> list[str]:
        return ["pdf", "txt"]

    def get_options(self) -> dict:
        return {"option1": self.option1}


class AnotherMockFormat(Format):
    """Another mock format for testing multiple formats."""

    def __init__(self, name: str):
        super().__init__(name)
        self._extension = ".another"

    def get_allowed_formats(self) -> list[str]:
        return ["mock"]

    def get_options(self) -> dict:
        return {}


class TestFormatRepository(unittest.TestCase):
    """Test cases for FormatRepository class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Arrange - Create fresh repository for each test
        self.repository = FormatRepository()

    def test_init_creates_empty_repository(self):
        """Test that __init__ creates empty registry and metadata storage."""
        # Arrange & Act (done in setUp)

        # Assert
        self.assertEqual(len(self.repository._registry), 0)
        self.assertEqual(len(self.repository._metadata), 0)

    def test_register_stores_format_class(self):
        """Test that register() stores the format class."""
        # Arrange
        name = "mock"
        display_name = "Mock Format"
        description = "A mock format for testing"

        # Act
        self.repository.register(name, MockFormat, display_name, description)

        # Assert
        self.assertEqual(self.repository._registry[name], MockFormat)

    def test_register_creates_metadata(self):
        """Test that register() creates FormatMetadata with correct values."""
        # Arrange
        name = "mock"
        display_name = "Mock Format"
        description = "A mock format for testing"

        # Act
        self.repository.register(name, MockFormat, display_name, description)

        # Assert
        metadata = self.repository._metadata[name]
        self.assertIsInstance(metadata, FormatMetadata)
        self.assertEqual(metadata.name, name)
        self.assertEqual(metadata.display_name, display_name)
        self.assertEqual(metadata.description, description)
        self.assertEqual(metadata.extension, ".mock")

    def test_register_does_not_overwrite_existing(self):
        """Test that register() does not overwrite already registered format."""
        # Arrange
        self.repository.register("mock", MockFormat, "First", "First description")

        # Act
        self.repository.register("mock", AnotherMockFormat, "Second", "Second description")

        # Assert - Should still be the first registration
        self.assertEqual(self.repository._registry["mock"], MockFormat)
        metadata = self.repository._metadata["mock"]
        self.assertEqual(metadata.display_name, "First")

    def test_get_class_returns_registered_class(self):
        """Test that get_class() returns the correct format class."""
        # Arrange
        self.repository.register("mock", MockFormat, "Mock", "Description")

        # Act
        result = self.repository.get_class("mock")

        # Assert
        self.assertEqual(result, MockFormat)

    def test_get_class_raises_error_for_unregistered_format(self):
        """Test that get_class() raises FormatRepositoryError for missing format."""
        # Arrange - empty repository

        # Act & Assert
        with self.assertRaises(FormatRepositoryError) as context:
            self.repository.get_class("nonexistent")

        self.assertIn("nonexistent", str(context.exception))
        self.assertIn("not registered", str(context.exception))

    def test_create_instance_returns_format_instance(self):
        """Test that create_instance() returns an instance of the format."""
        # Arrange
        self.repository.register("mock", MockFormat, "Mock", "Description")

        # Act
        instance = self.repository.create_instance("mock")

        # Assert
        self.assertIsInstance(instance, MockFormat)
        self.assertEqual(instance.name, "mock")

    def test_create_instance_passes_kwargs(self):
        """Test that create_instance() passes keyword arguments to constructor."""
        # Arrange
        self.repository.register("mock", MockFormat, "Mock", "Description")

        # Act
        instance = self.repository.create_instance("mock", option1="custom_value")

        # Assert
        self.assertEqual(instance.option1, "custom_value")

    def test_create_instance_raises_error_for_unregistered_format(self):
        """Test that create_instance() raises error for missing format."""
        # Arrange - empty repository

        # Act & Assert
        with self.assertRaises(FormatRepositoryError):
            self.repository.create_instance("nonexistent")

    def test_get_metadata_returns_format_metadata(self):
        """Test that get_metadata() returns FormatMetadata object."""
        # Arrange
        self.repository.register("mock", MockFormat, "Mock Format", "Test description")

        # Act
        metadata = self.repository.get_metadata("mock")

        # Assert
        self.assertIsInstance(metadata, FormatMetadata)
        self.assertEqual(metadata.name, "mock")
        self.assertEqual(metadata.display_name, "Mock Format")

    def test_get_metadata_raises_error_for_unregistered_format(self):
        """Test that get_metadata() raises FormatRepositoryError for missing format."""
        # Arrange - empty repository

        # Act & Assert
        with self.assertRaises(FormatRepositoryError) as context:
            self.repository.get_metadata("nonexistent")

        self.assertIn("nonexistent", str(context.exception))

    def test_get_all_returns_all_metadata(self):
        """Test that get_all() returns list of all FormatMetadata objects."""
        # Arrange
        self.repository.register("mock", MockFormat, "Mock", "First")
        self.repository.register("another", AnotherMockFormat, "Another", "Second")

        # Act
        all_metadata = self.repository.get_all()

        # Assert
        self.assertEqual(len(all_metadata), 2)
        self.assertTrue(all(isinstance(m, FormatMetadata) for m in all_metadata))

        # Check that both formats are present
        names = [m.name for m in all_metadata]
        self.assertIn("mock", names)
        self.assertIn("another", names)

    def test_get_all_returns_empty_list_for_empty_repository(self):
        """Test that get_all() returns empty list when no formats registered."""
        # Arrange - empty repository

        # Act
        all_metadata = self.repository.get_all()

        # Assert
        self.assertEqual(all_metadata, [])

    def test_exists_returns_true_for_registered_format(self):
        """Test that exists() returns True for registered format."""
        # Arrange
        self.repository.register("mock", MockFormat, "Mock", "Description")

        # Act
        result = self.repository.exists("mock")

        # Assert
        self.assertTrue(result)

    def test_exists_returns_false_for_unregistered_format(self):
        """Test that exists() returns False for unregistered format."""
        # Arrange - empty repository

        # Act
        result = self.repository.exists("nonexistent")

        # Assert
        self.assertFalse(result)

    def test_multiple_instances_have_separate_storage(self):
        """Test that different repository instances don't share storage."""
        # Arrange
        repo1 = FormatRepository()
        repo2 = FormatRepository()

        # Act
        repo1.register("mock", MockFormat, "Mock", "Description")

        # Assert
        self.assertTrue(repo1.exists("mock"))
        self.assertFalse(repo2.exists("mock"))


if __name__ == "__main__":
    unittest.main()
