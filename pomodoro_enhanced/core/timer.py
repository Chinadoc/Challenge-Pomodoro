"""Core Pomodoro timer functionality."""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Optional, Callable, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TimerMode(Enum):
    """Timer modes."""
    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()

@dataclass
class TimerState:
    """Current state of the timer."""
    mode: TimerMode
    remaining: int  # seconds
    is_running: bool
    current_cycle: int
    total_cycles: int
    work_duration: int
    short_break_duration: int
    long_break_duration: int
    long_break_interval: int

class TimerService:
    """Manages the Pomodoro timer state and notifies observers of changes."""
    
    def __init__(
        self,
        work_duration: int = 25 * 60,  # seconds
        short_break_duration: int = 5 * 60,
        long_break_duration: int = 15 * 60,
        long_break_interval: int = 4,
    ):
        self.work_duration = work_duration
        self.short_break_duration = short_break_duration
        self.long_break_duration = long_break_duration
        self.long_break_interval = long_break_interval
        
        self._mode = TimerMode.WORK
        self._remaining = work_duration
        self._is_running = False
        self._current_cycle = 0
        self._last_tick = None
        self._observers: List[Callable[['TimerState'], None]] = []
        
    @property
    def state(self) -> TimerState:
        """Get the current timer state."""
        return TimerState(
            mode=self._mode,
            remaining=self._remaining,
            is_running=self._is_running,
            current_cycle=self._current_cycle,
            total_cycles=self.long_break_interval,
            work_duration=self.work_duration,
            short_break_duration=self.short_break_duration,
            long_break_duration=self.long_break_duration,
            long_break_interval=self.long_break_interval,
        )
    
    def add_observer(self, callback: Callable[[TimerState], None]) -> None:
        """Add an observer to be notified of timer state changes."""
        self._observers.append(callback)
    
    def remove_observer(self, callback: Callable[[TimerState], None]) -> None:
        """Remove an observer."""
        self._observers.remove(callback)
    
    def _notify_observers(self) -> None:
        """Notify all observers of the current state."""
        state = self.state
        for observer in self._observers:
            try:
                observer(state)
            except Exception as e:
                logger.error("Error in timer observer: %s", e, exc_info=True)
    
    def start(self) -> None:
        """Start the timer."""
        if not self._is_running:
            self._is_running = True
            self._last_tick = time.monotonic()
            self._notify_observers()
    
    def pause(self) -> None:
        """Pause the timer."""
        if self._is_running:
            self._is_running = False
            self._update_remaining()
            self._notify_observers()
    
    def reset(self) -> None:
        """Reset the timer to the initial state."""
        self._is_running = False
        self._mode = TimerMode.WORK
        self._current_cycle = 0
        self._remaining = self.work_duration
        self._last_tick = None
        self._notify_observers()
    
    def toggle(self) -> None:
        """Toggle between start and pause."""
        if self._is_running:
            self.pause()
        else:
            self.start()
    
    def skip(self) -> None:
        """Skip to the next timer phase."""
        self._advance_phase()
    
    def _update_remaining(self) -> None:
        """Update remaining time based on elapsed time since last tick."""
        if self._is_running and self._last_tick is not None:
            now = time.monotonic()
            elapsed = now - self._last_tick
            self._last_tick = now
            
            self._remaining = max(0, self._remaining - elapsed)
            
            if self._remaining <= 0:
                self._on_timer_complete()
    
    def _on_timer_complete(self) -> None:
        """Handle timer completion."""
        if self._mode == TimerMode.WORK:
            self._current_cycle += 1
            if self._current_cycle % self.long_break_interval == 0:
                self._mode = TimerMode.LONG_BREAK
                self._remaining = self.long_break_duration
            else:
                self._mode = TimerMode.SHORT_BREAK
                self._remaining = self.short_break_duration
        else:
            self._mode = TimerMode.WORK
            self._remaining = self.work_duration
        
        self._is_running = False
        self._notify_observers()
    
    def _advance_phase(self) -> None:
        """Advance to the next timer phase."""
        if self._mode == TimerMode.WORK:
            self._current_cycle += 1
            if self._current_cycle % self.long_break_interval == 0:
                self._mode = TimerMode.LONG_BREAK
                self._remaining = self.long_break_duration
            else:
                self._mode = TimerMode.SHORT_BREAK
                self._remaining = self.short_break_duration
        else:
            self._mode = TimerMode.WORK
            self._remaining = self.work_duration
        
        self._is_running = False
        self._notify_observers()
    
    def update(self) -> None:
        """Update the timer state. Call this regularly from the main loop."""
        if self._is_running:
            self._update_remaining()
            self._notify_observers()
