"""
Integration module for the Pomodoro Timer enhanced features
Connects the core features with the UI components
"""

import tkinter as tk
from tkinter import messagebox

# Import core modules
from pomodoro_enhanced.core.categories import CategoryManager
from pomodoro_enhanced.core.intensive_mode import IntensiveMode, get_intensive_mode_durations
from datetime import datetime

# Import UI components
from pomodoro_enhanced.ui.category_selector import show_category_selector
from pomodoro_enhanced.ui.intensive_mode_panel import show_intensive_mode_dialog, IntensiveModeTimer
from pomodoro_enhanced.ui.challenges_panel import show_challenges_window, create_mini_challenge_display


class FeatureIntegrator:
    """
    Integrates enhanced features into the main Pomodoro Timer application
    """
    
    def __init__(self, pomodoro_timer):
        """
        Initialize with a reference to the main PomodoroTimer instance
        
        Args:
            pomodoro_timer: The main PomodoroTimer instance to enhance
        """
        self.pomodoro = pomodoro_timer
        self.root = pomodoro_timer.root if hasattr(pomodoro_timer, 'root') else None
        self.preferences = pomodoro_timer.preferences if hasattr(pomodoro_timer, 'preferences') else None
        
        # Initialize components
        self.category_manager = CategoryManager(self.preferences)
        self.intensive_mode = IntensiveMode(self._update_intensive_display)
        
        # Store UI references
        self.ui_components = {}
    
    def init_category_system(self):
        """Initialize the work category system"""
        # Register the current category with the pomodoro timer
        current_category = self.pomodoro.current_category if hasattr(self.pomodoro, 'current_category') else "Work"
        self.category_manager.select_category(current_category)
        
        # Update category UI if it exists
        if hasattr(self.pomodoro, 'category_label'):
            self.pomodoro.category_label.config(text=f"Category: {current_category}")
    
    def init_intensive_mode(self):
        """Initialize the intensive mode feature"""
        # Create timer display if intensive mode is active
        if self.intensive_mode.active:
            self._update_intensive_display()
    
    def init_challenges_display(self):
        """Initialize the challenges mini display"""
        if hasattr(self.pomodoro, 'challenges_mini_frame') and hasattr(self.pomodoro, 'challenge_manager'):
            self._update_challenges_display()
    
    def register_ui_component(self, name, component):
        """Register a UI component for later reference"""
        self.ui_components[name] = component
    
    def show_category_selector(self):
        """Show the category selection dialog"""
        categories = self.category_manager.get_all_categories()
        current = self.category_manager.current_category
        
        show_category_selector(
            self.root, 
            categories, 
            current, 
            self._on_category_selected
        )
    
    def _on_category_selected(self, category_name):
        """Handle category selection"""
        self.category_manager.select_category(category_name)
        
        # Update category in pomodoro timer
        if hasattr(self.pomodoro, 'current_category'):
            self.pomodoro.current_category = category_name
        
        # Update UI
        if hasattr(self.pomodoro, 'category_label'):
            self.pomodoro.category_label.config(text=f"Category: {category_name}")
            
            # Add visual feedback
            if hasattr(self.pomodoro, 'primary_color'):
                self.pomodoro.category_label.config(fg=self.pomodoro.primary_color)
                # Reset back to normal color after 1 second
                self.root.after(1000, lambda: self.pomodoro.category_label.config(
                    fg=self.pomodoro.fg_color if hasattr(self.pomodoro, 'fg_color') else "#000000"
                ))
    
    def toggle_intensive_mode(self):
        """Toggle intensive mode on/off"""
        if not self.intensive_mode.active:
            show_intensive_mode_dialog(self.root, self._start_intensive_mode)
        else:
            if messagebox.askyesno(
                "End Intensive Mode",
                "Are you sure you want to end Intensive Mode? You won't receive rewards unless you complete the full duration."
            ):
                self._stop_intensive_mode(completed=False)
    
    def _start_intensive_mode(self, duration_minutes):
        """Start intensive mode with the specified duration"""
        if self.pomodoro.running and not self.pomodoro.on_break:
            result = messagebox.askyesno(
                "Session in Progress",
                "You're already in a work session. Do you want to restart and enter Intensive Mode?"
            )
            if not result:
                return
                
            # Reset the timer
            self.pomodoro.reset_timer()
        
        # Start intensive mode
        self.intensive_mode.start(duration_minutes)
        
        # Update UI
        if 'intensive_button' in self.ui_components:
            self.ui_components['intensive_button'].config(text="End Intensive Mode")
        
        # Start the pomodoro timer if not already running
        if hasattr(self.pomodoro, 'running') and not self.pomodoro.running:
            self.pomodoro.toggle_timer()
        
        # Show confirmation message
        messagebox.showinfo(
            "Intensive Mode Started",
            f"You've started an Intensive Mode session for {duration_minutes} minutes. "
            "Stay focused until the end to earn extra rewards!"
        )
    
    def _stop_intensive_mode(self, completed=False):
        """End intensive mode and calculate rewards"""
        if not self.intensive_mode.active:
            return
            
        # Stop the timer and get rewards
        success, rewards = self.intensive_mode.stop(completed)
        
        # Reset UI
        if 'intensive_button' in self.ui_components:
            self.ui_components['intensive_button'].config(text="Intensive Mode")
        
        if 'intensive_timer_label' in self.ui_components:
            self.ui_components['intensive_timer_label'].config(text="")
        
        # Award rewards if completed
        if completed and hasattr(self.pomodoro, 'challenge_manager'):
            self.pomodoro.challenge_manager.add_points(rewards)
            
            # Update points display if it exists
            if 'points_label' in self.ui_components:
                self.ui_components['points_label'].config(
                    text=f"Points: {self.pomodoro.challenge_manager.total_points}"
                )
            
            # Show completion message
            messagebox.showinfo(
                "Intensive Mode Completed",
                f"Congratulations! You've completed an Intensive Work session and earned {rewards} bonus points!"
            )
    
    def _update_intensive_display(self):
        """Update the intensive mode timer display"""
        if not self.intensive_mode.active:
            if 'intensive_timer_label' in self.ui_components:
                self.ui_components['intensive_timer_label'].config(text="")
            return
        
        # Format the time remaining
        time_remaining = self.intensive_mode.format_time_remaining()
        
        # Update the display
        if 'intensive_timer_label' in self.ui_components:
            self.ui_components['intensive_timer_label'].config(text=f"Remaining: {time_remaining}")
        
        # Check if completed
        if self.intensive_mode.is_completed():
            self._stop_intensive_mode(completed=True)
            return
        
        # Schedule next update
        if self.root:
            self.root.after(1000, self._update_intensive_display)
    
    def show_challenges(self):
        """Show the challenges window"""
        if hasattr(self.pomodoro, 'challenge_manager'):
            challenges = self.pomodoro.challenge_manager.get_active_challenges()
            points = getattr(self.pomodoro.challenge_manager, 'total_points', 0)
            
            show_challenges_window(
                self.root,
                challenges,
                points,
                self._update_challenges_display
            )
    
    def _update_challenges_display(self):
        """Update the mini challenges display"""
        if not hasattr(self.pomodoro, 'challenges_mini_frame') or not hasattr(self.pomodoro, 'challenge_manager'):
            return
            
        # Clear existing challenges display
        for widget in self.pomodoro.challenges_mini_frame.winfo_children():
            widget.destroy()
            
        # Get active challenges
        active_challenges = self.pomodoro.challenge_manager.get_active_challenges()
        
        if not active_challenges:
            # No challenges to display
            no_challenges_label = tk.Label(
                self.pomodoro.challenges_mini_frame,
                text="All daily challenges completed! New challenges tomorrow.",
                bg=self.pomodoro.bg_color if hasattr(self.pomodoro, 'bg_color') else "#FFFFFF",
                fg=self.pomodoro.fg_color if hasattr(self.pomodoro, 'fg_color') else "#000000",
                font=("Helvetica", 10, "italic"),
                pady=10
            )
            no_challenges_label.pack(fill=tk.X, expand=True)
            return
            
        # Display each challenge
        for idx, challenge in enumerate(active_challenges[:3]):  # Show at most 3 challenges
            challenge_frame = create_mini_challenge_display(
                self.pomodoro.challenges_mini_frame,
                challenge,
                self.pomodoro.fg_color if hasattr(self.pomodoro, 'fg_color') else "#000000",
                self.pomodoro.bg_color if hasattr(self.pomodoro, 'bg_color') else "#FFFFFF"
            )
            challenge_frame.pack(fill=tk.X, pady=2)
    
    def update_challenge_progress(self, challenge_type, value=1, conditions=None):
        """Update progress for challenges of the specified type"""
        if not hasattr(self.pomodoro, 'challenge_manager'):
            return
        
        # Check time-based conditions if not provided
        if conditions is None:
            conditions = {}
            
        if 'time' not in conditions:
            current_hour = datetime.now().hour
            if current_hour < 10:  # Before 10 AM
                conditions['time'] = {'before_hour': 10}
            elif current_hour >= 20:  # After 8 PM
                conditions['time'] = {'after_hour': 20}
        
        # Check day-based conditions if not provided
        if 'day' not in conditions:
            current_day = datetime.now().weekday()
            if current_day >= 5:  # Weekend (5=Saturday, 6=Sunday)
                conditions['day'] = {'weekend': True}
        
        # Add category condition if available
        if 'category' not in conditions and hasattr(self.pomodoro, 'current_category'):
            conditions['category'] = {'value': self.pomodoro.current_category}
        
        # Update progress
        try:
            completed_challenges = self.pomodoro.challenge_manager.update_challenge_progress(
                challenge_type, value, conditions
            )
            
            if completed_challenges and len(completed_challenges) > 0:
                # Notify user of completed challenges
                challenge_names = [c['description'] for c in completed_challenges]
                points_earned = sum(c['reward_points'] for c in completed_challenges)
                
                # Update points display if it exists
                if 'points_label' in self.ui_components:
                    total_points = getattr(self.pomodoro.challenge_manager, 'total_points', 0)
                    self.ui_components['points_label'].config(text=f"Points: {total_points}")
                
                # Show notification for completed challenges
                notification_text = "Challenges Completed:\n" + "\n".join(challenge_names)
                notification_text += f"\n\nYou earned {points_earned} points!"
                
                messagebox.showinfo("Challenge Completed!", notification_text)
                
                # Update challenges display
                self._update_challenges_display()
                
                return True
        except Exception as e:
            print(f"Error updating challenge progress: {e}")
        
        return False
