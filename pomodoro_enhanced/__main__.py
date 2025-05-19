#!/usr/bin/env python3
"""
Enhanced Pomodoro Timer - Main Application
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

# Add the parent directory to the path so we can import our package
sys.path.insert(0, str(Path(__file__).parent.parent))

from pomodoro_enhanced.core.data_manager import DataManager
from pomodoro_enhanced.core.timer_service import TimerService, TimerState, TimerMode
from pomodoro_enhanced.ui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pomodoro_enhanced.log')
    ]
)
logger = logging.getLogger(__name__)

class PomodoroApp:
    """Main application class for the Enhanced Pomodoro Timer."""
    
    def __init__(self):
        """Initialize the application."""
        self.logger = logging.getLogger(f"{__name__}.PomodoroApp")
        self.logger.info("Initializing Pomodoro App")
        
        # Set up data management
        self.data_manager = DataManager()
        
        # Set up timer service
        self.timer_service = TimerService(self.data_manager)
        
        # Set up UI
        self.main_window = MainWindow(self.timer_service, self.data_manager)
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self) -> None:
        """Connect timer service signals to UI updates."""
        self.timer_service.register_update_callback(self._on_timer_update)
        self.timer_service.register_state_change_callback(self._on_timer_state_change)
        self.timer_service.register_mode_change_callback(self._on_timer_mode_change)
        self.timer_service.register_session_complete_callback(self._on_session_complete)
    
    def run(self) -> None:
        """Run the application."""
        self.logger.info("Starting Pomodoro App")
        self.main_window.mainloop()
    
    # Signal handlers
    
    def _on_timer_update(self, update) -> None:
        """Handle timer update events."""
        self.main_window.update_timer_display(update)
    
    def _on_timer_state_change(self, state: TimerState) -> None:
        """Handle timer state change events."""
        self.main_window.update_ui_state()
    
    def _on_timer_mode_change(self, mode: TimerMode) -> None:
        """Handle timer mode change events."""
        self.main_window.update_ui_mode(mode)
    
    def _on_session_complete(self, session) -> None:
        """Handle session completion events."""
        self.main_window.on_session_complete(session)

def main() -> None:
    """Main entry point for the application."""
    try:
        app = PomodoroApp()
        app.run()
    except Exception as e:
        logger.critical("Unhandled exception", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
