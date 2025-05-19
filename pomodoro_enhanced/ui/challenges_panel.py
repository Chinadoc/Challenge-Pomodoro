"""
Challenges UI panel for the Pomodoro Timer
Displays active challenges and progress in a visually appealing way
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class ChallengeCard(ttk.Frame):
    """A card widget that displays a single challenge with its progress"""
    
    def __init__(self, parent, challenge, **kwargs):
        """
        Initialize a challenge card
        
        Args:
            parent: Parent widget
            challenge: Challenge data dictionary
            **kwargs: Additional keyword arguments for the frame
        """
        super().__init__(parent, **kwargs)
        
        self.challenge = challenge
        
        # Configure style
        self.configure(relief="raised", borderwidth=1, padding=8)
        
        # Title frame with challenge name and points
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, expand=True)
        
        # Challenge title
        if hasattr(challenge, 'title'):
            title = challenge.title
        elif isinstance(challenge, dict) and 'title' in challenge:
            title = challenge['title']
        else:
            title = 'Challenge'
            
        title_label = ttk.Label(
            title_frame, 
            text=title,
            font=("Helvetica", 11, "bold")
        )
        title_label.pack(side=tk.LEFT, anchor=tk.W)
        
        # Points indicator
        if hasattr(challenge, 'reward_points'):
            points = challenge.reward_points
        elif isinstance(challenge, dict) and 'reward_points' in challenge:
            points = challenge['reward_points']
        else:
            points = 0
            
        points_label = ttk.Label(
            title_frame,
            text=f"{points} pts",
            font=("Helvetica", 10),
        )
        points_label.pack(side=tk.RIGHT, anchor=tk.E)
        
        # Description
        if hasattr(challenge, 'description'):
            description = challenge.description
        elif isinstance(challenge, dict) and 'description' in challenge:
            description = challenge['description']
        else:
            description = ''
            
        desc_label = ttk.Label(
            self,
            text=description,
            wraplength=300,
            justify=tk.LEFT
        )
        desc_label.pack(fill=tk.X, pady=(5, 10), anchor=tk.W)
        
        # Progress section
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill=tk.X)
        
        # Add progress bar if applicable
        has_target = False
        if hasattr(challenge, 'target_value') and challenge.target_value is not None:
            has_target = True
            target = challenge.target_value
            progress = getattr(challenge, 'progress', 0)
        elif isinstance(challenge, dict) and 'target_value' in challenge and challenge['target_value'] is not None:
            has_target = True
            target = challenge['target_value']
            progress = challenge.get('progress', 0)
            
        if has_target:
            
            # Progress bar
            progress_bar = ttk.Progressbar(
                progress_frame,
                orient="horizontal",
                length=200,
                mode="determinate"
            )
            progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            
            # Set progress value (0-100)
            progress_percentage = min(100, (progress / target) * 100) if target > 0 else 0
            progress_bar["value"] = progress_percentage
            
            # Progress text
            progress_text = ttk.Label(
                progress_frame,
                text=f"{progress}/{target}"
            )
            progress_text.pack(side=tk.RIGHT)
        
        # Completion status
        if hasattr(challenge, 'completed'):
            completed = challenge.completed
        elif isinstance(challenge, dict) and 'completed' in challenge:
            completed = challenge['completed']
        else:
            completed = False
            
        if completed:
            status_label = ttk.Label(
                self,
                text="✓ Completed",
                foreground="green",
                font=("Helvetica", 10, "bold")
            )
            status_label.pack(anchor=tk.E, pady=(5, 0))
        
        # Add expiry info
        has_expiry = False
        if hasattr(challenge, 'expiry_date'):
            expiry_date = challenge.expiry_date
            has_expiry = True
        elif isinstance(challenge, dict) and 'expiry_date' in challenge:
            expiry_date = challenge['expiry_date']
            has_expiry = True
            
        if has_expiry:
            try:
                expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
                today = datetime.now()
                days_left = (expiry - today).days + 1
                
                expiry_text = f"Expires today" if days_left == 0 else f"Expires in {days_left} days"
                
                expiry_label = ttk.Label(
                    self,
                    text=expiry_text,
                    font=("Helvetica", 8),
                    foreground="gray"
                )
                expiry_label.pack(anchor=tk.W, pady=(5, 0))
            except Exception:
                pass


def show_challenges_window(parent, challenges, points=0, callback=None):
    """
    Display a window showing all active challenges
    
    Args:
        parent: Parent tkinter window
        challenges: List of challenge dictionaries
        points: Total points accumulated
        callback: Optional callback when window is closed
    """
    dialog = tk.Toplevel(parent)
    dialog.title("Daily Challenges")
    dialog.geometry("400x500")
    dialog.minsize(350, 400)
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
    
    # Header with title and points
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill=tk.X, pady=(0, 15))
    
    title_label = ttk.Label(
        header_frame, 
        text="Daily Challenges", 
        font=("Helvetica", 16, "bold")
    )
    title_label.pack(side=tk.LEFT)
    
    points_label = ttk.Label(
        header_frame,
        text=f"Total Points: {points}",
        font=("Helvetica", 12)
    )
    points_label.pack(side=tk.RIGHT)
    
    # Create scrollable frame for challenges
    container = ttk.Frame(main_frame)
    container.pack(fill=tk.BOTH, expand=True)
    
    canvas = tk.Canvas(container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Sort challenges - completed ones at the bottom
    active_challenges = [c for c in challenges if not c.get('completed', False)]
    completed_challenges = [c for c in challenges if c.get('completed', False)]
    sorted_challenges = active_challenges + completed_challenges
    
    # Display challenges
    if not sorted_challenges:
        no_challenges_label = ttk.Label(
            scrollable_frame,
            text="No active challenges. New challenges will appear tomorrow!",
            font=("Helvetica", 11),
            padding=20,
            wraplength=300,
            justify=tk.CENTER
        )
        no_challenges_label.pack(pady=50)
    else:
        for challenge in sorted_challenges:
            challenge_card = ChallengeCard(scrollable_frame, challenge)
            challenge_card.pack(fill=tk.X, pady=5, padx=5)
    
    # Footer with buttons
    footer_frame = ttk.Frame(main_frame)
    footer_frame.pack(fill=tk.X, pady=(15, 0))
    
    close_button = ttk.Button(
        footer_frame,
        text="Close",
        command=dialog.destroy
    )
    close_button.pack(side=tk.RIGHT)
    
    # Set callback on close if provided
    if callback:
        dialog.protocol("WM_DELETE_WINDOW", lambda: on_close())
        
        def on_close():
            callback()
            dialog.destroy()
    
    # Wait for the dialog to close
    parent.wait_window(dialog)


def create_mini_challenge_display(parent, challenge, fg_color="#000000", bg_color="#FFFFFF"):
    """
    Create a compact challenge display for the main UI
    
    Args:
        parent: Parent widget
        challenge: Challenge dictionary
        fg_color: Foreground color for text
        bg_color: Background color
    
    Returns:
        Frame containing the challenge display
    """
    frame = ttk.Frame(parent)
    
    # Challenge name with progress
    if challenge.get('target_value') is not None:
        progress = challenge.get('progress', 0)
        target = challenge.get('target_value', 1)
        progress_text = f"{progress}/{target} - "
    else:
        progress_text = ""
    
    description = challenge.get('description', 'Challenge')
    points = challenge.get('reward_points', 0)
    
    challenge_text = f"{progress_text}{description} ({points} pts)"
    
    challenge_label = ttk.Label(
        frame,
        text=challenge_text,
        wraplength=350
    )
    challenge_label.pack(side=tk.LEFT, anchor=tk.W, pady=2)
    
    return frame
