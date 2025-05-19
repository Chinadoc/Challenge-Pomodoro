"""Example of using TimerFSM with a simple Tkinter UI."""
import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime

from pomodoro_enhanced.core.state import TimerFSM, Phase, Durations


class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Timer")
        
        # Initialize the FSM
        self.fsm = TimerFSM(
            durations=Durations(work=0.1, short_break=0.05, long_break=0.1, long_break_interval=2),
            on_state_change=self.on_state_change
        )
        
        self.setup_ui()
        self.running = False
        self.last_update = time.time()
        self.update_timer()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Timer display
        self.time_var = tk.StringVar(value="25:00")
        self.timer_label = ttk.Label(
            self.main_frame,
            textvariable=self.time_var,
            font=('Helvetica', 48, 'bold')
        )
        self.timer_label.grid(row=0, column=0, columnspan=3, pady=20)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to start")
        self.status_label = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            font=('Helvetica', 14)
        )
        self.status_label.grid(row=1, column=0, columnspan=3, pady=10)
        
        # Control buttons
        self.start_button = ttk.Button(
            self.main_frame,
            text="Start",
            command=self.toggle_timer
        )
        self.start_button.grid(row=2, column=0, padx=5, pady=10)
        
        self.pause_button = ttk.Button(
            self.main_frame,
            text="Pause",
            command=self.toggle_pause,
            state=tk.DISABLED
        )
        self.pause_button.grid(row=2, column=1, padx=5, pady=10)
        
        self.reset_button = ttk.Button(
            self.main_frame,
            text="Reset",
            command=self.reset_timer
        )
        self.reset_button.grid(row=2, column=2, padx=5, pady=10)
        
        # Cycles display
        self.cycles_var = tk.StringVar(value="Cycles: 0")
        self.cycles_label = ttk.Label(
            self.main_frame,
            textvariable=self.cycles_var
        )
        self.cycles_label.grid(row=3, column=0, columnspan=3, pady=10)
    
    def toggle_timer(self):
        """Start or stop the timer."""
        if not self.running:
            self.running = True
            self.start_button.config(text="Stop")
            self.pause_button.config(state=tk.NORMAL)
            self.last_update = time.time()
        else:
            self.running = False
            self.start_button.config(text="Start")
            self.pause_button.config(state=tk.DISABLED)
    
    def toggle_pause(self):
        """Pause or resume the timer."""
        if self.fsm.is_paused:
            self.fsm.resume()
            self.pause_button.config(text="Pause")
            self.last_update = time.time()
        else:
            self.fsm.pause()
            self.pause_button.config(text="Resume")
    
    def reset_timer(self):
        """Reset the timer to initial state."""
        self.running = False
        self.fsm = TimerFSM(
            durations=Durations(work=0.1, short_break=0.05, long_break=0.1, long_break_interval=2),
            on_state_change=self.on_state_change
        )
        self.start_button.config(text="Start")
        self.pause_button.config(state=tk.DISABLED, text="Pause")
        self.update_display()
    
    def update_timer(self):
        """Update the timer display and handle state changes."""
        if self.running and not self.fsm.is_paused:
            current_time = time.time()
            elapsed = current_time - self.last_update
            self.last_update = current_time
            
            # Update the FSM
            if self.fsm.tick(elapsed):
                # Phase completed, FSM already advanced to next phase
                pass
            
        self.update_display()
        self.root.after(50, self.update_timer)
    
    def update_display(self):
        """Update the display with current timer values."""
        # Update time display
        minutes = int(self.fsm.seconds_left // 60)
        seconds = int(self.fsm.seconds_left % 60)
        self.time_var.set(f"{minutes:02d}:{seconds:02d}")
        
        # Update status
        if self.fsm.is_paused:
            self.status_var.set("Paused")
        else:
            status_map = {
                Phase.WORK: "Working",
                Phase.SHORT_BREAK: "Short Break",
                Phase.LONG_BREAK: "Long Break",
                Phase.PAUSED: "Paused"
            }
            self.status_var.set(status_map.get(self.fsm.state, ""))
        
        # Update cycles
        self.cycles_var.set(f"Cycles: {self.fsm.cycles}")
    
    def on_state_change(self, new_state):
        """Handle state changes from the FSM."""
        print(f"State changed to: {new_state.name}")
        if new_state != Phase.PAUSED:
            self.pause_button.config(text="Pause")
        self.update_display()


if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()
