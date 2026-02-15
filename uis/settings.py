"""Settings Manager for E-book Converter.

This module handles loading and saving user preferences to disk.
Settings are stored in a JSON file at ~/.config/ebook-converter/settings.json

Example:
    >>> from uis.settings import get_font_size, set_font_size
    >>> current = get_font_size()  # Returns "Medium" by default
    >>> set_font_size("Large")     # Saves preference to disk
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default settings
DEFAULT_SETTINGS: dict[str, Any] = {
    "font_size": "Medium",  # Small | Medium | Large | Extra Large
}

# Config directory following XDG Base Directory Specification
CONFIG_DIR_NAME = "ebook-converter"
CONFIG_FILE_NAME = "settings.json"


def get_settings_dir() -> Path:
    """Get the settings directory path.

    Returns:
        Path to ~/.config/ebook-converter/
    """
    config_home = Path.home() / ".config"
    return config_home / CONFIG_DIR_NAME


def get_settings_path() -> Path:
    """Get the full path to the settings file.

    Returns:
        Path to ~/.config/ebook-converter/settings.json
    """
    return get_settings_dir() / CONFIG_FILE_NAME


def load_settings() -> dict[str, Any]:
    """Load settings from disk.

    If the settings file doesn't exist, creates it with default values.
    If the file is corrupted or unreadable, returns defaults.

    Returns:
        Dictionary containing user settings
    """
    settings_path = get_settings_path()

    if not settings_path.exists():
        # Create default settings file
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with settings_path.open("r", encoding="utf-8") as f:
            settings = json.load(f)

        # Merge with defaults to handle missing keys
        merged = DEFAULT_SETTINGS.copy()
        merged.update(settings)
        return merged

    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load settings: {e}. Using defaults.")
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict[str, Any]) -> None:
    """Save settings to disk.

    Creates the config directory if it doesn't exist.

    Args:
        settings: Dictionary containing settings to save
    """
    settings_dir = get_settings_dir()
    settings_path = get_settings_path()

    try:
        # Create directory if needed
        settings_dir.mkdir(parents=True, exist_ok=True)

        # Write settings
        with settings_path.open("w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

    except OSError as e:
        logger.error(f"Failed to save settings: {e}")


def get_font_size() -> str:
    """Get the current font size preference.

    Returns:
        Font size name: "Small", "Medium", "Large", or "Extra Large"
    """
    settings = load_settings()
    return settings.get("font_size", DEFAULT_SETTINGS["font_size"])


def set_font_size(size: str) -> None:
    """Save font size preference.

    Args:
        size: Font size name ("Small", "Medium", "Large", or "Extra Large")
    """
    valid_sizes = ["Small", "Medium", "Large", "Extra Large"]
    if size not in valid_sizes:
        logger.warning(f"Invalid font size '{size}'. Using 'Medium'.")
        size = "Medium"

    settings = load_settings()
    settings["font_size"] = size
    save_settings(settings)
