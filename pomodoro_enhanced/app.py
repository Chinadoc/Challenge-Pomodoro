"""Main application entry point for the Enhanced Pomodoro Timer."""

import logging
import sys
from pathlib import Path
import tkinter as tk

# Set up logging before other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pomodoro.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Initialize and run the application."""
    try:
        # Import here to avoid circular imports
        from .ui.main_window import MainWindow
        from .core.theme import theme_manager
        from .core.settings import TimerSettings
        
        # Initialize root window
        root = tk.Tk()
        root.title("Enhanced Pomodoro Timer")
        
        # Load settings
        settings_path = Path("settings.json")
        settings = TimerSettings.load(settings_path)
        
        # Apply theme
        theme_manager.apply_theme(settings.theme)
        
        # Create and run main window
        app = MainWindow(root, settings)
        
        # Save settings on exit
        def on_closing():
            settings.save(settings_path)
            root.destroy()
            
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the application
        root.mainloop()
        
    except Exception as e:
        logger.critical("Unhandled exception in main loop", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
