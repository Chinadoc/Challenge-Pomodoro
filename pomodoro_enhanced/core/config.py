"""
Configuration management for the Enhanced Pomodoro Timer.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv

# Initialize logger
logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the application."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._config: Dict[str, Any] = {}
            self._config_file: Optional[Path] = None
            self._initialized = True
            self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from environment and config file."""
        # Load environment variables from .env file if it exists
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        
        # Set default configuration
        self._config = {
            # Application
            'app_name': os.getenv('APP_NAME', 'Enhanced Pomodoro Timer'),
            'app_version': os.getenv('APP_VERSION', '0.1.0'),
            'debug': os.getenv('DEBUG', 'False').lower() == 'true',
            
            # Theme
            'theme': os.getenv('THEME', 'system').lower(),  # light, dark, system
            'font_size': int(os.getenv('FONT_SIZE', '12')),
            
            # Timer
            'work_duration': int(os.getenv('WORK_DURATION', '25')),  # minutes
            'short_break_duration': int(os.getenv('SHORT_BREAK_DURATION', '5')),  # minutes
            'long_break_duration': int(os.getenv('LONG_BREAK_DURATION', '15')),  # minutes
            'long_break_interval': int(os.getenv('LONG_BREAK_INTERVAL', '4')),  # number of work sessions
            
            # Auto-start
            'auto_start_breaks': os.getenv('AUTO_START_BREAKS', 'False').lower() == 'true',
            'auto_start_pomodoros': os.getenv('AUTO_START_POMODOROS', 'False').lower() == 'true',
            
            # Notifications
            'notifications': os.getenv('NOTIFICATIONS', 'True').lower() == 'true',
            'sound_effects': os.getenv('SOUND_EFFECTS', 'True').lower() == 'true',
            'volume': float(os.getenv('VOLUME', '0.8')),  # 0.0 to 1.0
            
            # Data
            'data_dir': Path(os.path.expanduser(os.getenv('DATA_DIR', '~/.config/enhanced-pomodoro'))),
            'backup_enabled': os.getenv('BACKUP_ENABLED', 'True').lower() == 'true',
            'backup_count': int(os.getenv('BACKUP_COUNT', '5')),
            
            # Window
            'window_width': int(os.getenv('WINDOW_WIDTH', '800')),
            'window_height': int(os.getenv('WINDOW_HEIGHT', '600')),
            'window_x': int(os.getenv('WINDOW_X', '100')),
            'window_y': int(os.getenv('WINDOW_Y', '100')),
            'window_maximized': os.getenv('WINDOW_MAXIMIZED', 'False').lower() == 'true',
            
            # Analytics
            'anonymous_stats': os.getenv('ANONYMOUS_STATS', 'False').lower() == 'true',
            'crash_reporting': os.getenv('CRASH_REPORTING', 'True').lower() == 'true',
            
            # Updates
            'check_for_updates': os.getenv('CHECK_FOR_UPDATES', 'True').lower() == 'true',
            'beta_updates': os.getenv('BETA_UPDATES', 'False').lower() == 'true',
        }
        
        # Ensure data directory exists
        self._config['data_dir'].mkdir(parents=True, exist_ok=True)
        
        # Set config file path
        self._config_file = self._config['data_dir'] / 'config.json'
        
        # Load user config if it exists
        self._load_user_config()
    
    def _load_user_config(self) -> None:
        """Load user configuration from file."""
        if self._config_file and self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._config.update(user_config)
                logger.debug("Loaded user configuration from %s", self._config_file)
            except (json.JSONDecodeError, IOError) as e:
                logger.error("Failed to load user configuration: %s", e)
    
    def save(self) -> None:
        """Save current configuration to file."""
        if not self._config_file:
            return
            
        try:
            # Ensure data directory exists
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
            
            logger.debug("Configuration saved to %s", self._config_file)
        except IOError as e:
            logger.error("Failed to save configuration: %s", e)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any, save: bool = False) -> None:
        """Set a configuration value."""
        if key in self._config:
            self._config[key] = value
            if save:
                self.save()
        else:
            logger.warning("Unknown configuration key: %s", key)
    
    def update(self, config_dict: Dict[str, Any], save: bool = False) -> None:
        """Update multiple configuration values at once."""
        for key, value in config_dict.items():
            if key in self._config:
                self._config[key] = value
            else:
                logger.warning("Unknown configuration key: %s", key)
        
        if save:
            self.save()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        # Save current window position/size
        window_config = {
            'window_width': self._config['window_width'],
            'window_height': self._config['window_height'],
            'window_x': self._config['window_x'],
            'window_y': self._config['window_y'],
            'window_maximized': self._config['window_maximized'],
        }
        
        # Reload defaults
        self._load_config()
        
        # Restore window config
        self._config.update(window_config)
        self.save()
    
    def get_window_geometry(self) -> Dict[str, Union[int, bool]]:
        """Get window geometry configuration."""
        return {
            'width': self._config['window_width'],
            'height': self._config['window_height'],
            'x': self._config['window_x'],
            'y': self._config['window_y'],
            'maximized': self._config['window_maximized'],
        }
    
    def set_window_geometry(self, width: int, height: int, x: int, y: int, maximized: bool = False) -> None:
        """Update window geometry configuration."""
        self._config['window_width'] = width
        self._config['window_height'] = height
        self._config['window_x'] = x
        self._config['window_y'] = y
        self._config['window_maximized'] = maximized
        self.save()
    
    def get_timer_settings(self) -> Dict[str, int]:
        """Get timer-related settings."""
        return {
            'work_duration': self._config['work_duration'],
            'short_break_duration': self._config['short_break_duration'],
            'long_break_duration': self._config['long_break_duration'],
            'long_break_interval': self._config['long_break_interval'],
        }
    
    def get_theme_settings(self) -> Dict[str, Any]:
        """Get theme-related settings."""
        return {
            'theme': self._config['theme'],
            'font_size': self._config['font_size'],
        }
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings."""
        return {
            'notifications': self._config['notifications'],
            'sound_effects': self._config['sound_effects'],
            'volume': self._config['volume'],
        }

# Global configuration instance
config = Config()

def get_config() -> Config:
    """Get the global configuration instance."""
    return config
