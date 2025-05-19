"""Utility functions for the Pomodoro application."""

import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Callable, Type
from datetime import datetime, timedelta

# Type variable for generic function return type
T = TypeVar('T')

def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path

def format_duration(seconds: int) -> str:
    """Format a duration in seconds as a human-readable string."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    return f"{minutes:02d}:{seconds:02d}"

def parse_time(time_str: str) -> Optional[datetime]:
    """Parse a time string in format HH:MM or HH:MM:SS to a datetime object."""
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 2:
            hours, minutes = parts
            seconds = 0
        elif len(parts) == 3:
            hours, minutes, seconds = parts
        else:
            return None
            
        if not (0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60):
            return None
            
        now = datetime.now()
        return now.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
    except (ValueError, AttributeError):
        return None

def get_app_data_dir(app_name: str = "pomodoro_enhanced") -> Path:
    """Get the application data directory for the current platform."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    
    return base / app_name

def singleton(cls: Type[T]) -> Callable[..., T]:
    """A decorator to make a class a singleton."""
    instances: Dict[Type[T], T] = {}
    
    def get_instance(*args: Any, **kwargs: Any) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """Set up logging configuration."""
    handlers = [logging.StreamHandler()]
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def humanize_seconds(seconds: int) -> str:
    """Convert seconds to a human-readable string."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0 or hours > 0:  # Show minutes even if 0 if we have hours
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if not parts:  # Only show seconds if less than a minute
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    return " ".join(parts[:2])  # Return at most two parts (e.g., "2 hours 30 minutes")
