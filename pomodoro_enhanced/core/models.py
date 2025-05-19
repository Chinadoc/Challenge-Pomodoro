from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional, List, Dict, Any
import uuid

class TimerMode(Enum):
    """Represents the different timer modes."""
    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()
    CUSTOM = auto()

class TaskPriority(Enum):
    """Priority levels for tasks."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class TaskStatus(Enum):
    """Status of a task."""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"

@dataclass
class Task:
    """Represents a task with tracking information."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    category: str = "General"
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    estimated_duration: int = 25  # in minutes
    time_spent: int = 0  # in seconds
    tags: List[str] = field(default_factory=list)
    pomodoros_completed: int = 0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'estimated_duration': self.estimated_duration,
            'time_spent': self.time_spent,
            'tags': self.tags,
            'pomodoros_completed': self.pomodoros_completed,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        task = cls()
        task.id = data.get('id', str(uuid.uuid4()))
        task.title = data.get('title', '')
        task.description = data.get('description', '')
        task.category = data.get('category', 'General')
        task.priority = TaskPriority(data.get('priority', 2))
        task.status = TaskStatus(data.get('status', 'To Do'))
        task.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        task.updated_at = datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        task.due_date = datetime.fromisoformat(data['due_date']) if data.get('due_date') else None
        task.estimated_duration = data.get('estimated_duration', 25)
        task.time_spent = data.get('time_spent', 0)
        task.tags = data.get('tags', [])
        task.pomodoros_completed = data.get('pomodoros_completed', 0)
        task.notes = data.get('notes', '')
        return task

@dataclass
class PomodoroSession:
    """Represents a completed Pomodoro session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: int = 0  # in seconds
    mode: TimerMode = TimerMode.WORK
    was_completed: bool = False
    notes: str = ""

    def complete(self) -> None:
        """Mark the session as completed."""
        self.end_time = datetime.now()
        self.duration = int((self.end_time - self.start_time).total_seconds())
        self.was_completed = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'mode': self.mode.name,
            'was_completed': self.was_completed,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PomodoroSession':
        """Create session from dictionary."""
        session = cls()
        session.id = data.get('id', str(uuid.uuid4()))
        session.task_id = data.get('task_id')
        session.start_time = datetime.fromisoformat(data.get('start_time', datetime.now().isoformat()))
        session.end_time = datetime.fromisoformat(data['end_time']) if data.get('end_time') else None
        session.duration = data.get('duration', 0)
        session.mode = TimerMode[data.get('mode', 'WORK')]
        session.was_completed = data.get('was_completed', False)
        session.notes = data.get('notes', '')
        return session

@dataclass
class TimerSettings:
    """User settings for the Pomodoro timer."""
    work_duration: int = 25  # minutes
    short_break_duration: int = 5  # minutes
    long_break_duration: int = 15  # minutes
    long_break_interval: int = 4  # number of work sessions before long break
    auto_start_breaks: bool = True
    auto_start_pomodoros: bool = False
    notifications: bool = True
    dark_mode: bool = True
    theme: str = "default"
    categories: List[str] = field(default_factory=lambda: ["Work", "Study", "Personal"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'work_duration': self.work_duration,
            'short_break_duration': self.short_break_duration,
            'long_break_duration': self.long_break_duration,
            'long_break_interval': self.long_break_interval,
            'auto_start_breaks': self.auto_start_breaks,
            'auto_start_pomodoros': self.auto_start_pomodoros,
            'notifications': self.notifications,
            'dark_mode': self.dark_mode,
            'theme': self.theme,
            'categories': self.categories
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimerSettings':
        """Create settings from dictionary."""
        settings = cls()
        settings.work_duration = data.get('work_duration', 25)
        settings.short_break_duration = data.get('short_break_duration', 5)
        settings.long_break_duration = data.get('long_break_duration', 15)
        settings.long_break_interval = data.get('long_break_interval', 4)
        settings.auto_start_breaks = data.get('auto_start_breaks', True)
        settings.auto_start_pomodoros = data.get('auto_start_pomodoros', False)
        settings.notifications = data.get('notifications', True)
        settings.dark_mode = data.get('dark_mode', True)
        settings.theme = data.get('theme', 'default')
        settings.categories = data.get('categories', ["Work", "Study", "Personal"])
        return settings
