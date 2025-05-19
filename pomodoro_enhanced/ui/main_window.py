""
Main window for the Enhanced Pomodoro Timer application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any
import logging
from datetime import datetime, timedelta

from ..core.models import Task, TimerMode, TaskStatus
from ..core.timer_service import TimerService, TimerState, TimerUpdate
from .task_panel import TaskPanel
from .stats_panel import StatsPanel
from .settings_panel import SettingsPanel

class MainWindow(tk.Tk):
    """Main application window."""
    
    def __init__(self, timer_service: TimerService, data_manager, *args, **kwargs):
        """Initialize the main window."""
        super().__init__(*args, **kwargs)
        
        self.timer_service = timer_service
        self.data_manager = data_manager
        self.logger = logging.getLogger(f"{__name__}.MainWindow")
        
        # Window configuration
        self.title("Enhanced Pomodoro Timer")
        self.geometry("800x600")
        self.minsize(800, 600)
        
        # Style configuration
        self._setup_styles()
        
        # Create UI components
        self._create_widgets()
        
        # Update UI with current state
        self.update_ui_state()
        self.update_ui_mode(self.timer_service.mode)
    
    def _setup_styles(self) -> None:
        """Configure application styles."""
        style = ttk.Style()
        
        # Configure theme
        self.tk.call('source', 'themes/azure/azure.tcl')
        self.tk.call('set_theme', 'dark')
        
        # Custom styles
        style.configure('Timer.TLabel', font=('Helvetica', 48, 'bold'))
        style.configure('Mode.TLabel', font=('Helvetica', 14, 'bold'))
        style.configure('TimerButton.TButton', font=('Helvetica', 12, 'bold'))
        style.configure('Accent.TButton', font=('Helvetica', 12, 'bold'), foreground='white')
        
        # Configure notebook style
        style.configure('TNotebook', tabposition='n')
        style.configure('TNotebook.Tab', padding=[15, 5], font=('Helvetica', 10, 'bold'))
    
    def _create_widgets(self) -> None:
        """Create and arrange all UI widgets."""
        # Main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Timer display
        self._create_timer_frame()
        
        # Control buttons
        self._create_control_buttons()
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Create tabs
        self.task_panel = TaskPanel(self.notebook, self.data_manager, self._on_task_selected)
        self.stats_panel = StatsPanel(self.notebook, self.data_manager)
        self.settings_panel = SettingsPanel(self.notebook, self.timer_service, self.data_manager)
        
        self.notebook.add(self.task_panel, text="Tasks")
        self.notebook.add(self.stats_panel, text="Statistics")
        self.notebook.add(self.settings_panel, text="Settings")
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            self.main_container,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=5
        )
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Set initial status
        self.update_status("Ready")
    
    def _create_timer_frame(self) -> None:
        """Create the timer display frame."""
        timer_frame = ttk.LabelFrame(self.main_container, text="Pomodoro Timer", padding=10)
        timer_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Mode label
        self.mode_var = tk.StringVar(value="Work")
        self.mode_label = ttk.Label(
            timer_frame,
            textvariable=self.mode_var,
            style='Mode.TLabel'
        )
        self.mode_label.pack(pady=(0, 5))
        
        # Timer display
        self.time_var = tk.StringVar(value="25:00")
        self.timer_label = ttk.Label(
            timer_frame,
            textvariable=self.time_var,
            style='Timer.TLabel'
        )
        self.timer_label.pack(pady=10)
        
        # Current task display
        self.task_var = tk.StringVar(value="No task selected")
        self.task_label = ttk.Label(
            timer_frame,
            textvariable=self.task_var,
            wraplength=400
        )
        self.task_label.pack(fill=tk.X, pady=(0, 10))
    
    def _create_control_buttons(self) -> None:
        """Create the control buttons frame."""
        button_frame = ttk.Frame(self.main_container)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Start/Pause button
        self.start_button = ttk.Button(
            button_frame,
            text="Start",
            style='Accent.TButton',
            command=self._on_start_pause_clicked
        )
        self.start_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Stop button
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self._on_stop_clicked
        )
        self.stop_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Skip button
        self.skip_button = ttk.Button(
            button_frame,
            text="Skip",
            command=self._on_skip_clicked
        )
        self.skip_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    # Public methods for UI updates
    
    def update_timer_display(self, update: TimerUpdate) -> None:
        """Update the timer display with the current time."""
        minutes = update.time_left // 60
        seconds = update.time_left % 60
        self.time_var.set(f"{minutes:02d}:{seconds:02d}")
        
        # Update progress in task panel if we have a task
        if hasattr(self, 'task_panel') and update.current_task:
            self.task_panel.update_task_progress(update.current_task.id, update.progress)
    
    def update_ui_state(self) -> None:
        """Update UI elements based on the current timer state."""
        state = self.timer_service.state
        
        # Update button states and text
        if state == TimerState.RUNNING:
            self.start_button.config(text="Pause")
            self.stop_button.config(state=tk.NORMAL)
            self.skip_button.config(state=tk.NORMAL)
        elif state == TimerState.PAUSED:
            self.start_button.config(text="Resume")
            self.stop_button.config(state=tk.NORMAL)
            self.skip_button.config(state=tk.NORMAL)
        else:  # STOPPED or COMPLETED
            self.start_button.config(text="Start")
            self.stop_button.config(state=tk.DISABLED)
            self.skip_button.config(state=tk.DISABLED)
    
    def update_ui_mode(self, mode: TimerMode) -> None:
        """Update UI elements based on the current timer mode."""
        self.mode_var.set(mode.name.replace('_', ' ').title())
        
        # Update colors based on mode
        style = ttk.Style()
        if mode == TimerMode.WORK:
            style.configure('TFrame', background='#2d2d2d')
            style.configure('Accent.TButton', background='#e74c3c')  # Red
        else:  # BREAK modes
            style.configure('TFrame', background='#1e3a5f')
            style.configure('Accent.TButton', background='#27ae60')  # Green
    
    def on_session_complete(self, session) -> None:
        """Handle session completion."""
        # Play sound
        self.bell()
        
        # Show notification
        if session.mode == TimerMode.WORK:
            messagebox.showinfo(
                "Work Session Complete",
                "Time for a break!"
            )
        else:
            messagebox.showinfo(
                "Break Complete",
                "Break is over. Ready for the next work session?"
            )
        
        # Refresh tasks and stats
        if hasattr(self, 'task_panel'):
            self.task_panel.refresh_tasks()
        
        if hasattr(self, 'stats_panel'):
            self.stats_panel.refresh_stats()
    
    def update_status(self, message: str) -> None:
        """Update the status bar with a message."""
        self.status_var.set(message)
        self.logger.info(f"Status: {message}")
    
    # Event handlers
    
    def _on_start_pause_clicked(self) -> None:
        """Handle Start/Pause button click."""
        if self.timer_service.state == TimerState.RUNNING:
            self.timer_service.pause()
        else:
            self.timer_service.start()
    
    def _on_stop_clicked(self) -> None:
        """Handle Stop button click."""
        if messagebox.askyesno("Stop Timer", "Are you sure you want to stop the current session?"):
            self.timer_service.stop()
    
    def _on_skip_clicked(self) -> None:
        """Handle Skip button click."""
        if messagebox.askyesno("Skip Session", "Are you sure you want to skip the current session?"):
            self.timer_service.skip()
    
    def _on_task_selected(self, task: Optional[Task]) -> None:
        """Handle task selection from the task panel."""
        if task:
            self.task_var.set(f"Current Task: {task.title}")
            self.update_status(f"Selected task: {task.title}")
            
            # Update the timer service with the selected task
            self.timer_service.current_task = task
            
            # If the timer is stopped, update the task display
            if self.timer_service.state == TimerState.STOPPED:
                self.task_label.config(foreground='white')
        else:
            self.task_var.set("No task selected")
            self.timer_service.current_task = None
    
    def mainloop(self, *args, **kwargs) -> None:
        """Start the main event loop."""
        self.update_status("Application started")
        super().mainloop(*args, **kwargs)
