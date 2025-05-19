"""
Intensive Mode module for Pomodoro Timer
Provides extended focus sessions with enhanced rewards
"""

from datetime import datetime, timedelta

class IntensiveMode:
    """
    Manages intensive work sessions where users commit to longer periods
    of focused work with enhanced rewards upon completion
    """
    
    def __init__(self, callback=None):
        """Initialize intensive mode tracker"""
        self.active = False
        self.start_time = None
        self.end_time = None
        self.duration_minutes = 0
        self.update_callback = callback
        self.timer_id = None
    
    def start(self, duration_minutes):
        """Start intensive mode for the specified duration"""
        if duration_minutes <= 0:
            return False
        
        self.active = True
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        self.duration_minutes = duration_minutes
        return True
    
    def stop(self, completed=False):
        """Stop intensive mode and calculate rewards if completed"""
        if not self.active:
            return False, 0
        
        self.active = False
        rewards = 0
        
        if completed:
            # Calculate rewards based on time spent
            # 1 point per 15 minutes completed
            rewards = self.duration_minutes // 15
        
        return completed, rewards
    
    def get_time_remaining(self):
        """Calculate time remaining in intensive mode"""
        if not self.active or not self.end_time:
            return 0
        
        remaining = self.end_time - datetime.now()
        return max(0, remaining.total_seconds())
    
    def is_completed(self):
        """Check if intensive mode is completed based on time"""
        if not self.active:
            return False
        
        return datetime.now() >= self.end_time
    
    def format_time_remaining(self):
        """Format the remaining time for display"""
        if not self.active:
            return ""
        
        seconds_remaining = self.get_time_remaining()
        if seconds_remaining <= 0:
            return "00:00:00"
        
        hours, remainder = divmod(seconds_remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def get_intensive_mode_durations():
    """Return standard options for intensive mode durations"""
    return [
        ("30 minutes", 30),
        ("1 hour", 60),
        ("2 hours", 120), 
        ("3 hours", 180)
    ]
