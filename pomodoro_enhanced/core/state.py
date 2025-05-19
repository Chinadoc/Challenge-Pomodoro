"""Finite‑state Pomodoro session tracker.

`TimerFSM` separates bare *count‑down* logic (handled elsewhere) from the
*semantic* state (work / short break / long break / paused).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional


class Phase(Enum):
    """Represents the current phase of the Pomodoro timer."""
    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()
    PAUSED = auto()  # meta‑state; duration = remaining seconds


class TransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


@dataclass
class Durations:
    """Container for all timer durations in minutes."""
    work: int  # minutes
    short_break: int
    long_break: int
    long_break_interval: int = 4


@dataclass
class TimerFSM:
    """Finite State Machine for Pomodoro timer logic.
    
    Handles state transitions and enforces valid state changes.
    """
    durations: Durations
    on_state_change: Optional[Callable[[Phase], None]] = None

    phase: Phase = Phase.WORK
    cycles: int = 0  # completed work phases
    seconds_left: int = field(init=False)
    _paused_phase: Optional[Phase] = field(default=None, init=False, repr=False)

    # transition map – only *legal* next phases listed
    _ALLOWED: Dict[Phase, List[Phase]] = field(
        default_factory=lambda: {
            Phase.WORK:       [Phase.SHORT_BREAK, Phase.LONG_BREAK, Phase.PAUSED],
            Phase.SHORT_BREAK: [Phase.WORK, Phase.PAUSED],
            Phase.LONG_BREAK:  [Phase.WORK, Phase.PAUSED],
            Phase.PAUSED:      [Phase.WORK, Phase.SHORT_BREAK, Phase.LONG_BREAK],
        },
        init=False,
        repr=False,
    )

    def __post_init__(self):
        self.seconds_left = self.durations.work * 60

    @property
    def state(self) -> Phase:
        """Get the current phase of the timer."""
        return self.phase

    @property
    def is_paused(self) -> bool:
        """Check if the timer is currently paused."""
        return self.phase is Phase.PAUSED

    @property
    def duration(self) -> int:
        """Get the duration of the current phase in seconds."""
        return self._duration_for(self.phase)

    def tick(self, seconds: int = 1) -> bool:
        """Advance the countdown; returns True when phase completed."""
        if self.is_paused:
            return False
            
        self.seconds_left = max(0, self.seconds_left - seconds)
        if self.seconds_left == 0:
            self.next()
            return True
        return False

    def next(self):
        """Transition to the next logical phase."""
        if self.phase is Phase.WORK:
            self.cycles += 1
            next_phase = (
                Phase.LONG_BREAK 
                if self.cycles % self.durations.long_break_interval == 0 
                else Phase.SHORT_BREAK
            )
        else:
            next_phase = Phase.WORK
        self._set_phase(next_phase)

    def pause(self):
        """Pause the current phase."""
        if self.phase is Phase.PAUSED:
            return
            
        self._paused_phase = self.phase
        self._set_phase(Phase.PAUSED)

    def resume(self):
        """Resume from a paused state."""
        if not self.is_paused or self._paused_phase is None:
            return
            
        self._set_phase(self._paused_phase)
        self._paused_phase = None

    def _set_phase(self, new_phase: Phase):
        """Safely transition to a new phase."""
        if new_phase not in self._ALLOWED[self.phase]:
            raise TransitionError(
                f"Illegal transition: {self.phase.name} → {new_phase.name}"
            )
            
        old_phase = self.phase
        self.phase = new_phase
        
        # Only reset timer if not pausing/resuming
        if old_phase is not Phase.PAUSED and new_phase is not Phase.PAUSED:
            self.seconds_left = self._duration_for(new_phase)
            
        if self.on_state_change:
            self.on_state_change(new_phase)

    def _duration_for(self, phase: Phase) -> int:
        """Get duration in seconds for a given phase."""
        if phase is Phase.PAUSED:
            return self.seconds_left
            
        minutes = {
            Phase.WORK: self.durations.work,
            Phase.SHORT_BREAK: self.durations.short_break,
            Phase.LONG_BREAK: self.durations.long_break,
        }[phase]
        return minutes * 60
