import time
import threading
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Optional, Callable, Dict, Any, List
import logging
from dataclasses import dataclass
from .models import TimerMode, PomodoroSession, Task

class TimerState(Enum):
    """Possible states of the Pomodoro timer."""
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()

@dataclass
class TimerUpdate:
    """Data class for timer update events."""
    time_left: int  # seconds
    mode: TimerMode
    state: TimerState
    current_cycle: int
    total_cycles: int
    current_task: Optional[Task] = None

class TimerService:
    """
    Service class that manages the Pomodoro timer logic.
    Handles work/break cycles, timing, and session tracking.
    """
    
    def __init__(self, data_manager, settings=None):
        """
        Initialize the TimerService.
        
        Args:
            data_manager: Instance of DataManager for data persistence
            settings: Optional TimerSettings to override defaults
        """
        self.logger = logging.getLogger(__name__)
        self.data_manager = data_manager
        self.settings = settings or data_manager.get_settings()
        
        # Timer state
        self.state = TimerState.STOPPED
        self.mode = TimerMode.WORK
        self.time_left = self.settings.work_duration * 60  # in seconds
        self.work_duration = self.settings.work_duration * 60
        self.short_break_duration = self.settings.short_break_duration * 60
        self.long_break_duration = self.settings.long_break_duration * 60
        
        # Session tracking
        self.current_cycle = 0
        self.total_cycles = 0
        self.current_session: Optional[PomodoroSession] = None
        self.current_task: Optional[Task] = None
        
        # Threading
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._paused = False
        self._paused_event = threading.Event()
        self._paused_event.set()  # Start not paused
        
        # Callbacks
        self._update_callbacks: List[Callable[[TimerUpdate], None]] = []
        self._mode_change_callbacks: List[Callable[[TimerMode], None]] = []
        self._state_change_callbacks: List[Callable[[TimerState], None]] = []
        self._session_complete_callbacks: List[Callable[[PomodoroSession], None]] = []
    
    # Public API
    
    def start(self, task: Optional[Task] = None) -> bool:
        """Start the timer."""
        if self.state == TimerState.RUNNING:
            self.logger.warning("Timer is already running")
            return False
            
        self.current_task = task
        
        if self.state == TimerState.STOPPED:
            # Start a new session
            self.current_session = PomodoroSession(
                task_id=task.id if task else None,
                mode=self.mode,
                start_time=datetime.now()
            )
            self.logger.info(f"Started new {self.mode.name} session")
        else:  # Resuming from paused
            self.logger.info(f"Resumed {self.mode.name} session")
        
        self.state = TimerState.RUNNING
        self._stop_event.clear()
        self._paused = False
        self._paused_event.set()
        
        # Start the timer thread if not already running
        if not self._timer_thread or not self._timer_thread.is_alive():
            self._timer_thread = threading.Thread(target=self._run_timer, daemon=True)
            self._timer_thread.start()
        
        self._notify_state_change()
        self._notify_update()
        return True
    
    def pause(self) -> bool:
        """Pause the running timer."""
        if self.state != TimerState.RUNNING:
            self.logger.warning("Cannot pause: timer is not running")
            return False
            
        self.state = TimerState.PAUSED
        self._paused = True
        self._paused_event.clear()
        
        # Record the pause time for accurate duration calculation
        if self.current_session:
            self.current_session.pause_time = datetime.now()
        
        self.logger.info("Timer paused")
        self._notify_state_change()
        self._notify_update()
        return True
    
    def stop(self, completed: bool = False) -> bool:
        """Stop the timer.
        
        Args:
            completed: Whether the timer completed naturally or was stopped manually
        """
        if self.state == TimerState.STOPPED:
            return False
            
        self.logger.info(f"Stopping timer (completed: {completed})")
        
        # Complete the current session
        if self.current_session:
            self.current_session.complete()
            self.current_session.was_completed = completed
            
            # Save the session
            self.data_manager.add_session(self.current_session)
            
            # Update task stats if there's an associated task
            if self.current_task and completed and self.mode == TimerMode.WORK:
                self.current_task.time_spent += self.work_duration
                self.current_task.pomodoros_completed += 1
                self.data_manager.update_task(self.current_task)
            
            # Notify listeners
            self._notify_session_complete(self.current_session)
            
            # Clean up
            self.current_session = None
        
        # Reset timer state
        self.state = TimerState.STOPPED
        self._stop_event.set()
        self._paused = False
        self._paused_event.set()
        
        # If completed naturally, move to next mode
        if completed:
            self._next_mode()
        
        self._notify_state_change()
        self._notify_update()
        return True
    
    def reset(self) -> bool:
        """Reset the timer to initial state."""
        self.stop(completed=False)
        
        # Reset to work mode
        self.mode = TimerMode.WORK
        self.time_left = self.work_duration
        self.current_cycle = 0
        
        self._notify_update()
        return True
    
    def set_mode(self, mode: TimerMode) -> bool:
        """Set the timer mode (WORK, SHORT_BREAK, LONG_BREAK, CUSTOM)."""
        if self.state != TimerState.STOPPED:
            self.logger.warning("Cannot change mode while timer is running")
            return False
            
        old_mode = self.mode
        self.mode = mode
        
        # Update time_left based on mode
        if mode == TimerMode.WORK:
            self.time_left = self.work_duration
        elif mode == TimerMode.SHORT_BREAK:
            self.time_left = self.short_break_duration
        elif mode == TimerMode.LONG_BREAK:
            self.time_left = self.long_break_duration
        # For CUSTOM mode, time_left should be set separately
        
        if old_mode != mode:
            self._notify_mode_change()
            
        self._notify_update()
        return True
    
    def set_duration(self, minutes: int) -> bool:
        """Set the duration for the current mode in minutes."""
        if self.state != TimerState.STOPPED:
            self.logger.warning("Cannot change duration while timer is running")
            return False
            
        seconds = minutes * 60
        
        if self.mode == TimerMode.WORK:
            self.work_duration = seconds
        elif self.mode == TimerMode.SHORT_BREAK:
            self.short_break_duration = seconds
        elif self.mode == TimerMode.LONG_BREAK:
            self.long_break_duration = seconds
        
        self.time_left = seconds
        self._notify_update()
        return True
    
    # Callback registration
    
    def register_update_callback(self, callback: Callable[[TimerUpdate], None]) -> None:
        """Register a callback for timer updates."""
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)
    
    def unregister_update_callback(self, callback: Callable[[TimerUpdate], None]) -> None:
        """Unregister a timer update callback."""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
    
    def register_mode_change_callback(self, callback: Callable[[TimerMode], None]) -> None:
        """Register a callback for mode changes."""
        if callback not in self._mode_change_callbacks:
            self._mode_change_callbacks.append(callback)
    
    def register_state_change_callback(self, callback: Callable[[TimerState], None]) -> None:
        """Register a callback for state changes."""
        if callback not in self._state_change_callbacks:
            self._state_change_callbacks.append(callback)
    
    def register_session_complete_callback(self, callback: Callable[[PomodoroSession], None]) -> None:
        """Register a callback for session completion."""
        if callback not in self._session_complete_callbacks:
            self._session_complete_callbacks.append(callback)
    
    # Private methods
    
    def _run_timer(self) -> None:
        """Main timer loop."""
        last_update = time.time()
        
        while not self._stop_event.is_set():
            current_time = time.time()
            elapsed = current_time - last_update
            last_update = current_time
            
            if self.state == TimerState.RUNNING and not self._paused:
                self.time_left = max(0, self.time_left - elapsed)
                
                # Notify listeners of the update
                self._notify_update()
                
                # Check if timer has completed
                if self.time_left <= 0:
                    self.logger.info(f"Timer completed: {self.mode.name}")
                    self.stop(completed=True)
                    
                    # Auto-start next timer if configured
                    if (self.mode == TimerMode.WORK and self.settings.auto_start_breaks) or \
                       (self.mode != TimerMode.WORK and self.settings.auto_start_pomodoros):
                        # Small delay before starting next timer
                        time.sleep(1)
                        self.start(task=self.current_task)
            
            # Sleep to prevent high CPU usage
            time.sleep(0.1)
    
    def _next_mode(self) -> None:
        """Transition to the next mode in the Pomodoro cycle."""
        old_mode = self.mode
        
        if self.mode == TimerMode.WORK:
            self.current_cycle += 1
            
            # Check if it's time for a long break
            if self.current_cycle % self.settings.long_break_interval == 0:
                self.mode = TimerMode.LONG_BREAK
                self.time_left = self.long_break_duration
            else:
                self.mode = TimerMode.SHORT_BREAK
                self.time_left = self.short_break_duration
        else:
            # After any break, go back to work
            self.mode = TimerMode.WORK
            self.time_left = self.work_duration
        
        self.logger.info(f"Mode changed from {old_mode.name} to {self.mode.name}")
        self._notify_mode_change()
    
    # Notification methods
    
    def _notify_update(self) -> None:
        """Notify all registered callbacks of a timer update."""
        update = TimerUpdate(
            time_left=int(self.time_left),
            mode=self.mode,
            state=self.state,
            current_cycle=self.current_cycle,
            total_cycles=self.total_cycles,
            current_task=self.current_task
        )
        
        for callback in self._update_callbacks:
            try:
                callback(update)
            except Exception as e:
                self.logger.error(f"Error in update callback: {e}")
    
    def _notify_mode_change(self) -> None:
        """Notify all registered callbacks of a mode change."""
        for callback in self._mode_change_callbacks:
            try:
                callback(self.mode)
            except Exception as e:
                self.logger.error(f"Error in mode change callback: {e}")
    
    def _notify_state_change(self) -> None:
        """Notify all registered callbacks of a state change."""
        for callback in self._state_change_callbacks:
            try:
                callback(self.state)
            except Exception as e:
                self.logger.error(f"Error in state change callback: {e}")
    
    def _notify_session_complete(self, session: PomodoroSession) -> None:
        """Notify all registered callbacks of a completed session."""
        for callback in self._session_complete_callbacks:
            try:
                callback(session)
            except Exception as e:
                self.logger.error(f"Error in session complete callback: {e}")
