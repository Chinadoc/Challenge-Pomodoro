"""
Challenge display components for the Pomodoro Timer
Provides UI components for showing challenges in the main application window
"""

import tkinter as tk
from tkinter import ttk

class MiniChallengeDisplay(ttk.Frame):
    """A compact widget for displaying challenge information in the main UI"""
    
    def __init__(self, parent, challenge, fg_color="#000000", bg_color="#FFFFFF", **kwargs):
        """
        Initialize a mini challenge display
        
        Args:
            parent: Parent widget
            challenge: Challenge dictionary with details to display
            fg_color: Foreground color for text
            bg_color: Background color
        """
        super().__init__(parent, **kwargs)
        
        self.challenge = challenge
        self.fg_color = fg_color
        self.bg_color = bg_color
        
        # Create the UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the challenge display widgets"""
        # Main frame with challenge info
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, expand=True)
        
        # Challenge description with icon
        description = self.challenge.get('description', 'Challenge')
        
        description_label = tk.Label(
            info_frame,
            text=description,
            font=("Helvetica", 10),
            fg=self.fg_color,
            bg=self.bg_color,
            anchor='w',
            justify=tk.LEFT
        )
        description_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Points indicator
        points = self.challenge.get('reward_points', 0)
        points_label = tk.Label(
            info_frame,
            text=f"{points} pts",
            font=("Helvetica", 9),
            fg=self.fg_color,
            bg=self.bg_color
        )
        points_label.pack(side=tk.RIGHT, padx=5)
        
        # Progress bar if applicable
        if 'target_value' in self.challenge and self.challenge['target_value'] is not None:
            progress_frame = ttk.Frame(self)
            progress_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
            
            progress = self.challenge.get('progress', 0)
            target = self.challenge.get('target_value', 1)
            
            # Create progress bar
            progress_bar = ttk.Progressbar(
                progress_frame,
                orient="horizontal",
                length=200,
                mode="determinate"
            )
            progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Calculate progress percentage
            progress_value = min(100, (progress / target) * 100) if target > 0 else 0
            progress_bar["value"] = progress_value
            
            # Progress text
            progress_text = tk.Label(
                progress_frame,
                text=f"{progress}/{target}",
                font=("Helvetica", 8),
                fg=self.fg_color,
                bg=self.bg_color
            )
            progress_text.pack(side=tk.LEFT, padx=5)
    
    def update(self, challenge=None):
        """Update the display with new challenge data"""
        if challenge:
            self.challenge = challenge
        
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Recreate widgets with updated data
        self._create_widgets()


def populate_challenges_frame(parent_frame, challenges, fg_color="#000000", bg_color="#FFFFFF"):
    """
    Add challenge displays to a parent frame
    
    Args:
        parent_frame: Frame to add challenge displays to
        challenges: List of challenge dictionaries
        fg_color: Foreground color for text
        bg_color: Background color
    
    Returns:
        List of created MiniChallengeDisplay widgets
    """
    # Clear any existing widgets
    for widget in parent_frame.winfo_children():
        widget.destroy()
    
    # If no challenges, show a message
    if not challenges:
        no_challenges_label = tk.Label(
            parent_frame,
            text="All daily challenges completed!",
            font=("Helvetica", 10, "italic"),
            fg=fg_color,
            bg=bg_color,
            pady=10
        )
        no_challenges_label.pack(fill=tk.X, expand=True)
        return []
    
    # Create display widgets for each challenge (up to 3)
    displays = []
    for challenge in challenges[:3]:
        display = MiniChallengeDisplay(
            parent_frame,
            challenge,
            fg_color,
            bg_color,
            padding=5
        )
        display.pack(fill=tk.X, pady=2)
        displays.append(display)
    
    return displays
