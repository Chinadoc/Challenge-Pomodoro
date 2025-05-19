"""Persistence layer for application data."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Generic, Type
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and date objects."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

class JSONDecoder(json.JSONDecoder):
    """Custom JSON decoder that can handle datetime strings."""
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
    
    def object_hook(self, dct):
        for key, value in dct.items():
            if isinstance(value, str):
                try:
                    # Try to parse ISO format datetime
                    dct[key] = datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    pass
        return dct

class DataManager:
    """Manages saving and loading application data to/from disk."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize with optional data directory."""
        if data_dir is None:
            data_dir = Path.home() / ".pomodoro_enhanced"
        
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Default file paths
        self.settings_path = self.data_dir / "settings.json"
        self.tasks_path = self.data_dir / "tasks.json"
        self.stats_path = self.data_dir / "stats.json"
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from disk."""
        return self._load_json(self.settings_path, {})
    
    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Save settings to disk."""
        self._save_json(self.settings_path, settings)
    
    def load_tasks(self) -> Dict[str, Any]:
        """Load tasks from disk."""
        return self._load_json(self.tasks_path, {"tasks": [], "categories": ["Work", "Study", "Personal"]})
    
    def save_tasks(self, tasks_data: Dict[str, Any]) -> None:
        """Save tasks to disk."""
        self._save_json(self.tasks_path, tasks_data)
    
    def load_stats(self) -> Dict[str, Any]:
        """Load statistics from disk."""
        return self._load_json(self.stats_path, {
            "daily_stats": {},
            "weekly_stats": {},
            "all_time_stats": {
                "total_work_seconds": 0,
                "total_pomodoros": 0,
                "total_tasks_completed": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "last_session_date": None
            }
        })
    
    def save_stats(self, stats_data: Dict[str, Any]) -> None:
        """Save statistics to disk."""
        self._save_json(self.stats_path, stats_data)
    
    def _load_json(self, path: Path, default: Any = None) -> Any:
        """Load data from a JSON file."""
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f, cls=JSONDecoder)
            return default
        except Exception as e:
            logger.error("Error loading %s: %s", path, e, exc_info=True)
            return default
    
    def _save_json(self, path: Path, data: Any) -> None:
        """Save data to a JSON file."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, cls=JSONEncoder, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Error saving %s: %s", path, e, exc_info=True)
            raise
