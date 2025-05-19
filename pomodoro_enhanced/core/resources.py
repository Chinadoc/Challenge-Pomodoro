""
Resource management for the Enhanced Pomodoro Timer.
Handles loading and accessing application resources like icons and sounds.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, Tuple

# Initialize logger
logger = logging.getLogger(__name__)

class ResourceManager:
    """Manages application resources like icons, sounds, and other assets."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._resources: Dict[str, Any] = {}
            self._resource_dirs: Dict[str, Path] = {}
            self._initialized = True
            self._setup_resource_paths()
    
    def _setup_resource_paths(self) -> None:
        """Set up resource paths based on the application's installation location."""
        # Determine if we're running in a bundle (PyInstaller) or from source
        if getattr(sys, 'frozen', False):
            # Running in a bundle (PyInstaller)
            base_path = Path(sys._MEIPASS)  # type: ignore
            self._resource_dirs['base'] = base_path
            self._resource_dirs['assets'] = base_path / 'assets'
            self._resource_dirs['icons'] = base_path / 'assets' / 'icons'
            self._resource_dirs['sounds'] = base_path / 'assets' / 'sounds'
            self._resource_dirs['themes'] = base_path / 'assets' / 'themes'
        else:
            # Running from source
            base_path = Path(__file__).parent.parent
            self._resource_dirs['base'] = base_path.parent
            self._resource_dirs['assets'] = base_path.parent / 'assets'
            self._resource_dirs['icons'] = base_path.parent / 'assets' / 'icons'
            self._resource_dirs['sounds'] = base_path.parent / 'assets' / 'sounds'
            self._resource_dirs['themes'] = base_path.parent / 'assets' / 'themes'
        
        # Create necessary directories if they don't exist
        for name, path in self._resource_dirs.items():
            if name != 'base':  # Don't create base directory
                path.mkdir(parents=True, exist_ok=True)
    
    def get_path(self, resource_type: str, *path_parts: str) -> Path:
        """Get the path to a resource.
        
        Args:
            resource_type: Type of resource ('icons', 'sounds', 'themes', etc.)
            *path_parts: Additional path components
            
        Returns:
            Path to the requested resource
        """
        if resource_type not in self._resource_dirs:
            raise ValueError(f"Unknown resource type: {resource_type}")
        
        return self._resource_dirs[resource_type].joinpath(*path_parts)
    
    def get_icon_path(self, icon_name: str) -> Path:
        """Get the path to an icon file.
        
        Args:
            icon_name: Name of the icon file (without extension)
            
        Returns:
            Path to the icon file
        """
        # Try different icon formats
        for ext in ['.png', '.ico', '.svg']:
            icon_path = self.get_path('icons', f"{icon_name}{ext}")
            if icon_path.exists():
                return icon_path
        
        # Return default path if not found
        return self.get_path('icons', f"{icon_name}.png")
    
    def get_sound_path(self, sound_name: str) -> Path:
        """Get the path to a sound file.
        
        Args:
            sound_name: Name of the sound file (without extension)
            
        Returns:
            Path to the sound file
        """
        # Try different sound formats
        for ext in ['.wav', '.mp3', '.ogg']:
            sound_path = self.get_path('sounds', f"{sound_name}{ext}")
            if sound_path.exists():
                return sound_path
        
        # Return default path if not found
        return self.get_path('sounds', f"{sound_name}.wav")
    
    def get_theme_path(self, theme_name: str) -> Path:
        """Get the path to a theme file.
        
        Args:
            theme_name: Name of the theme file (without extension)
            
        Returns:
            Path to the theme file
        """
        return self.get_path('themes', f"{theme_name}.json")
    
    def ensure_resource(self, resource_type: str, resource_name: str) -> bool:
        """Ensure a resource exists, and if not, create a default version.
        
        Args:
            resource_type: Type of resource ('icons', 'sounds', 'themes')
            resource_name: Name of the resource file (with extension)
            
        Returns:
            bool: True if the resource exists or was created, False otherwise
        """
        resource_path = self.get_path(resource_type, resource_name)
        
        if resource_path.exists():
            return True
        
        # Create default resource if it doesn't exist
        try:
            if resource_type == 'themes':
                self._create_default_theme(resource_path)
            elif resource_type == 'sounds':
                self._create_default_sound(resource_path)
            elif resource_type == 'icons':
                self._create_default_icon(resource_path)
            else:
                return False
                
            return True
        except Exception as e:
            logger.error(f"Failed to create default {resource_type} '{resource_name}': {e}")
            return False
    
    def _create_default_theme(self, theme_path: Path) -> None:
        """Create a default theme file."""
        default_theme = {
            "name": "Default",
            "author": "Enhanced Pomodoro Timer",
            "version": "1.0",
            "colors": {
                "primary": "#2b2b2b",
                "secondary": "#3b3b3b",
                "accent": "#4CAF50",
                "text": "#ffffff",
                "text_secondary": "#b0b0b0",
                "background": "#1e1e1e",
                "surface": "#2b2b2b",
                "error": "#f44336",
                "warning": "#ff9800",
                "success": "#4caf50",
                "info": "#2196f3"
            },
            "sizes": {
                "border_radius": 6,
                "padding": 10,
                "spacing": 8
            },
            "fonts": {
                "family": "Segoe UI, Arial, sans-serif",
                "size_small": 10,
                "size_medium": 12,
                "size_large": 14,
                "size_title": 18
            }
        }
        
        with open(theme_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(default_theme, f, indent=2)
    
    def _create_default_sound(self, sound_path: Path) -> None:
        """Create a default sound file (silent)."""
        # For now, we'll just create an empty file
        # In a real app, you might want to include a default sound
        sound_path.touch()
    
    def _create_default_icon(self, icon_path: Path) -> None:
        """Create a default icon (blank)."""
        # For now, we'll just create an empty file
        # In a real app, you might want to include a default icon
        icon_path.touch()

# Global resource manager instance
resource_manager = ResourceManager()

def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance."""
    return resource_manager
