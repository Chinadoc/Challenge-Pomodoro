"""
Intensive Mode UI components for the Pomodoro Timer
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

def show_intensive_mode_dialog(parent, callback):
    """
    Display a dialog for setting up intensive work mode
    
    Args:
        parent: Parent tkinter window
        callback: Function to call with selected duration
    """
    dialog = tk.Toplevel(parent)
    dialog.title("Intensive Work Mode")
    dialog.geometry("350x400")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center the dialog
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
    dialog.geometry(f"+{x}+{y}")
    
    # Create main frame
    main_frame = ttk.Frame(dialog, padding=15)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title and description
    title_label = ttk.Label(
        main_frame, 
        text="Intensive Mode", 
        font=("Helvetica", 16, "bold")
    )
    title_label.pack(pady=(0, 5))
    
    description = (
        "Intensive Mode lets you commit to focused work for "
        "a longer duration. Complete the full session to earn "
        "bonus points and rewards. How long can you focus today?"
    )
    
    desc_label = ttk.Label(
        main_frame, 
        text=description, 
        wraplength=300, 
        justify=tk.CENTER
    )
    desc_label.pack(pady=(0, 20))
    
    # Duration options
    duration_frame = ttk.LabelFrame(main_frame, text="Select Duration")
    duration_frame.pack(fill=tk.X, pady=10)
    
    # Duration radio buttons
    duration_var = tk.IntVar(value=60)  # Default to 1 hour
    durations = [
        ("30 minutes", 30),
        ("1 hour", 60),
        ("2 hours", 120),
        ("3 hours", 180)
    ]
    
    for text, value in durations:
        radio = ttk.Radiobutton(
            duration_frame,
            text=text,
            value=value,
            variable=duration_var
        )
        radio.pack(anchor=tk.W, padx=10, pady=5)
    
    # Custom duration
    custom_frame = ttk.Frame(main_frame)
    custom_frame.pack(fill=tk.X, pady=10)
    
    custom_check_var = tk.BooleanVar(value=False)
    custom_check = ttk.Checkbutton(
        custom_frame,
        text="Custom duration:",
        variable=custom_check_var,
        command=lambda: toggle_custom_entry()
    )
    custom_check.pack(side=tk.LEFT, padx=(0, 5))
    
    custom_var = tk.StringVar(value="45")
    custom_entry = ttk.Entry(custom_frame, textvariable=custom_var, width=5)
    custom_entry.pack(side=tk.LEFT)
    custom_entry.configure(state="disabled")
    
    ttk.Label(custom_frame, text="minutes").pack(side=tk.LEFT, padx=5)
    
    def toggle_custom_entry():
        if custom_check_var.get():
            custom_entry.configure(state="normal")
        else:
            custom_entry.configure(state="disabled")
    
    # Rewards info
    rewards_frame = ttk.LabelFrame(main_frame, text="Potential Rewards")
    rewards_frame.pack(fill=tk.X, pady=10)
    
    rewards_text = (
        "• 1 point per 15 minutes completed\n"
        "• Bonus achievement for long sessions\n"
        "• Enhanced rank progression\n"
        "• Satisfaction of deep work"
    )
    
    rewards_label = ttk.Label(
        rewards_frame,
        text=rewards_text,
        justify=tk.LEFT,
        padding=10
    )
    rewards_label.pack(fill=tk.X)
    
    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=15)
    
    cancel_button = ttk.Button(
        button_frame,
        text="Cancel",
        command=dialog.destroy
    )
    cancel_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    
    start_button = ttk.Button(
        button_frame,
        text="Start Intensive Mode",
        command=lambda: start_intensive_mode()
    )
    start_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    
    def start_intensive_mode():
        duration = 0
        if custom_check_var.get():
            try:
                duration = int(custom_var.get())
                if duration <= 0 or duration > 360:  # Max 6 hours
                    raise ValueError("Invalid duration")
            except ValueError:
                messagebox.showerror(
                    "Invalid Duration", 
                    "Please enter a valid duration between 1 and 360 minutes."
                )
                return
        else:
            duration = duration_var.get()
        
        # Calculate potential points
        points = duration // 15
        
        # Confirm start
        result = messagebox.askyesno(
            "Start Intensive Mode",
            f"You're about to start an Intensive Mode session for {duration} minutes.\n\n"
            f"You'll earn {points} points if you complete the full duration.\n\n"
            "Ready to begin?",
            parent=dialog
        )
        
        if result:
            callback(duration)
            dialog.destroy()
    
    # Wait for the dialog to close
    parent.wait_window(dialog)


class IntensiveModeTimer(tk.Frame):
    """A widget that displays the time remaining in intensive mode"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.active = False
        self.end_time = None
        self.update_interval = 1000  # Update every second
        self.after_id = None
        
        # Timer display
        self.timer_var = tk.StringVar(value="")
        self.timer_label = ttk.Label(
            self,
            textvariable=self.timer_var,
            font=("Helvetica", 10, "bold")
        )
        self.timer_label.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        self.stop_button = ttk.Button(
            self,
            text="Stop",
            command=self._stop_pressed,
            width=8
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.pack_forget()  # Hide initially
        
        self.stop_callback = None
    
    def start(self, duration_minutes, stop_callback=None):
        """Start the intensive mode timer"""
        self.active = True
        self.end_time = datetime.now() + timedelta(minutes=duration_minutes)
        self.stop_callback = stop_callback
        
        # Show the stop button
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Update the timer
        self._update_timer()
    
    def stop(self):
        """Stop the timer"""
        self.active = False
        self.timer_var.set("")
        self.stop_button.pack_forget()
        
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
    
    def _update_timer(self):
        """Update the timer display"""
        if not self.active or not self.end_time:
            return
        
        remaining = self.end_time - datetime.now()
        
        # Check if timer has expired
        if remaining.total_seconds() <= 0:
            self.timer_var.set("Completed!")
            if self.stop_callback:
                self.stop_callback(completed=True)
            return
        
        # Format remaining time
        hours, remainder = divmod(remaining.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        self.timer_var.set(f"Remaining: {time_str}")
        
        # Schedule next update
        self.after_id = self.after(self.update_interval, self._update_timer)
    
    def _stop_pressed(self):
        """Handle stop button press"""
        result = messagebox.askyesno(
            "Stop Intensive Mode",
            "Are you sure you want to stop Intensive Mode?\n\n"
            "You won't receive rewards if you stop before completion.",
            parent=self.winfo_toplevel()
        )
        
        if result and self.stop_callback:
            self.stop_callback(completed=False)
