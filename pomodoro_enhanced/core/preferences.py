"""
Preference management for the Pomodoro Timer application.
Handles loading and saving user preferences.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional


class PreferenceManager:
    """Manages user preferences for the application."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the preference manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.logger = logging.getLogger(f"{__name__}.PreferenceManager")
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self.preferences: Dict[str, Any] = {}
        
        # Load existing preferences
        self.load_preferences()

    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        return Path.home() / ".pomodoro_preferences.json"

    def load_preferences(self) -> None:
        """Load preferences from the configuration file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.preferences = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading preferences: {e}")
            self.preferences = {}

    def save_preferences(self) -> None:
        """Save current preferences to the configuration file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving preferences: {e}")

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a preference value.
        
        Args:
            key: Preference key
            default: Default value if key doesn't exist
            
        Returns:
            The preference value or default if not found
        """
        return self.preferences.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a preference value.
        
        Args:
            key: Preference key
            value: Value to set
        """
        self.preferences[key] = value
        self.save_preferences()

    def delete(self, key: str) -> None:
        """Delete a preference.
        
        Args:
            key: Preference key to delete
        """
        if key in self.preferences:
            del self.preferences[key]
            self.save_preferences()
