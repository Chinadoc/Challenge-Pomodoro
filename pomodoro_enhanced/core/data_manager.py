import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, TypeVar, Type
from datetime import datetime
import logging
from .models import Task, PomodoroSession, TimerSettings

T = TypeVar('T')

class DataManager:
    """Handles all data persistence for the application."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the data manager with optional custom data directory."""
        self.logger = logging.getLogger(__name__)
        
        # Set up data directory
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to user's home directory
            self.data_dir = Path.home() / '.pomodoro_enhanced'
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.tasks_file = self.data_dir / 'tasks.json'
        self.sessions_file = self.data_dir / 'sessions.json'
        self.settings_file = self.data_dir / 'settings.json'
        self.backup_dir = self.data_dir / 'backups'
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize data
        self.tasks: List[Task] = []
        self.sessions: List[PomodoroSession] = []
        self.settings = TimerSettings()
        
        # Load data
        self.load_all_data()
    
    def _load_json_file(self, file_path: Path, default: Any = None):
        """Load JSON data from a file, returning default if file doesn't exist."""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {e}")
            return default
    
    def _save_json_file(self, file_path: Path, data: Any) -> bool:
        """Save data to a JSON file with error handling."""
        try:
            # Create backup if file exists
            if file_path.exists():
                backup_file = self.backup_dir / f"{file_path.stem}_{int(datetime.now().timestamp())}{file_path.suffix}"
                file_path.rename(backup_file)
                
            # Save new data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=self._json_serializer)
            return True
        except Exception as e:
            self.logger.error(f"Error saving {file_path}: {e}")
            return False
    
    @staticmethod
    def _json_serializer(obj):
        """JSON serializer for objects not serializable by default json code"""
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def load_all_data(self) -> None:
        """Load all data from disk."""
        # Load tasks
        tasks_data = self._load_json_file(self.tasks_file, [])
        self.tasks = [Task.from_dict(task_data) for task_data in tasks_data]
        
        # Load sessions
        sessions_data = self._load_json_file(self.sessions_file, [])
        self.sessions = [PomodoroSession.from_dict(session_data) for session_data in sessions_data]
        
        # Load settings
        settings_data = self._load_json_file(self.settings_file, {})
        self.settings = TimerSettings.from_dict(settings_data)
    
    def save_all_data(self) -> bool:
        """Save all data to disk."""
        success = True
        
        # Save tasks
        tasks_data = [task.to_dict() for task in self.tasks]
        if not self._save_json_file(self.tasks_file, tasks_data):
            success = False
        
        # Save sessions
        sessions_data = [session.to_dict() for session in self.sessions]
        if not self._save_json_file(self.sessions_file, sessions_data):
            success = False
        
        # Save settings
        settings_data = self.settings.to_dict()
        if not self._save_json_file(self.settings_file, settings_data):
            success = False
        
        return success
    
    # Task management
    def add_task(self, task: Task) -> str:
        """Add a new task."""
        self.tasks.append(task)
        self.save_all_data()
        return task.id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def update_task(self, task: Task) -> bool:
        """Update an existing task."""
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                self.save_all_data()
                return True
        return False
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[i]
                self.save_all_data()
                return True
        return False
    
    def get_tasks(self, **filters) -> List[Task]:
        """Get tasks with optional filtering."""
        tasks = self.tasks
        
        for key, value in filters.items():
            if key == 'status':
                tasks = [t for t in tasks if t.status == value]
            elif key == 'category':
                tasks = [t for t in tasks if t.category == value]
            elif key == 'priority':
                tasks = [t for t in tasks if t.priority == value]
        
        return tasks
    
    # Session management
    def add_session(self, session: PomodoroSession) -> str:
        """Add a new session."""
        self.sessions.append(session)
        self.save_all_data()
        return session.id
    
    def get_sessions(self, **filters) -> List[PomodoroSession]:
        """Get sessions with optional filtering."""
        sessions = self.sessions
        
        for key, value in filters.items():
            if key == 'task_id':
                sessions = [s for s in sessions if s.task_id == value]
            elif key == 'mode':
                sessions = [s for s in sessions if s.mode == value]
            elif key == 'date':
                sessions = [s for s in sessions if s.start_time.date() == value]
        
        return sessions
    
    # Settings management
    def update_settings(self, settings: TimerSettings) -> bool:
        """Update application settings."""
        self.settings = settings
        return self.save_all_data()
    
    def get_settings(self) -> TimerSettings:
        """Get current settings."""
        return self.settings
    
    # Backup and restore
    def create_backup(self, backup_dir: str = None) -> str:
        """Create a backup of all data."""
        backup_dir = Path(backup_dir) if backup_dir else self.backup_dir
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"pomodoro_backup_{timestamp}.json"
        
        backup_data = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'tasks': [task.to_dict() for task in self.tasks],
            'sessions': [session.to_dict() for session in self.sessions],
            'settings': self.settings.to_dict()
        }
        
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False, default=self._json_serializer)
            return str(backup_file)
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise
    
    def restore_backup(self, backup_file: str) -> bool:
        """Restore data from a backup file."""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Restore tasks
            self.tasks = [Task.from_dict(task_data) for task_data in backup_data.get('tasks', [])]
            
            # Restore sessions
            self.sessions = [PomodoroSession.from_dict(session_data) 
                           for session_data in backup_data.get('sessions', [])]
            
            # Restore settings
            if 'settings' in backup_data:
                self.settings = TimerSettings.from_dict(backup_data['settings'])
            
            # Save the restored data
            return self.save_all_data()
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False
