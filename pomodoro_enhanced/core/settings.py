from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class TimerSettings:
    """Stores all configurable settings for the Pomodoro timer."""
    work_duration: int = 25
    short_break_duration: int = 5
    long_break_duration: int = 15
    long_break_interval: int = 4
    auto_start_breaks: bool = True
    auto_start_pomodoros: bool = False
    notifications: bool = True
    sound_enabled: bool = True
    sound_pack: str = "classic"
    gamification_enabled: bool = True
    daily_goal: int = 4
    dark_mode: bool = True
    theme: str = "default"
    language: str = "en"
    categories: List[str] = field(default_factory=lambda: ["Work", "Study", "Personal"])

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimerSettings':
        """Create settings from a dictionary, using defaults for missing keys."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to a dictionary."""
        return asdict(self)

    @classmethod
    def load(cls, filepath: Path) -> 'TimerSettings':
        """Load settings from a JSON file."""
        try:
            data = json.loads(filepath.read_text())
            return cls.from_dict(data)
        except FileNotFoundError:
            return cls()
        except json.JSONDecodeError:
            return cls()

    def save(self, filepath: Path) -> None:
        """Save settings to a JSON file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(self.to_dict(), indent=2))
