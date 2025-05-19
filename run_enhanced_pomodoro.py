#!/usr/bin/env python3
"""
Enhanced Pomodoro Timer Application Launcher
Integrates all features including:
- Cosmic-themed rank system
- Daily challenges
- Work categories
- Intensive work mode
- Enhanced UI
"""

import os
import sys
import tkinter as tk
from pomodoro import PomodoroTimer

def check_dependencies():
    """Check that all required dependencies are installed"""
    try:
        import pygame
        import darkdetect
        print("Core dependencies verified.")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages: pip install pygame darkdetect")
        return False

def check_enhanced_features():
    """Check if enhanced features are available"""
    try:
        from pomodoro_enhanced.core.categories import CategoryManager
        from pomodoro_enhanced.core.intensive_mode import IntensiveMode
        from pomodoro_enhanced.core.challenges import ChallengeManager
        print("Enhanced features available.")
        return True
    except ImportError as e:
        print(f"Enhanced features not fully available: {e}")
        print("Some features may be limited.")
        return False

def setup_environment():
    """Setup environment variables and paths"""
    # Ensure directories exist
    os.makedirs(os.path.join(os.path.expanduser('~'), '.pomodoro_timer'), exist_ok=True)
    
    # Check for API keys if sound generation is needed
    if not os.path.exists('.env') and not os.environ.get('ELEVENLABS_API_KEY'):
        print("Notice: ElevenLabs API key not found. Custom voice synthesis will be unavailable.")
        print("To enable voice synthesis, create a .env file with ELEVENLABS_API_KEY=your_key")

def main():
    """Main entry point for the enhanced Pomodoro Timer"""
    print("Starting Enhanced Pomodoro Timer...")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check enhanced features
    enhanced_available = check_enhanced_features()
    
    # Setup environment
    setup_environment()
    
    try:
        # Initialize Tkinter
        root = tk.Tk()
        root.withdraw()  # Hide the main window initially
        
        # Create and start the Pomodoro Timer
        app = PomodoroTimer(root)
        
        # Start the main event loop
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting Pomodoro Timer: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
