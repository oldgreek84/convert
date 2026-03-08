from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from interfaces.format_instance import Format


class ConverterStatus(StrEnum):
    """Enumeration of possible conversion status states.

    This enum defines the different states a conversion operation can be in,
    providing a standardized way to track and communicate conversion progress.

    Values:
        READY: Converter is initialized and ready to start processing
        PROCESSING: Conversion is currently in progress
        FAILED: Conversion encountered an error and failed
        COMPLETED: Conversion finished successfully
    """

    READY = "ready"
    PROCESSING = "processing"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass(frozen=True)
class ViewSelections:
    """Raw user selections from the view layer.

    Contains only primitive types — no domain objects.
    The presenter translates this into a JobConfig.
    """

    source_format: str
    target_format: str
    path_to_file: str


@dataclass
class Target:
    """Defines the conversion target format and options."""

    target: str
    category: str
    options: dict = field(default_factory=dict)


@dataclass
class JobConfig:
    """Complete configuration for a conversion job.

    Bundles source/target formats, target options, and file paths
    into a single object passed through the conversion pipeline.
    """

    fmt_from: Format
    fmt_to: Format
    target: Target
    path_to_file: str
    path_to_save: str = "books"

    @property
    def job_target(self):
        """Get the target format from the target configuration."""
        return self.target.target

    @property
    def job_category(self):
        """Get the category from the target configuration."""
        return self.target.category

    @property
    def job_options(self):
        """Get the conversion options from the target configuration."""
        return self.target.options

    def get_config(self) -> dict:
        """Generate a processor-compatible configuration dictionary.

        Returns:
            Dictionary containing category, target, and options for processors.
        """
        return {
            "category": self.job_category,
            "target": self.job_target,
            "options": self.job_options,
        }
