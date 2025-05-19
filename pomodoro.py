print("POMODORO.PY SCRIPT EXECUTION STARTED", flush=True)
import sys
print(f"Python version: {sys.version}", flush=True)

# Import core modules from pomodoro_enhanced
from pomodoro_enhanced.core.theme import ThemeManager
from pomodoro_enhanced.core.state import Phase  # Add Phase import to fix timer functionality

# Import configuration
try:
    from pomodoro_enhanced import config
    print("Successfully imported config from pomodoro_enhanced package")
except ImportError:
    print("Could not import config from pomodoro_enhanced package, using fallback values")
    # Define a fallback config
    class ConfigFallback:
        DEFAULT_WORK_DURATION_MIN = 25
        DEFAULT_SHORT_BREAK_MIN = 5
        DEFAULT_LONG_BREAK_MIN = 15
        DEFAULT_LONG_BREAK_INTERVAL = 4
        DEFAULT_SOUND_PACK = 'default'
        BACKGROUND_COLOR = '#0A0A0A'
        FOREGROUND_COLOR = '#E0E0E0'
        SURFACE_COLOR = '#1A1A1A'
        PRIMARY_COLOR = '#6A8759'
        SECONDARY_COLOR = '#8A6A59'
    config = ConfigFallback()

# Import logging utilities
try:
    from pomodoro_enhanced.utils.logging_utils import configure_logger, logger
    print("Successfully imported logging utilities from pomodoro_enhanced package")
except ImportError:
    print("Could not import logging utilities, using basic logging")
    import logging
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('pomodoro_timer')

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, Menu
import time
import json
import os
import darkdetect
from datetime import datetime, timedelta, date
import threading
from threading import Event, Thread
from enum import Enum
import tempfile
import random
import csv
import signal
import sys
import queue
import logging

# Import enhanced features
try:
    from pomodoro_enhanced.integrator import FeatureIntegrator
    from pomodoro_enhanced.core.challenges import ChallengeManager
    # Import MCP plugin manager
    from pomodoro_enhanced.integrations.mcp_plugins import MCPPluginManager, show_plugin_manager_window
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    print("Enhanced features not available. Some functionality will be limited.")
    ENHANCED_FEATURES_AVAILABLE = False
import logging
import pygame
import random
import threading
from dotenv import load_dotenv
load_dotenv()
try:
    from elevenlabs import set_api_key, generate
except ImportError:
    set_api_key = None
    generate = None

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import enhanced modules
from pomodoro_enhanced.ui.settings_panel import SettingsPanel
from pomodoro_enhanced.core.models import TimerSettings
from pomodoro_enhanced.core.notifications import NotificationManager
from pomodoro_enhanced.core.analytics import get_analytics_manager
from pomodoro_enhanced.core.preferences import PreferenceManager
from pomodoro_enhanced.core.i18n import set_language, _ as translate
from pomodoro_enhanced.core.ranks import get_rank_for_sessions, get_next_rank, calculate_rank_progress
from pomodoro_enhanced.core.challenges import ChallengeManager

class Achievement:
    def __init__(self, id, name, description, target, icon_filename, is_mystery=False, paywall=False):
        self.id = id
        self.name = name
        self.description = description
        self.target = target
        self.icon_filename = icon_filename
        self.is_mystery = is_mystery
        self.paywall = paywall
        self.unlocked = False

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tipwindow or not self.text: return
        x = event.x_root + 10
        y = event.y_root + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="#ffffe0", relief='solid', borderwidth=1, wraplength=200)
        label.pack()

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class PomodoroTimer:
    def __init__(self, root):
        print("INIT: Start of PomodoroTimer.__init__", flush=True)
        self.root = root
        # Do NOT deiconify/lift/focus_force yet; wait until UI is ready
        self.style = ttk.Style() # Initialize ttk.Style early
        self.preferences = PreferenceManager()
        
        # Initialize work categories
        self.current_category = "Work"
        self.category_stats = self.preferences.get('category_stats', {})

        # Initialize settings with default values
        try:
            self.settings = TimerSettings()
            logger.info("Settings initialized successfully.")
        except NameError as e:
            logger.critical(f"TimerSettings class is not defined: {e}")
            # Fallback to basic settings if TimerSettings is not available
            class EmergencySettings:
                work_duration = 25
                short_break_duration = 5
                long_break_duration = 15
                long_break_interval = 4
                auto_start_breaks = True
                auto_start_pomodoros = False
                notifications = True
                sound_enabled = True
                sound_pack = 'default'
                gamification_enabled = True
                daily_goal = 4
                dark_mode = True
                theme = 'default'
                language = 'en'
                categories = ['Work', 'Study', 'Personal']
            self.settings = EmergencySettings()
            logger.warning("Using emergency fallback settings")

        # Initialize sound manager
        try:
            from pomodoro_enhanced.core.audio import SoundManager, NullSoundManager
            sounds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
            os.makedirs(sounds_dir, exist_ok=True)
            
            self.sound_manager = SoundManager(
                pack=getattr(self.settings, 'sound_pack', 'default'),
                base_dir=sounds_dir,
                enabled=getattr(self.settings, 'sound_enabled', True)
            )
            logger.info("Using enhanced SoundManager for audio playback")
            self.sound_enabled = self.sound_manager._enabled
            
            # Initialize sound queue for backward compatibility
            self.sound_queue = queue.Queue()
            self.stop_sound_event = threading.Event()
            self.sound_thread = None
            
        except Exception as e:
            logger.error(f"Failed to initialize SoundManager: {e}")
            from pomodoro_enhanced.core.audio import NullSoundManager
            self.sound_manager = NullSoundManager()
            self.sound_enabled = False
            self.sound_queue = queue.Queue()
            self.stop_sound_event = threading.Event()
            self.sound_thread = None

        # Load settings from preferences (will override defaults with saved values)
        self.load_settings()

        # Initialize timer state
        self.on_break = False  # Initialize on_break attribute
        self.timer_running = False
        
        # Initialize colors before FSM and UI setup
        # Default colors (light theme)
        self.fg_color = '#212121'  # Default foreground color
        self.bg_color = '#f5f5f5'  # Default background color
        self.primary_color = '#4a90e2'  # Default primary color
        self.surface_color = '#ffffff'  # Default surface color
        self.button_active_bg = '#3a7bc8'  # Default active button background
        self.work_color = '#d32f2f'  # Dark red
        self.break_color = '#00796b'  # Dark teal
        self.secondary_color = '#ff9800'  # Orange
        self.button_bg = self.surface_color
        self.button_fg = self.fg_color
        
        # Initialize FSM for timer state management
        try:
            from pomodoro_enhanced.core.state import TimerFSM, Durations
            
            # Ensure all required settings are present
            if not hasattr(self.settings, 'daily_goal'):
                self.settings.daily_goal = 4  # Default value
            if not hasattr(self.settings, 'work_duration'):
                self.settings.work_duration = 25
            if not hasattr(self.settings, 'short_break_duration'):
                self.settings.short_break_duration = 5
            if not hasattr(self.settings, 'long_break_duration'):
                self.settings.long_break_duration = 15
            if not hasattr(self.settings, 'long_break_interval'):
                self.settings.long_break_interval = 4
            
            # Define the state change handler
            def _on_state_change(new_state):
                """Handle state changes from the FSM."""
                logger.info(f"State changed to: {new_state}")
                if hasattr(self, 'update_timer_display'):
                    self.update_timer_display()
                
                # Update UI based on the new state if UI elements exist
                if hasattr(self, 'status_label'):
                    if new_state == 'work':
                        self.status_label.config(text=translate("Time to focus!"))
                    elif new_state == 'short_break':
                        self.status_label.config(text=translate("Take a short break"))
                    elif new_state == 'long_break':
                        self.status_label.config(text=translate("Take a long break"))
            
            # Store the method as an instance attribute
            self._on_state_change = _on_state_change
            
            try:
                # Create FSM with correct durations (in seconds):
                # Note: The Durations class may expect minutes, but we're passing seconds directly
                # to ensure consistent units. We'll ensure this works with explicit debugging
                self.fsm = TimerFSM(
                    durations=Durations(
                        # Pass in minutes as expected by the FSM
                        work=self.settings.work_duration,
                        short_break=self.settings.short_break_duration,
                        long_break=self.settings.long_break_duration,
                        long_break_interval=self.settings.long_break_interval
                    ),
                    on_state_change=self._on_state_change
                )
                # Force the initial time_left to be 25 minutes (1500 seconds)
                self.time_left = self.settings.work_duration * 60
                logger.info("TimerFSM initialized successfully")
                
                # Initialize other timer-related attributes
                self.sessions_completed = 0
                self.total_work_time = 0
                self.total_break_time = 0
                self.daily_goal = self.settings.daily_goal
                self.daily_completed = 0
                self.weekly_goal = 5  # Default weekly goal
                self.weekly_completed = 0
                self.streak = 0
                self.last_session_date = None
                self.achievements = self.load_achievements() if hasattr(self, 'load_achievements') else {}
                
            except Exception as fsm_error:
                logger.error(f"Failed to initialize TimerFSM: {fsm_error}")
                raise fsm_error
            
        except Exception as e:
            logger.error(f"Failed to initialize TimerFSM: {e}")
            # Fallback to old state management
            logger.warning("Falling back to legacy timer state management")
            self.time_left = self.settings.work_duration * 60
            self.cycles_before_long_break = self.settings.long_break_interval
            self.pomodoro_count = 0
            self.timer_running = False
            self.paused = False
            self.on_break = False
            self.long_break_next = False
            self.start_time = None
            self.elapsed_time = 0
            self.pause_start = None
            self.pause_elapsed = 0
            self.sessions_completed = 0
            self.total_work_time = 0
            self.total_break_time = 0
            self.daily_goal = self.settings.daily_goal
            self.daily_completed = 0
            self.weekly_goal = 5
            self.weekly_completed = 0
            self.streak = 0
            self.last_session_date = None
            self.achievements = self.load_achievements()
            self.fsm = None  # Indicate FSM is not available # Changed from threading.Queue()
        self.stop_sound_event = Event()
        
        # Initialize challenge manager if enhanced features are available
        if ENHANCED_FEATURES_AVAILABLE:
            self.challenge_manager = ChallengeManager()
            # Initialize feature integrator
            self.feature_integrator = FeatureIntegrator(self)
            # Initialize MCP plugin manager
            self.plugin_manager = MCPPluginManager()
            # Initialize flags for enhanced features
            self.intensive_mode_active = False

        # Initialize with default settings object first
        try:
            self.settings = TimerSettings() 
        except NameError: # Fallback if TimerSettings class itself is somehow not defined/imported
            logger.critical("TimerSettings class is not defined. Using emergency fallback attributes.") # Changed print to logger
            # This is an emergency fallback, proper definition/import is required
            class EmergencySettings:
                work_duration = config.DEFAULT_WORK_DURATION_MIN
                short_break_duration = config.DEFAULT_SHORT_BREAK_MIN
                long_break_duration = config.DEFAULT_LONG_BREAK_MIN
                long_break_interval = config.DEFAULT_LONG_BREAK_INTERVAL
                auto_start_breaks = True
                auto_start_pomodoros = False
                notifications = True
                sound_enabled = True
                sound_pack = config.DEFAULT_SOUND_PACK # Use config default
                gamification_enabled = True
                daily_goal = 4
                dark_mode = True # This might also come from config if we have a system/app default
                theme = 'default' # This might also come from config
        self.time_left = self.work_duration # Default to work_duration
        
        self.root.withdraw()
        self.root.title(translate("Enhanced Pomodoro Timer")) # Translate title
        self.root.geometry("600x650")
        self.root.minsize(400, 550)

        # macOS specific window settings
        if sys.platform == 'darwin':
            self.root.tk.call('tk', 'scaling', 2.0)  # Better retina support
            self.root.resizable(True, True)

        # Initialize ThemeManager
        try:
            # Create a config object with theme colors
            class ThemeConfig:
                # Dark theme colors (default)
                BACKGROUND_COLOR = '#1e1e1e'
                FOREGROUND_COLOR = '#ffffff'
                SURFACE_COLOR = '#2d2d2d'
                PRIMARY_COLOR = '#0078d7'
                SECONDARY_COLOR = '#ff8c00'
                BUTTON_ACTIVE_BG = '#3c3c3c'
                WORK_COLOR = '#ff8a80'  # Reddish
                BREAK_COLOR = '#80cbc4'  # Teal
                
                # Light theme colors (with fallbacks)
                BACKGROUND_COLOR_LIGHT = '#f5f5f5'
                FOREGROUND_COLOR_LIGHT = '#212121'
                SURFACE_COLOR_LIGHT = '#ffffff'
                PRIMARY_COLOR_LIGHT = '#007bff'
                SECONDARY_COLOR_LIGHT = '#ff9800'
                BUTTON_ACTIVE_BG_LIGHT = '#e0e0e0'
                WORK_COLOR_LIGHT = '#d32f2f'  # Dark red
                BREAK_COLOR_LIGHT = '#00796b'  # Dark teal
            
            # Initialize ThemeManager
            self.theme_manager = ThemeManager(self.root, ThemeConfig())
            logger.info("ThemeManager initialized successfully.")
            
            # Apply initial theme based on system preference
            self.theme_manager.update_theme(dark_mode=getattr(self.settings, 'dark_mode', None))
            
        except Exception as e:
            logger.critical(f'Failed to initialize ThemeManager: {e}. Using emergency fallback colors.', exc_info=True)
            # Emergency fallback
            try:
                self.bg_color = config.BACKGROUND_COLOR if hasattr(config, 'BACKGROUND_COLOR') else '#0A0A0A'
                self.fg_color = config.FOREGROUND_COLOR if hasattr(config, 'FOREGROUND_COLOR') else '#E0E0E0'
                self.surface_color = config.SURFACE_COLOR if hasattr(config, 'SURFACE_COLOR') else '#1A1A1A'
                self.primary_color = config.PRIMARY_COLOR if hasattr(config, 'PRIMARY_COLOR') else '#6A8759'
                self.secondary_color = config.SECONDARY_COLOR if hasattr(config, 'SECONDARY_COLOR') else '#8A6A59'
                self.button_active_bg = '#303030'
                self.work_color = '#8A3324'
                self.break_color = '#336B8A'
                
                self.button_bg = self.surface_color 
                self.button_fg = self.primary_color
                
                if hasattr(self.root, 'configure') and self.bg_color:
                    self.root.configure(bg=self.bg_color)
                logger.info("Emergency fallback theme applied in __init__.")
            except Exception as e:
                logger.critical(f'Failed to apply emergency fallback theme: {e}')
                raise

        # Setup UI (now all dependent attributes have default values)
        self.setup_ui()
        print("INIT: UI setup completed.")
        # Now that UI is ready, show the window
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        print("DEBUG: Called deiconify/lift/focus_force on root window (after UI setup)", flush=True)

        # Load saved settings (will override defaults if present)
        self.load_settings()
        print("INIT: Settings loaded.")

        # Load saved state (will override defaults/settings-derived values if present)
        self.load_state()
        print("INIT: State loaded.")
        
    def toggle_timer(self):
        """Start or pause the timer based on current state."""
        logger.info("Toggle timer called")
        
        # Use FSM if available
        if hasattr(self, 'fsm') and self.fsm is not None:
            try:
                # ---- START ----
                if not self.timer_running and not self.paused:
                    logger.info("Starting timer with FSM")
                    self.timer_running = True
                    self.paused = False
                    self.start_time = time.time()
                    self.pause_elapsed = 0
                    self.action_button.config(text=translate("PAUSE"))
                    # Apply theme-based styling if available
                    if hasattr(self, 'theme'):
                        self.action_button.config(bg=self.theme['accent_warning'])
                    self.update_timer()
                    return
                
                # ---- PAUSE ----
                if self.timer_running and not self.paused:
                    logger.info("Pausing timer with FSM")
                    self.timer_running = False
                    self.paused = True
                    self.pause_start = time.time()
                    self.action_button.config(text=translate("RESUME"))
                    # Apply theme-based styling if available
                    if hasattr(self, 'theme'):
                        self.action_button.config(bg=self.theme['accent_success'])
                    return
                
                # ---- RESUME ----
                if self.paused:
                    logger.info("Resuming timer with FSM")
                    self.timer_running = True
                    self.paused = False
                    # accumulate time spent in pause
                    self.pause_elapsed += time.time() - self.pause_start
                    self.action_button.config(text=translate("PAUSE"))
                    # Apply theme-based styling if available
                    if hasattr(self, 'theme'):
                        self.action_button.config(bg=self.theme['accent_warning'])
                    self.update_timer()
            except Exception as e:
                logger.error(f"Error in toggle_timer with FSM: {e}")
                # Fall back to legacy timer control
                self._legacy_toggle_timer()
        else:
            # Use legacy timer control
            self._legacy_toggle_timer()
    
    def _legacy_toggle_timer(self):
        """Legacy method to toggle the timer state."""
        try:
            # ---- START ----
            if not self.timer_running and not self.paused:
                logger.info("Starting timer (legacy)")
                self.timer_running = True
                self.paused = False
                self.start_time = time.time()
                self.pause_elapsed = 0
                self.action_button.config(text=translate("PAUSE"))
                # Apply theme-based styling if available
                if hasattr(self, 'theme'):
                    self.action_button.config(bg=self.theme['accent_warning'])
                self.update_timer()
                return

            # ---- PAUSE ----
            if self.timer_running and not self.paused:
                logger.info("Pausing timer (legacy)")
                self.timer_running = False
                self.paused = True
                self.pause_start = time.time()
                self.action_button.config(text=translate("RESUME"))
                # Apply theme-based styling if available
                if hasattr(self, 'theme'):
                    self.action_button.config(bg=self.theme['accent_success'])
                return

            # ---- RESUME ----
            if self.paused:
                logger.info("Resuming timer (legacy)")
                self.timer_running = True
                self.paused = False
                # accumulate time spent in pause
                self.pause_elapsed += time.time() - self.pause_start
                self.action_button.config(text=translate("PAUSE"))
                # Apply theme-based styling if available
                if hasattr(self, 'theme'):
                    self.action_button.config(bg=self.theme['accent_warning'])
                self.update_timer()
        except Exception as e:
            logger.error(f"Error in legacy toggle_timer: {e}")
            # Display error to user
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Error: {str(e)[:50]}...")
                self.status_label.config(fg='red')
                
    def skip_session(self):
        """Skip the current pomodoro or break session."""
        logger.info("Skipping session")
        
        # Use FSM if available
        if hasattr(self, 'fsm') and self.fsm is not None:
            try:
                # Reset current phase and move to next
                if hasattr(self.fsm, 'phase'):
                    current_phase = self.fsm.phase
                    logger.info(f"Current phase: {current_phase}")
                    
                    # Advance to next phase
                    if hasattr(self.fsm, '_advance') and callable(self.fsm._advance):
                        self.fsm._advance()
                        logger.info(f"Advanced to phase: {self.fsm.phase}")
                        
                        # Update timer display
                        if hasattr(self, 'update_timer_display'):
                            self.update_timer_display()
                        
                        # Update UI based on the new state
                        if hasattr(self, 'status_label'):
                            if self.fsm.phase == 'work':
                                self.status_label.config(text=translate("Time to focus!"))
                            elif self.fsm.phase == 'short_break':
                                self.status_label.config(text=translate("Take a short break"))
                            elif self.fsm.phase == 'long_break':
                                self.status_label.config(text=translate("Take a long break"))
                    else:
                        logger.error("FSM does not have _advance method")
            except Exception as e:
                logger.error(f"Error in skip_session with FSM: {e}")
                # Fall back to legacy timer control
                self._legacy_skip_session()
        else:
            # Use legacy skip method
            self._legacy_skip_session()
    
    def _legacy_skip_session(self):
        """Legacy method to skip the current session."""
        try:
            # Reset timer for next session
            if self.on_break:
                # End break, start work
                self.on_break = False
                self.time_left = self.settings.work_duration * 60
                if hasattr(self, 'status_label'):
                    self.status_label.config(text=translate("Time to focus!"))
            else:
                # End work, start break
                self.on_break = True
                if self.pomodoro_count % self.cycles_before_long_break == 0:
                    # Long break
                    self.time_left = self.settings.long_break_duration * 60
                    if hasattr(self, 'status_label'):
                        self.status_label.config(text=translate("Take a long break"))
                else:
                    # Short break
                    self.time_left = self.settings.short_break_duration * 60
                    if hasattr(self, 'status_label'):
                        self.status_label.config(text=translate("Take a short break"))
                
                # Increment pomodoro count if completing work session
                self.pomodoro_count += 1
                if hasattr(self, 'cycles_label'):
                    self.cycles_label.config(text=f"{self.pomodoro_count}")
            
            # Reset timer state
            self.timer_running = False
            self.start_time = None
            self.pause_elapsed = 0
            self.pause_start = None
            
            # Update UI
            if hasattr(self, 'action_button'):
                self.action_button.config(text=translate("START"))
            self.update_timer_display()
        except Exception as e:
            logger.error(f"Error in legacy skip_session: {e}")
    
    def _start_reset_timer(self, event):
        """Start a timer to detect long press for reset."""
        if hasattr(self.root, 'after'):
            self.press_time = time.time()
            self.reset_check_id = self.root.after(1000, self._check_for_reset)
    
    def _stop_reset_timer(self, event):
        """Stop the reset timer if button is released quickly."""
        if hasattr(self, 'reset_check_id') and self.reset_check_id and hasattr(self.root, 'after_cancel'):
            self.root.after_cancel(self.reset_check_id)
            
            # If press was quick, treat as skip
            if hasattr(self, 'press_time') and time.time() - self.press_time < 1.0:
                self.skip_session()
    
    def _check_for_reset(self):
        """Check if button is still pressed after timeout - reset if so."""
        if hasattr(self, 'press_time') and time.time() - self.press_time >= 1.0:
            self._reset_timer()
    
    def _reset_timer(self):
        """Reset the timer to the beginning of the current session."""
        logger.info("Resetting timer")
        
        # Use FSM if available
        if hasattr(self, 'fsm') and self.fsm is not None:
            try:
                # Reset current phase without advancing
                if hasattr(self.fsm, 'reset_current_phase') and callable(self.fsm.reset_current_phase):
                    self.fsm.reset_current_phase()
                    logger.info(f"Reset current phase: {self.fsm.phase}")
                else:
                    # Fallback if reset_current_phase doesn't exist
                    if hasattr(self.fsm, 'phase'):
                        current_phase = self.fsm.phase
                        if current_phase == 'work':
                            self.fsm.seconds_left = self.settings.work_duration * 60
                        elif current_phase == 'short_break':
                            self.fsm.seconds_left = self.settings.short_break_duration * 60
                        elif current_phase == 'long_break':
                            self.fsm.seconds_left = self.settings.long_break_duration * 60
                
                # Update timer display
                if hasattr(self, 'update_timer_display'):
                    self.update_timer_display()
            except Exception as e:
                logger.error(f"Error in _reset_timer with FSM: {e}")
                # Fall back to legacy timer reset
                self._legacy_reset_timer()
        else:
            # Use legacy reset method
            self._legacy_reset_timer()
    
    def _legacy_reset_timer(self):
        """Legacy method to reset the timer."""
        try:
            # Reset timer for current session
            if self.on_break:
                if self.current_cycle > 0 and self.current_cycle % self.settings.long_break_interval == 0:
                    self.time_left = self.settings.long_break_duration * 60
                else:
                    self.time_left = self.settings.short_break_duration * 60
            else:
                self.time_left = self.settings.work_duration * 60
            
            # Reset timer state
            self.timer_running = False
            self.paused = False
            self.start_time = None
            self.pause_elapsed = 0
            self.pause_start = None
            
            # Update UI
            if hasattr(self, 'action_button'):
                self.action_button.config(text=translate("START"))
                if hasattr(self, 'theme'):
                    self.action_button.config(bg=self.theme['accent_success'])
            
            self.update_timer_display()
            
            # Play reset sound
            if hasattr(self, 'sound_manager') and hasattr(self.sound_manager, 'play'):
                self.sound_manager.play('reset')
        except Exception as e:
            logger.error(f"Error in legacy reset_timer: {e}")
        
        # Initialize Pygame Mixer for audio (after settings are loaded)
        # self.initialize_audio() 
        # self.start_sound_daemon()

        # Load streak data
        self.load_streak_data()
        print("INIT: Streak data loaded.")
        self.update_streak_data() # Update streak data after loading
        
        # Load rank data
        self.load_rank_data()
        print("INIT: Rank data loaded.")
        self.update_rank_display() # Update rank display after loading
        
        # Load challenge data
        self.load_challenges()
        print("INIT: Challenges loaded.")
        # Generate daily challenges if needed
        self.generate_daily_challenges()
        print("INIT: Daily challenges generated.")

        # Update UI displays with potentially loaded values
        self.update_timer_display()
        self.update_status_display()
        self.update_cycles_display()
        self.update_today_stats_display() 
        print("INIT: UI displays updated.")
        
        # Initialize enhanced features if available
        if ENHANCED_FEATURES_AVAILABLE and hasattr(self, 'feature_integrator'):
            try:
                # Register UI components with the integrator
                if hasattr(self, 'category_button'):
                    self.feature_integrator.register_ui_component('category_button', self.category_button)
                if hasattr(self, 'category_label'):
                    self.feature_integrator.register_ui_component('category_label', self.category_label)
                if hasattr(self, 'intensive_button'):
                    self.feature_integrator.register_ui_component('intensive_button', self.intensive_button)
                if hasattr(self, 'intensive_timer_label'):
                    self.feature_integrator.register_ui_component('intensive_timer_label', self.intensive_timer_label)
                if hasattr(self, 'points_label'):
                    self.feature_integrator.register_ui_component('points_label', self.points_label)
                
                # Initialize feature systems
                self.feature_integrator.init_category_system()
                self.feature_integrator.init_intensive_mode()
                self.feature_integrator.init_challenges_display()
                print("INIT: Enhanced features initialized.")
            except Exception as e:
                print(f"Error initializing enhanced features: {e}")

        # Bindings
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        if sys.platform == 'darwin':
            self.root.createcommand('::tk::mac::Quit', self.on_closing)

        print("INIT: About to deiconify root window...")
        self.root.deiconify() # Show the main window
        self.root.focus_force() # Try to bring window to front
        self.root.lift()
        print("INIT: Root window deiconified and focused.")

        # Apply initial theme colors to all UI elements after UI is setup and visible
        if hasattr(self, 'update_ui_colors') and callable(self.update_ui_colors):
            try:
                self.update_ui_colors()
                logger.info("Initial UI colors updated after __init__ and deiconify.")
            except Exception as e:
                logger.error(f"Error calling update_ui_colors during __init__: {e}", exc_info=True)
        else:
            logger.warning("update_ui_colors method not found or not callable during __init__ when expected.")

        # Define achievements with custom names and descriptions
        self.achievements = [
            Achievement("early_bird", 
                       translate("Early Bird"), 
                       translate("Complete a Pomodoro before 9 AM"),
                       1, 
                       os.path.join('assets', 'achievements', 'early_bird.png')),
                       
            Achievement("marathoner",
                       translate("Marathoner"),
                       translate("Complete 5+ Pomodoros in one day"),
                       5,
                       os.path.join('assets', 'achievements', 'marathoner.png')),
                       
            Achievement("weekend_warrior",
                       translate("Weekend Warrior"),
                       translate("Complete Pomodoros on both weekend days"),
                       4,
                       os.path.join('assets', 'achievements', 'weekend_warrior.png')),
                       
            Achievement("night_owl",
                       translate("Night Owl"),
                       translate("Complete a Pomodoro after 10 PM"),
                       1,
                       os.path.join('assets', 'achievements', 'night_owl.png')),
                       
            Achievement("perfect_week",
                       translate("Perfect Week"),
                       translate("Complete your daily Pomodoro goal every day for a week"),
                       7,
                       os.path.join('assets', 'achievements', 'perfect_week.png')),
                       
            Achievement("focused_mind",
                       translate("Focused Mind"),
                       translate("Complete a Pomodoro without any breaks"),
                       1,
                       os.path.join('assets', 'achievements', 'focused_mind.png')),
                       
            Achievement("quick_draw",
                       translate("Quick Draw"),
                       translate("Start a Pomodoro within 1 minute of the previous one"),
                       1,
                       os.path.join('assets', 'achievements', 'quick_draw.png')),
                       
            Achievement("balanced",
                       translate("Balanced"),
                       translate("Maintain a perfect 5-minute break between Pomodoros"),
                       3,
                       os.path.join('assets', 'achievements', 'balanced.png')),
                       
            Achievement("early_riser",
                       translate("Early Riser"),
                       translate("Complete a Pomodoro before 7 AM"),
                       1,
                       os.path.join('assets', 'achievements', 'early_riser.png')),
                       
            Achievement("power_hour",
                       translate("Power Hour"),
                       translate("Complete 4 consecutive Pomodoros with only short breaks"),
                       4,
                       os.path.join('assets', 'achievements', 'power_hour.png'))
        ]
        
        # Track achievement progress
        self.achievement_progress = {achievement.id: 0 for achievement in self.achievements}
        self.achievement_sounds = {achievement.id: os.path.join('assets', 'sounds', 'achievements', f"{achievement.id}.mp3") 
                                 for achievement in self.achievements}
        self.load_achievement_progress()

    def _update_theme_colors(self):
        """Update theme colors based on system or user preference."""
        if not hasattr(self, 'theme_manager'):
            logger.error("ThemeManager not initialized. Cannot update theme colors.")
            return
            
        try:
            # Get the current theme config
            theme_config = self.theme_manager.theme
            
            # Update colors from the theme
            self.bg_color = theme_config.bg
            self.fg_color = theme_config.fg
            self.surface_color = theme_config.surface
            self.primary_color = theme_config.primary
            self.secondary_color = theme_config.secondary
            self.button_active_bg = theme_config.button_active_bg
            self.work_color = theme_config.work
            self.break_color = theme_config.brk
            
            # Set derived colors
            self.button_bg = self.surface_color
            self.button_fg = self.primary_color
            
            # Apply to root window
            if hasattr(self.root, 'configure') and self.bg_color:
                self.root.configure(bg=self.bg_color)
                
            logger.info(f"Theme updated via ThemeManager: bg={self.bg_color}, fg={self.fg_color}")
            
        except Exception as e:
            logger.error(f'Error updating theme colors: {e}', exc_info=True)
            # Fall back to dark theme on error
            try:
                self.bg_color = '#0F172A'
                self.fg_color = '#F1F5F9'
                self.surface_color = '#1E293B'
                self.primary_color = '#9F7AEA'
                self.secondary_color = '#FBBF24'
                self.button_active_bg = '#3c3c3c'
                self.work_color = '#ff8a80'
                self.break_color = '#80cbc4'
                self.button_bg = self.surface_color
                self.button_fg = self.primary_color
                
                if hasattr(self.root, 'configure') and self.bg_color:
                    self.root.configure(bg=self.bg_color)
            except Exception as e:
                logger.critical(f'Critical error in theme fallback: {e}')
            logger.info("Internal fallback theme applied in _update_theme_colors.")
        
        # Regardless of success or failure in getting theme colors, attempt to apply them to UI elements
        if hasattr(self, 'update_ui_colors') and callable(self.update_ui_colors):
            try:
                self.update_ui_colors()
            except Exception as e:
                logger.error(f"Error calling update_ui_colors from _update_theme_colors: {e}", exc_info=True)

    def update_ui_colors(self):
        """Apply the current theme colors to all UI elements."""
        logger.info("Applying theme colors to UI elements.")
        
        # Ensure ThemeManager is initialized
        if not hasattr(self, 'theme_manager'):
            logger.error("ThemeManager not initialized. Cannot update UI colors.")
            return
            
        # Ensure self.style is initialized
        if not hasattr(self, 'style'):
            self.style = ttk.Style()
        
        # Get the current theme config
        theme_config = self.theme_manager.theme
        
        # Update local color variables
        self._update_theme_colors()
        
        # Create a dictionary of all widgets to style
        widgets_to_style = {
            # Root window
            'root': self.root if hasattr(self, 'root') else None,
            # Main containers
            'main_frame': self.main_frame if hasattr(self, 'main_frame') else None,
            # Labels
            'timer_label': self.timer_label if hasattr(self, 'timer_label') else None,
            'status_label': self.status_label if hasattr(self, 'status_label') else None,
            'category_label': self.category_label if hasattr(self, 'category_label') else None,
            'intensive_timer_label': self.intensive_timer_label if hasattr(self, 'intensive_timer_label') else None,
            'points_label': self.points_label if hasattr(self, 'points_label') else None,
            # Frames
            'controls_frame': self.controls_frame_ref if hasattr(self, 'controls_frame_ref') else None,
            'secondary_controls': self.secondary_controls_ref if hasattr(self, 'secondary_controls_ref') else None,
            'stats_button_frame': self.stats_button_frame_ref if hasattr(self, 'stats_button_frame_ref') else None,
            'daily_stats_frame': self.daily_stats_frame if hasattr(self, 'daily_stats_frame') else None,
            'advanced_controls_frame': self.advanced_controls_frame_ref if hasattr(self, 'advanced_controls_frame_ref') else None,
            'challenges_mini_display': self.challenges_mini_display if hasattr(self, 'challenges_mini_display') and self.challenges_mini_display else None,
        }
        
        # Apply theme colors to all widgets first as a base style
        for w, widget in widgets_to_style.items():
            if widget:
                try:
                    widget.configure(background=self.bg_color, foreground=self.fg_color)
                    logger.debug(f"DEBUG: {w} set to background={self.bg_color}, foreground={self.fg_color}")
                except Exception as e:
                    logger.debug(f"Could not update widget colors for {w}: {e}")
        
        # Force explicit high-contrast colors for critical UI elements
        critical_widgets = [
            ('timer_label', self.timer_label if hasattr(self, 'timer_label') else None),
            ('status_label', self.status_label if hasattr(self, 'status_label') else None),
            ('action_button', self.action_button if hasattr(self, 'action_button') else None),
            ('skip_reset_button', self.skip_reset_button if hasattr(self, 'skip_reset_button') else None),
            ('cycles_label', self.cycles_label if hasattr(self, 'cycles_label') else None)
        ]
        
        print("DEBUG: Applying explicit high-contrast colors to critical UI elements")
        for name, widget in critical_widgets:
            if widget:
                try:
                    if isinstance(widget, tk.Button):
                        # Buttons get bright, high-contrast colors
                        if name == 'action_button':
                            widget.configure(bg='#4CAF50', fg='#FFFFFF')  # Green with white text
                            print(f"DEBUG: {name} explicitly styled green/white")
                        else:
                            widget.configure(bg='#2196F3', fg='#FFFFFF')  # Blue with white text
                            print(f"DEBUG: {name} explicitly styled blue/white")
                    else:
                        # Labels get light background with dark text for readability
                        widget.configure(bg='#f5f5f5', fg='#000000')  # Light gray with black text
                        print(f"DEBUG: {name} explicitly styled lightgray/black")
                except Exception as e:
                    print(f"ERROR styling {name}: {e}")
                    logger.error(f"Could not apply explicit styling to {name}: {e}")
        # (Consider: In future, migrate all labels to ttk.Label for unified theming)
        
    def _configure_ttk_styles(self):
        """Configure ttk styles based on the current theme."""
        if not hasattr(self, 'style'):
            self.style = ttk.Style()
            
        # Configure general TButton style
        self.style.configure('TButton',
                           background=self.button_bg,
                           foreground=self.button_fg,
                           font=('Helvetica', 10),
                           relief=tk.FLAT)
                           
        self.style.map('TButton',
                      background=[('active', self.button_active_bg), ('pressed', self.button_active_bg)],
                      foreground=[('active', self.button_fg)])
                      
        # Configure primary button style
        self.style.configure('Primary.TButton',
                           background=self.primary_color,
                           foreground=self.fg_color,
                           font=('Helvetica', 10, 'bold'))
                           
        self.style.map('Primary.TButton',
                      background=[('active', self.button_active_bg)],
                      foreground=[('active', self.fg_color)])
        
        # Configure frame styles
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabelframe', background=self.bg_color)
        self.style.configure('TLabelframe.Label', background=self.bg_color, foreground=self.fg_color)
        
        # Configure label styles
        self.style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('Title.TLabel', font=('Helvetica', 14, 'bold'))
        
        # Configure entry styles
        self.style.configure('TEntry',
                           fieldbackground=self.surface_color,
                           foreground=self.fg_color,
                           insertcolor=self.fg_color)
        
        # Configure combobox styles
        self.style.map('TCombobox',
                      fieldbackground=[('readonly', self.surface_color)],
                      selectbackground=[('readonly', self.primary_color)],
                      selectforeground=[('readonly', self.fg_color)])
        
        # Configure notebook style
        self.style.configure('TNotebook', background=self.bg_color)
        self.style.configure('TNotebook.Tab',
                           background=self.surface_color,
                           foreground=self.fg_color,
                           padding=[10, 5])
        self.style.map('TNotebook.Tab',
                      background=[('selected', self.primary_color)],
                      foreground=[('selected', self.fg_color)])

        # Primary action button style
        if hasattr(self, 'primary_color') and hasattr(self, 'surface_color') and hasattr(self, 'button_active_bg'):
            # Assuming primary button uses primary_color as background
            # and a contrasting foreground (e.g. fg_color if light, or a specific on_primary_fg)
            on_primary_fg = self.fg_color # Default, might need adjustment based on primary_color brightness
            if self.primary_color.startswith('#') and len(self.primary_color) == 7:
                 #簡易的な輝度計算 (This is a very basic heuristic for contrast)
                r, g, b = int(self.primary_color[1:3], 16), int(self.primary_color[3:5], 16), int(self.primary_color[5:7], 16)
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                on_primary_fg = '#000000' if brightness > 128 else '#FFFFFF' 

            self.style.configure('Primary.TButton',
                                 font=('Helvetica', 12, 'bold'), 
                                 background=self.primary_color, 
                                 foreground=on_primary_fg,
                                 relief=tk.RAISED,
                                 borderwidth=2)
            self.style.map('Primary.TButton', 
                           background=[('active', self.button_active_bg), ('pressed', self.button_active_bg)],
                           foreground=[('active', on_primary_fg)])

    def load_sound_pack(self, pack_name):
        """Load a sound pack by name.
        
        Args:
            pack_name: Name of the sound pack to load
        """
        logger.info(f"Loading sound pack: {pack_name}")
        
        if not hasattr(self, 'sound_manager'):
            logger.warning("SoundManager not initialized, cannot load sound pack")
            return
        
        try:
            self.sound_manager.set_pack(pack_name)
            self.current_sound_pack = pack_name
            logger.info(f"Successfully loaded sound pack: {pack_name}")
            
            # Update settings if they exist
            if hasattr(self, 'settings'):
                self.settings.sound_pack = pack_name
                
        except FileNotFoundError:
            logger.warning(f"Sound pack not found: {pack_name}")
            # Fall back to default if available
            if pack_name != 'default':
                logger.info("Falling back to default sound pack")
                self.load_sound_pack('default')
        except Exception as e:
            logger.error(f"Error loading sound pack {pack_name}: {e}", exc_info=True)

    def start_sound_daemon(self):
        """Start the sound daemon (no-op with new SoundManager)."""
        logger.info("Sound daemon not needed with SoundManager")

    def play_sound_async(self, sound_key):
        """Play a sound asynchronously.
        
        Args:
            sound_key: The key of the sound to play (e.g., 'work_start', 'break_end')
        """
        if not hasattr(self, 'sound_manager') or not self.sound_enabled:
            return
        
        try:
            self.sound_manager.play(sound_key)
        except ValueError as e:
            logger.warning(f"Sound error: {e}")
        except Exception as e:
            logger.error(f"Error playing sound {sound_key}: {e}", exc_info=True)

    def load_settings(self):
        print("Attempting to load settings...")
        loaded_settings_dict = self.preferences.get('timer_settings', None)
        
        if loaded_settings_dict and isinstance(loaded_settings_dict, dict):
            # Ensure all expected fields for TimerSettings are present or provide defaults
            s_data = {
                'work_duration': loaded_settings_dict.get('work_duration', 25),
                'short_break_duration': loaded_settings_dict.get('short_break_duration', 5),
                'long_break_duration': loaded_settings_dict.get('long_break_duration', 15),
                'long_break_interval': loaded_settings_dict.get('long_break_interval', 4),
                'auto_start_breaks': loaded_settings_dict.get('auto_start_breaks', True),
                'auto_start_pomodoros': loaded_settings_dict.get('auto_start_pomodoros', False),
                'notifications': loaded_settings_dict.get('notifications', True),
                'sound_enabled': loaded_settings_dict.get('sound_enabled', True),
                'sound_pack': loaded_settings_dict.get('sound_pack', 'default'),
                'gamification_enabled': loaded_settings_dict.get('gamification_enabled', True),
                'daily_goal': loaded_settings_dict.get('daily_goal', 4),
                'dark_mode': loaded_settings_dict.get('dark_mode', True), 
                'theme': loaded_settings_dict.get('theme', 'default'),
                'language': loaded_settings_dict.get('language', 'en'), 
                'categories': loaded_settings_dict.get('categories', ['Work', 'Study', 'Personal'])
            }
            
            # Update settings object
            for key, value in s_data.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
            
            print(f"Settings loaded from preferences: {self.settings}")
        else:
            print("No saved settings found, using defaults")
        
        # Update timer durations
        self.work_duration = self.settings.work_duration * 60
        self.short_break_duration = self.settings.short_break_duration * 60
        self.long_break_duration = self.settings.long_break_duration * 60
        self.cycles_before_long_break = self.settings.long_break_interval
        
        # Update sound settings
        if hasattr(self, 'sound_manager') and hasattr(self.settings, 'sound_enabled'):
            self.sound_enabled = self.settings.sound_enabled
            self.sound_manager._enabled = self.sound_enabled
            
            # Load sound pack if specified and different from current
            if hasattr(self.settings, 'sound_pack'):
                current_pack = getattr(self.settings, 'sound_pack', 'default')
                if hasattr(self, 'current_sound_pack') and self.current_sound_pack != current_pack:
                    self.load_sound_pack(current_pack)
        
        # Update theme if needed
        if hasattr(self, 'update_ui_colors') and callable(self.update_ui_colors):
            try:
                self.update_ui_colors()
            except Exception as e:
                logger.error(f"Error updating UI colors in load_settings: {e}", exc_info=True)
        else:
            self.sound_enabled = True # Default value
            print("WARNING: 'sound_enabled' not found in TimerSettings, defaulting to True. Consider updating TimerSettings class.")
        
        self.notifications_enabled = getattr(self.settings, 'notifications', True)
        self.auto_start_work = getattr(self.settings, 'auto_start_pomodoros', False) # Note: name mismatch in TimerSettings? pomodoros vs work
        self.auto_start_break = getattr(self.settings, 'auto_start_breaks', True)
        self.gamification_enabled = getattr(self.settings, 'gamification_enabled', True)
        
        # Update sound pack if it has changed
        new_sound_pack = getattr(self.settings, 'sound_pack', 'classic')
        if hasattr(self, 'current_sound_pack') and self.current_sound_pack != new_sound_pack:
            self.current_sound_pack = new_sound_pack
            # Only reload the sound pack if audio is already initialized
            if hasattr(self, 'sounds'):
                print(f"SOUND: Reloading sound pack to: {new_sound_pack}")
                self.load_sound_pack(new_sound_pack)
        else:
            self.current_sound_pack = new_sound_pack
        self.language = getattr(self.settings, 'language', 'en') # Load language
        
        # Apply language setting
        set_language(self.language)
        print(f"Language set to: {self.language}")

    def load_state(self):
        print("Attempting to load state...")
        self.current_cycle = self.preferences.get('current_cycle', 0)
        self.on_break = self.preferences.get('on_break', False)
        self.paused = self.preferences.get('paused', False)
        self.total_work_time_today = timedelta(seconds=self.preferences.get('total_work_time_today_seconds', 0))

        if self.paused and self.preferences.get('time_left_on_pause') is not None:
            self.time_left = self.preferences.get('time_left_on_pause')
        elif self.on_break:
            if self.current_cycle > 0 and self.current_cycle % self.cycles_before_long_break == 0:
                self.time_left = self.long_break_duration
            else:
                self.time_left = self.short_break_duration
        else:
            self.time_left = self.work_duration
        print(f"State loaded: Time left: {self.time_left}, On break: {self.on_break}, Cycle: {self.current_cycle}")

    def load_streak_data(self):
        print("Attempting to load streak data...")
        default_streak = {'current_streak': 0, 'last_completed_date': None}
        loaded_streak = self.preferences.get('streak_data', default_streak)
        # Ensure loaded_streak is a dictionary with expected keys
        if not isinstance(loaded_streak, dict) or 'current_streak' not in loaded_streak or 'last_completed_date' not in loaded_streak:
            print(f"Warning: Invalid streak data found: {loaded_streak}. Resetting to default.")
            self.streak_data = default_streak
        else:
            self.streak_data = loaded_streak
        print(f"Streak data loaded: {self.streak_data}")

    def load_rank_data(self):
        print("Attempting to load rank data...")
        rank_data = self.preferences.get('rank_data', None)
        if rank_data:
            self.rank_data = rank_data
            print(f"Rank data loaded: {self.rank_data}")
        else:
            # Initialize with default values
            self.rank_data = {
                'current_rank_id': 'slacker',
                'total_sessions_completed': 0
            }
            print(f"Using default rank data: {self.rank_data}")

    def save_rank_data(self):
        print(f"Saving rank data: {self.rank_data}")
        self.preferences.set('rank_data', self.rank_data)

    def update_rank(self, session_completed=False):
        """Update the user's rank based on their completed sessions"""
        if session_completed:
            # Increment the total sessions completed
            self.rank_data['total_sessions_completed'] += 1
            self.today_stats['total_sessions_completed'] = self.rank_data['total_sessions_completed']

            # Get the current rank based on total sessions
            current_rank = get_rank_for_sessions(self.rank_data['total_sessions_completed'])
            self.rank_data['current_rank_id'] = current_rank.id

            # Save the updated rank data
            self.save_rank_data()

            # Update the rank display
            self.update_rank_display()

    def update_rank_display(self):
        """Update the UI to display the current rank and progress"""
        if hasattr(self, 'rank_label'):
            # Get current rank and next rank
            current_rank = get_rank_for_sessions(self.rank_data['total_sessions_completed'])
            next_rank = get_next_rank(self.rank_data['total_sessions_completed'])

            # Calculate progress toward next rank
            progress, remaining = calculate_rank_progress(self.rank_data['total_sessions_completed'])

            # Update rank label
            self.rank_label.config(text=f"Rank: {current_rank.name}")

            # Update rank progress label
            if next_rank:
                progress_text = f"Progress to {next_rank.name}: {progress:.0f}% ({remaining} sessions remaining)"
            else:
                progress_text = "Maximum rank achieved!"

            self.rank_progress_label.config(text=progress_text)

            # Update progress bar if available
            if hasattr(self, 'rank_progress_bar'):
                self.rank_progress_bar["value"] = progress

    def unlock_achievement(self, achievement_id):
        """Unlock an achievement and play its sound"""
        for achievement in self.achievements:
            if achievement.id == achievement_id and not achievement.unlocked:
                self.show_notification(
                    translate("Achievement Unlocked!"),
                    f"{achievement.name}: {achievement.description}",
                    duration=5000  # 5 seconds
                )
                return True
        return False

    def load_achievement_progress(self):
        """Load achievement progress from file"""
        try:
            save_file = os.path.join(os.path.dirname(__file__), 'achievements.json')
            if os.path.exists(save_file):
                with open(save_file, 'r') as f:
                    data = json.load(f)
                    for achievement_id, unlocked in data.items():
                        for achievement in self.achievements:
                            if achievement.id == achievement_id:
                                achievement.unlocked = unlocked
        except Exception as e:
            print(f"Error loading achievement progress: {e}")
    
    def save_achievement_progress(self):
        """Save achievement progress to file"""
        try:
            save_file = os.path.join(os.path.dirname(__file__), 'achievements.json')
            data = {achievement.id: achievement.unlocked for achievement in self.achievements}
            with open(save_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving achievement progress: {e}")

    def update_streak_data(self, session_started=False, session_completed=False, reset_streak=False):
        today = date.today().isoformat()
        
        if reset_streak:
            self.streak_data = {'current_streak': 0, 'last_completed_date': None}
            self.save_streak_data()
            print("UPDATE_STREAK_DATA: Streak reset.", flush=True)
            return

        if session_completed:
            # self.today_stats['pomodoros_completed'] += 1 # Already handled in run_timer
            # self.today_stats['work_time_seconds'] += self.settings.work_duration * 60 # Already handled in run_timer

            last_completed_iso = self.streak_data.get('last_completed_date')
            if last_completed_iso:
                last_completed_date = date.fromisoformat(last_completed_iso)
                if (date.today() - last_completed_date).days == 1:
                    self.streak_data['current_streak'] = self.streak_data.get('current_streak', 0) + 1
                    print(f"UPDATE_STREAK_DATA: Streak incremented to {self.streak_data['current_streak']}", flush=True)
                elif date.today() > last_completed_date:
                    self.streak_data['current_streak'] = 1 # Reset if not consecutive but completed today
                    print("UPDATE_STREAK_DATA: Streak reset to 1 (non-consecutive day).", flush=True)
                # If last_completed_date is today, streak already counted or is 1.
            else:
                self.streak_data['current_streak'] = 1 # First pomodoro ever or after a long break
                print("UPDATE_STREAK_DATA: Streak started at 1.", flush=True)
            
            self.streak_data['last_completed_date'] = today
            self.save_streak_data()
            self.save_today_stats() # Save today's stats as well

        # Update UI (will be called by update_all_displays or separately)
        # self.update_today_stats_display()
        # if hasattr(self, 'streak_label'): self.streak_label.config(text=f"Streak: {self.streak_data['current_streak']}")
        print(f"UPDATE_STREAK_DATA: Streak data: {self.streak_data}", flush=True)
        print(f"UPDATE_STREAK_DATA: Today's stats: {self.today_stats}", flush=True)

    def save_today_stats(self):
        print("SAVE_TODAY_STATS: Saving today_stats...", self.today_stats, flush=True)

    def save_settings(self):
        """Save current settings to preferences and update the application state."""
        print("Saving settings...")
        
        # Update sound settings in the settings object
        if hasattr(self, 'sound_manager'):
            self.settings.sound_enabled = self.sound_enabled
            if hasattr(self, 'current_sound_pack'):
                self.settings.sound_pack = self.current_sound_pack
        
        # Save all settings to preferences
        settings_dict = {
            'work_duration': self.settings.work_duration,
            'short_break_duration': self.settings.short_break_duration,
            'long_break_duration': self.settings.long_break_duration,
            'long_break_interval': self.settings.long_break_interval,
            'auto_start_breaks': self.settings.auto_start_breaks,
            'auto_start_pomodoros': self.settings.auto_start_pomodoros,
            'notifications': self.settings.notifications,
            'sound_enabled': self.settings.sound_enabled,
            'sound_pack': self.settings.sound_pack,
            'gamification_enabled': self.settings.gamification_enabled,
            'daily_goal': self.settings.daily_goal,
            'dark_mode': self.settings.dark_mode,
            'theme': self.settings.theme,
            'language': self.settings.language,
            'categories': self.settings.categories
        }
        
        self.preferences.set('timer_settings', settings_dict)
        
        # Update sound manager with new settings
        if hasattr(self, 'sound_manager'):
            self.sound_manager._enabled = self.settings.sound_enabled
            if hasattr(self.settings, 'sound_pack') and hasattr(self, 'current_sound_pack'):
                if self.settings.sound_pack != self.current_sound_pack:
                    self.load_sound_pack(self.settings.sound_pack)
        
        # Re-apply durations based on potentially new settings
        self.work_duration = self.settings.work_duration * 60
        self.short_break_duration = self.settings.short_break_duration * 60
        self.long_break_duration = self.settings.long_break_duration * 60
        self.cycles_before_long_break = self.settings.long_break_interval
        
        # Update UI
        self.update_timer_display()
        self.update_cycles_display()
        
        # Update theme if needed
        if hasattr(self, 'update_ui_colors') and callable(self.update_ui_colors):
            try:
                self.update_ui_colors()
            except Exception as e:
                logger.error(f"Error updating UI colors in save_settings: {e}", exc_info=True)

    def save_state(self):
        print("Saving state...")
        self.preferences.set('current_cycle', self.current_cycle)
        self.preferences.set('on_break', self.on_break)
        self.preferences.set('paused', self.paused)
        if self.paused:
            self.preferences.set('time_left_on_pause', self.time_left)
        else: # Clear it if not paused
            self.preferences.delete('time_left_on_pause')
        self.preferences.set('total_work_time_today_seconds', self.total_work_time_today.total_seconds())

    def save_streak_data(self):
        """Save streak data to preferences"""
        if hasattr(self, 'streak_data'):
            self.preferences.set('streak_data', self.streak_data)
            self.preferences.save()
    
    def load_challenges(self):
        """Load challenges from the challenge manager"""
        if not ENHANCED_FEATURES_AVAILABLE:
            print("Enhanced features not available, challenges not loaded")
            return
            
        try:
            if hasattr(self, 'challenge_manager'):
                challenges = self.preferences.get('challenges', None)
                challenge_points = self.preferences.get('challenge_points', 0)
                
                if challenges:
                    self.challenge_manager.challenges = challenges
                    self.challenge_manager.total_points = challenge_points
                    print(f"Loaded {len(challenges)} challenges with {challenge_points} total points")
                else:
                    # Generate initial challenges if none exist
                    self.generate_daily_challenges()
            else:
                print("Challenge manager not initialized")
        except Exception as e:
            print(f"Error loading challenge data: {e}")
    
    def generate_daily_challenges(self, count=3):
        """Generate daily challenges if needed"""
        if not ENHANCED_FEATURES_AVAILABLE:
            return []
            
        try:
            if hasattr(self, 'challenge_manager'):
                challenges = self.challenge_manager.generate_daily_challenges(count)
                print(f"Generated/loaded {len(challenges)} daily challenges")
                if hasattr(self, 'update_challenges_display'):
                    self.update_challenges_display()
                return challenges
            else:
                print("Challenge manager not initialized")
                return []
        except Exception as e:
            print(f"Error generating challenges: {e}")
            return []

    def format_timedelta(self, total_seconds):
        if total_seconds < 0:
            total_seconds = 0 # Ensure non-negative
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def update_today_stats_display(self):
        print("UPDATE_TODAY_STATS_DISPLAY: Called")
        try:
            completed = self.today_stats.get("pomodoros_completed", 0)
            total_seconds = self.today_stats.get("work_time_seconds", 0)
            
            # Convert seconds to hours:minutes
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            # Update labels
            if hasattr(self, 'completed_pomodoros_label'):
                self.completed_pomodoros_label.config(text=f"{translate('Completed Today')}: {completed}")
                print(f"  Updated completed_pomodoros_label: {translate('Completed Today')}: {completed}")
            if hasattr(self, 'total_work_time_label'):
                self.total_work_time_label.config(text=f"{translate('Work time today')}: {time_str}")
                print(f"  Updated total_work_time_label: {translate('Work time today')}: {time_str}")
            # Update progress bar if it exists
            if hasattr(self, 'progress_bar'):
                # Assuming a goal of 8 pomodoros per day for the progress bar
                progress = min(completed / 8 * 100, 100)
                self.progress_bar['value'] = progress
                print(f"  Updated progress_bar: {progress}% towards daily goal")
        except Exception as e:
            print(f"UPDATE_TODAY_STATS_DISPLAY ERROR: {str(e)}")

    def update_all_displays(self):
        print("UPDATE_ALL_DISPLAYS: Called. Updating timer, status, and stats displays.", flush=True)
        self.update_timer_display()
        self.update_status_display()
        self.update_today_stats_display()
        if hasattr(self, 'streak_label') and hasattr(self, 'streak_data'): 
            self.streak_label.config(text=f"{translate('Streak')}: {self.streak_data.get('current_streak', 0)}")
        if hasattr(self, 'cycles_label'): 
            self.cycles_label.config(text=self.get_cycles_display_text()) # Assuming get_cycles_display_text exists
        # pass # Removed redundant pass

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def update_timer_display(self):
        # Ensure time_left is valid and within reasonable limits
        # Work duration is typically 25 minutes = 1500 seconds, so anything beyond
        # 100 minutes (6000 seconds) is likely an error
        if hasattr(self, 'time_left') and self.time_left > 6000:
            logger.warning(f"Abnormal time_left value detected: {self.time_left} seconds. Resetting to 25 minutes.")
            self.time_left = self.settings.work_duration * 60  # Reset to default work duration
        
        # Convert total seconds to minutes:seconds format
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        # Debug output with correct time format
        print(f"UPDATE_TIMER_DISPLAY: Called. Time left: {time_str} ({minutes} min, {seconds} sec)", flush=True)
        
        # Update timer display label
        if hasattr(self, 'timer_label'):  # Check if timer_label exists
            # Set the timer display with proper minutes and seconds
            self.timer_label.config(text=time_str)
            
        # Update window title    
        if hasattr(self, 'root'): # Check if root exists
            self.root.title(f"{time_str} - {translate('Pomodoro Timer')}")
            
        # Update status based on timer state
        if hasattr(self, 'status_label'):
            if self.timer_running and not self.paused:
                if self.on_break:
                    self.status_label.config(text=f"{translate('Break time!')} ({time_str})")
                else:
                    self.status_label.config(text=f"{translate('Focus!')} ({time_str})")
            elif self.paused:
                self.status_label.config(text=f"{translate('Paused')} ({time_str})")
            else:  
                self.status_label.config(text=translate("Ready to start!"))

    def get_status_display_text(self):
        if self.quick_timer_active:
            return translate("Quick Timer")
        if self.on_break:
            if self.current_cycle % self.settings.long_break_interval == 0:
                return translate("Long Break")
            else:
                return translate("Short Break")
        else:
            return translate("Work")

    def update_status_display(self):
        print("UPDATE_STATUS_DISPLAY: Called", flush=True)
        # Update status label (e.g., Work, Break)
        if hasattr(self, 'status_label'):
            self.status_label.config(text=self.get_status_display_text())
        else:
            print("UPDATE_STATUS_DISPLAY: Warning, status_label not found.")

    def update_cycles_display(self):
        if hasattr(self, 'cycles_label'):
            self.cycles_label.config(text=self.get_cycles_display_text())

    def get_cycles_display_text(self):
        return f"{translate('Cycle')}: {self.current_cycle}/{self.cycles_before_long_break}"

    # UI Setup and Updates
    def setup_ui(self):
        try:
            # Set up a coherent theme across the application
            self.theme = {
                # Base colors
                'bg_dark': '#1E1E2E',      # Dark background
                'bg_medium': '#292D3E',    # Medium background for containers
                'bg_light': '#373B4D',     # Light background for elements
                'text_light': '#FFFFFF',   # Light text
                'text_muted': '#A6ACCD',   # Muted text
                'accent_main': '#89DDFF',  # Primary accent
                'accent_secondary': '#C792EA', # Secondary accent
                'accent_success': '#C3E88D',  # Success color
                'accent_warning': '#FFCB6B',  # Warning color
                'accent_error': '#FF5370',    # Error color
                'border': '#41485E'           # Border color
            }
            
            # Root window background
            self.root.configure(bg=self.theme['bg_dark'])
            print(f"DEBUG: Root configured with unified dark theme: {self.root.cget('bg')}")
            
            # Store theme colors for widgets
            self.bg_color = self.theme['bg_dark']
            self.fg_color = self.theme['text_light']

            # Main frame - using medium background from theme
            self.main_frame = tk.Frame(
                self.root, 
                bg=self.theme['bg_medium'],
                highlightbackground=self.theme['border'], 
                highlightthickness=1
            )
            self.main_frame.pack(expand=True, fill='both', padx=20, pady=20)
            print(f"DEBUG: main_frame packed with theme bg: {self.main_frame.cget('bg')}")
            
            # Timer display with enhanced visibility
            self.timer_label = tk.Label(
                self.main_frame,
                text="25:00",
                font=('Helvetica', 80, 'bold'),  # Larger size for better visibility
                fg='white',  # Pure white for maximum contrast
                bg='black',  # Black background for highest contrast
                padx=20,
                pady=10,
                relief=tk.SUNKEN,
                borderwidth=2
            )
            self.timer_label.pack(pady=40)
            print(f"DEBUG: timer_label packed with themed colors")
            
            # Status label with unified theme and improved visibility
            self.status_label = tk.Label(
                self.main_frame,
                text=translate("Ready to start!"),
                font=('Helvetica', 18, 'bold'),
                fg='white',   # Pure white for maximum contrast
                bg=self.theme['bg_dark'],    # Dark background for contrast
                padx=10,
                pady=5,
                relief=tk.RIDGE,
                borderwidth=1
            )
            self.status_label.pack(pady=10)
            print(f"DEBUG: status_label packed with themed colors")
            
            # Control buttons frame with unified theme
            controls_frame = tk.Frame(
                self.main_frame, 
                bg=self.theme['bg_light'],  # Light background for controls
                highlightbackground=self.theme['border'], 
                highlightthickness=1,
                width=400, 
                height=70
            )
            controls_frame.pack(pady=20, fill='x')
            print(f"DEBUG: controls_frame packed with themed colors")
            self.controls_frame_ref = controls_frame
            
            # Primary Action Button (START) with high-contrast styling
            self.action_button = tk.Button(
                self.controls_frame_ref,
                text=translate("START"),
                command=self.toggle_timer,
                font=('Helvetica', 14, 'bold'),  # Larger font
                bg='#00CC00',  # Bright green color
                fg='white',    # White text for contrast
                width=15, 
                height=2,
                relief=tk.RAISED,
                borderwidth=3,  # Thicker border
                cursor='hand2'  # Hand cursor on hover
            )
            self.action_button.pack(side='left', padx=10, pady=5)
            print(f"DEBUG: action_button packed with themed colors")
            
            # Secondary controls frame with theme colors
            secondary_controls = tk.Frame(
                self.controls_frame_ref, 
                bg=self.theme['bg_light'],
                width=200, 
                height=100
            )
            secondary_controls.pack(side=tk.LEFT, padx=5)
            print(f"DEBUG: secondary_controls packed with themed colors")
            self.secondary_controls_ref = secondary_controls
            
            # Skip/Reset Button with themed styling
            self.skip_reset_button = tk.Button(
                self.secondary_controls_ref,
                text=translate("Skip"),
                command=self.skip_session,
                font=('Helvetica', 10),
                bg=self.theme['accent_secondary'],  # Secondary accent color
                fg=self.theme['text_light'],       # Light text
                width=8,
                height=1,
                relief=tk.RAISED,
                borderwidth=1
            )
            self.skip_reset_button.pack(side=tk.TOP, pady=2)
            print(f"DEBUG: skip_reset_button packed with themed colors")
            
            # Stats Button Frame with theme styling
            stats_frame = tk.Frame(
                self.secondary_controls_ref, 
                bg=self.theme['bg_light'],
                width=100, 
                height=30
            )
            stats_frame.pack(side=tk.TOP, pady=2, fill='x')
            self.stats_button_frame_ref = stats_frame
            
            # Stats Button with theme styling
            self.stats_button = tk.Button(
                self.stats_button_frame_ref,
                text=translate("Stats"),
                command=self.show_statistics_window,
                width=10,
                bg=self.theme['accent_main'],    # Main accent color
                fg=self.theme['text_light'],     # Light text
                relief=tk.FLAT
            )
            self.stats_button.pack(side=tk.LEFT)
            
            # Settings Button with theme styling
            self.settings_button = tk.Button(
                self.secondary_controls_ref,
                text=translate("Settings"),
                command=self.open_settings_panel,
                width=10,
                bg=self.theme['accent_main'],    # Main accent color
                fg=self.theme['text_light'],     # Light text
                relief=tk.FLAT
            )
            self.settings_button.pack(side=tk.TOP, pady=2)
            
            # Cycles label with theme styling
            self.cycles_label = tk.Label(
                self.main_frame,
                text=f"{translate('Cycle')}: 0", 
                font=('Helvetica', 10),
                bg=self.theme['bg_medium'],     # Medium background
                fg=self.theme['text_muted']     # Muted text color
            )
            self.cycles_label.pack(pady=5)
            
            # Daily Stats Frame with theme styling
            daily_stats_frame = tk.Frame(
                self.main_frame, 
                bg=self.theme['bg_light'],
                highlightbackground=self.theme['border'], 
                highlightthickness=1
            )
            daily_stats_frame.pack(fill='x', padx=20, pady=10)
            self.daily_stats_frame = daily_stats_frame
            
            # RANK FRAME with theme styling
            self.rank_frame = tk.Frame(
                self.main_frame, 
                relief=tk.GROOVE, 
                bd=1, 
                bg=self.theme['bg_light'],
                highlightbackground=self.theme['border'], 
                highlightthickness=1
            )
            self.rank_frame.pack(fill=tk.X, pady=10, padx=10)
            
            # Rank Label with theme styling
            self.rank_label = tk.Label(
                self.rank_frame,
                text="Rank: Distracted Slacker",
                font=('Helvetica', 14, 'bold'),
                bg=self.theme['bg_light'],     # Light background
                fg=self.theme['accent_warning'] # Warning accent (gold)
            )
            self.rank_label.pack(pady=(10, 5))
            
            # Rank Progress Label with theme styling
            self.rank_progress_label = tk.Label(
                self.rank_frame,
                text="Progress to Focus Beginner: 0% (10 sessions remaining)",
                font=('Helvetica', 10),
                bg=self.theme['bg_light'],     # Light background
                fg=self.theme['text_light']    # Light text
            )
            self.rank_progress_label.pack(pady=(0, 5))
            
            # Rank Progress Bar with theme styling
            self.rank_progress_bar = ttk.Progressbar(
                self.rank_frame,
                orient=tk.HORIZONTAL,
                length=400,
                mode='determinate'
            )
            self.rank_progress_bar.pack(pady=(0, 10), padx=20, fill=tk.X)
            
            # Challenge header frame with theme styling
            challenge_header_frame = tk.Frame(
                self.main_frame, 
                bg=self.theme['bg_light'],
                highlightbackground=self.theme['border'], 
                highlightthickness=1
            )
            challenge_header_frame.pack(fill=tk.X, pady=(15, 5), padx=10)
            
            # Challenges title with theme styling
            challenges_title = tk.Label(
                challenge_header_frame,
                text=translate("Daily Challenges"),
                font=("Helvetica", 14, "bold"),
                bg=self.theme['bg_light'],     # Light background
                fg=self.theme['accent_main']   # Main accent
            )
            challenges_title.pack(side=tk.LEFT)
            
            # View Challenges button with theme styling
            self.view_challenges_button = tk.Button(
                challenge_header_frame,
                text=translate("View"),
                command=self.show_challenges_window,
                bg=self.theme['accent_main'],  # Main accent
                fg=self.theme['text_light'],   # Light text
                width=6,
                relief=tk.FLAT
            )
            self.view_challenges_button.pack(side=tk.RIGHT, padx=(0, 10))
            
            # Points label with theme styling
            self.points_label = tk.Label(
                challenge_header_frame,
                text=f"{translate('Points')}: 0",
                font=("Helvetica", 12),
                bg=self.theme['bg_light'],     # Light background
                fg=self.theme['accent_warning'] # Warning accent (gold)
            )
            self.points_label.pack(side=tk.RIGHT, padx=(0, 5))
            
            # Mini challenges display frame with improved styling
            self.challenges_mini_frame = tk.Frame(
                self.main_frame, 
                relief=tk.RIDGE,
                bd=2,
                height=120,  # Increased height for more space
                width=400,
                bg=self.theme['bg_medium'],         # Medium background
                highlightbackground=self.theme['accent_main'],  # Accent color for highlight
                highlightthickness=2  # Thicker highlight for visibility
            )
            self.challenges_mini_frame.pack(fill=tk.X, pady=10, padx=10)  # More padding
            
            # Add a sample challenge with enhanced icon styling
            sample_challenge = tk.Frame(self.challenges_mini_frame, bg=self.theme['bg_light'], bd=2, relief=tk.RAISED)
            sample_challenge.pack(fill=tk.X, padx=8, pady=8)
            
            # Create a circular frame for the trophy icon
            trophy_frame = tk.Frame(
                sample_challenge,
                bg=self.theme['accent_warning'],  # Warning accent (gold) background
                width=50,  # Wider frame
                height=50, # Taller frame
                highlightbackground=self.theme['accent_main'],
                highlightthickness=2
            )
            trophy_frame.pack_propagate(False)  # Don't shrink
            trophy_frame.pack(side=tk.LEFT, padx=10)
            
            # Place trophy icon in center of frame
            icon_label = tk.Label(
                trophy_frame, 
                text="🏆", 
                font=("Helvetica", 28),  # Even larger font
                bg=self.theme['accent_warning'],  # Match frame background
                fg="#FFFFFF"  # Pure white for maximum contrast
            )
            icon_label.pack(expand=True, fill='both')
            
            challenge_text = tk.Label(
                sample_challenge, 
                text="Complete 3 Pomodoro sessions", 
                font=("Helvetica", 12, "bold"),  # Bold font for better readability
                bg=self.theme['bg_light'], 
                fg=self.theme['text_light'],
                padx=10,  # More horizontal padding
                pady=8    # More vertical padding
            )
            challenge_text.pack(side=tk.LEFT, padx=10, fill='y')
            
            # Add another sample achievement with enhanced styling
            sample_achievement = tk.Frame(self.challenges_mini_frame, bg=self.theme['bg_light'], bd=2, relief=tk.RAISED)
            sample_achievement.pack(fill=tk.X, padx=8, pady=8)
            
            # Create a circular frame for the medal icon
            medal_frame = tk.Frame(
                sample_achievement,
                bg=self.theme['accent_secondary'],  # Secondary accent background
                width=50,  # Wider frame
                height=50, # Taller frame
                highlightbackground=self.theme['accent_main'],
                highlightthickness=2
            )
            medal_frame.pack_propagate(False)  # Don't shrink
            medal_frame.pack(side=tk.LEFT, padx=10)
            
            # Place medal icon in center of frame
            medal_label = tk.Label(
                medal_frame, 
                text="🥇", 
                font=("Helvetica", 28),  # Even larger font
                bg=self.theme['accent_secondary'],  # Match frame background
                fg="#FFFFFF"  # Pure white for maximum contrast
            )
            medal_label.pack(expand=True, fill='both')
            
            achievement_text = tk.Label(
                sample_achievement, 
                text="Early Bird: Started before 9am", 
                font=("Helvetica", 12, "bold"),  # Bold font for better readability
                bg=self.theme['bg_light'], 
                fg=self.theme['text_light'],
                padx=10,  # More horizontal padding
                pady=8    # More vertical padding
            )
            achievement_text.pack(side=tk.LEFT, padx=10, fill='y')

            # At the end of setup_ui, apply theme colors
            if hasattr(self, 'update_ui_colors') and callable(self.update_ui_colors):
                try:
                    self.update_ui_colors()
                    print("DEBUG: update_ui_colors called at end of setup_ui")
                except Exception as e:
                    logger.error(f"Error calling update_ui_colors during setup_ui: {e}", exc_info=True)
                    self.root.deiconify()
                    if hasattr(self, 'status_label'):
                        self.status_label.config(text=f"Error in setup_ui: {str(e)[:30]}...")
                        self.status_label.config(fg='red')
        except Exception as e:
            import traceback
            logger.error(f"Error in setup_ui: {e}")
            print(f"Error in setup_ui: {e}")
            traceback.print_exc()
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Error in setup_ui: {str(e)[:30]}...")
                self.status_label.config(fg='red')

            # Timer display already created above
            # (Removing duplicate timer_label declaration)
            
            # Status label
            self.status_label = tk.Label(
                self.main_frame,
                text=translate("Ready to start!"), # Translate
                font=('Helvetica', 18)
            )
            self.status_label.pack(pady=10)
            print("DEBUG: status_label packed")
            
            # Control buttons frame
            controls_frame = tk.Frame(self.main_frame)
            controls_frame.pack(pady=20)
            print("DEBUG: controls_frame packed")
            self.controls_frame_ref = controls_frame  # Store reference

            # Primary Action Button with EXPLICIT styling for maximum visibility
            self.action_button = tk.Button(
                self.controls_frame_ref,
                text=translate("START"),
                command=self.toggle_timer,
                font=('Helvetica', 12, 'bold'),
                bg='#4CAF50',  # Green background
                fg='#FFFFFF',  # White text
                width=15,
                height=2,
                relief=tk.RAISED,
                borderwidth=3
            )
            self.action_button.pack(side='left', padx=10, pady=5)
            print(f"DEBUG: action_button packed with fg={self.action_button.cget('fg')}, bg={self.action_button.cget('bg')}")
            
            # Use self.style (initialized in __init__) instead of local style
            self.style.configure('Primary.TButton', font=('Helvetica', 12, 'bold'))

            # Control Frame for secondary buttons
            secondary_controls = tk.Frame(self.controls_frame_ref)
            secondary_controls.pack(side=tk.LEFT, padx=5)
            print("DEBUG: secondary_controls packed")
            self.secondary_controls_ref = secondary_controls  # Store reference

            # Combined Skip/Reset Button with explicit styling
            self.skip_reset_button = tk.Button(
                self.secondary_controls_ref,
                text=translate("Skip"),
                command=self.skip_session,
                font=('Helvetica', 10),
                bg='#2196F3',  # Blue background
                fg='#FFFFFF',  # White text
                width=8,
                height=1,
                relief=tk.RAISED,
                borderwidth=2
            )
            self.skip_reset_button.pack(side=tk.TOP, pady=2)
            print(f"DEBUG: skip_reset_button packed with fg={self.skip_reset_button.cget('fg')}, bg={self.skip_reset_button.cget('bg')}")
            print("DEBUG: skip_reset_button packed")
            ToolTip(self.skip_reset_button, translate("Click to skip this session\nPress and hold to reset timer"))
            
            # Bind long press for reset
            self.skip_reset_button.bind("<ButtonPress-1>", self._start_reset_timer)
            self.skip_reset_button.bind("<ButtonRelease-1>", self._stop_reset_timer)
            self.reset_timer_id = None
            self.reset_pressed = False

            # Stats Button with indicator frame
            stats_frame = tk.Frame(self.secondary_controls_ref)
            stats_frame.pack(side=tk.TOP, pady=2)
            print("DEBUG: stats_frame packed")
            self.stats_button_frame_ref = stats_frame  # Store reference
            
            self.stats_button = ttk.Button(
                self.stats_button_frame_ref,  # Use reference
                text=translate("Stats"),
                command=self.show_statistics_window,
                width=10
            )
            self.stats_button.pack(side=tk.LEFT)
            print("DEBUG: stats_button packed")
            
            # Settings Button
            self.settings_button = ttk.Button(
                self.secondary_controls_ref,  # Use reference
                text=translate("Settings"),
                command=self.open_settings_panel,
                width=10
            )
            self.settings_button.pack(side=tk.TOP, pady=2)
            print("DEBUG: settings_button packed")
            
            # Cycles display at the bottom
            self.cycles_label = ttk.Label(self.main_frame, text=f"{translate('Cycle')}: 0", font=('Helvetica', 10))
            self.cycles_label.pack(pady=5)
            print("DEBUG: cycles_label packed")
            
            # Daily stats display
            self.daily_stats_frame = tk.Frame(self.main_frame)
            self.daily_stats_frame.pack(fill=tk.X, pady=5)
            
            # Create advanced controls frame
            advanced_controls = tk.Frame(self.main_frame, bg=self.bg_color)
            advanced_controls.pack(fill=tk.X, pady=10)
            self.advanced_controls_frame_ref = advanced_controls  # Store reference
            
            # Category button
            self.category_button = ttk.Button(
                self.advanced_controls_frame_ref,  # Use reference
                text=translate("Change Category"),
                command=self.show_category_selector,
                width=15
            )
            self.category_button.pack(side=tk.LEFT, padx=10)
            
            # Current category label
            self.category_label = tk.Label(
                self.advanced_controls_frame_ref,  # Use reference
                text=f"{translate('Category')}: Work",
                font=("Helvetica", 10),
                bg=self.bg_color,
                fg=self.fg_color
            )
            self.category_label.pack(side=tk.LEFT, padx=5)
            
            # Intensive mode button
            self.intensive_button = ttk.Button(
                self.advanced_controls_frame_ref,  # Use reference
                text=translate("Intensive Mode"),
                command=self.toggle_intensive_mode,
                width=15
            )
            self.intensive_button.pack(side=tk.RIGHT, padx=10)
            
            # Intensive mode timer label
            self.intensive_timer_label = tk.Label(
                self.advanced_controls_frame_ref,  # Use reference
                text="",
                font=("Helvetica", 10, "bold"),
                bg=self.bg_color,
                fg=self.secondary_color
            )
            self.intensive_timer_label.pack(side=tk.RIGHT, padx=5)

            # Completed Pomodoros Label
            self.completed_pomodoros_label = tk.Label(
                self.daily_stats_frame,  # Use renamed reference
                text=f"{translate('Completed Today')}: 0", 
                font=('Helvetica', 12), 
                bg=self.bg_color, 
                fg=self.fg_color
            )
            self.completed_pomodoros_label.grid(row=0, column=0, padx=10, sticky='w')

            # Total Work Time Label (was self.today_work_label)
            self.total_work_time_label = tk.Label(
                self.daily_stats_frame, 
                text=f"{translate('Work time today')}: 0m 0s", 
                font=('Helvetica', 12), 
                bg=self.bg_color, 
                fg=self.fg_color
            )
            self.total_work_time_label.grid(row=0, column=1, padx=10, sticky='e')

            self.streak_label = tk.Label(self.daily_stats_frame, text=f"{translate('Streak')}: 0 {translate('days')}", font=('Helvetica', 12), bg=self.bg_color, fg=self.fg_color)
            self.streak_label.grid(row=1, column=0, columnspan=2, padx=10)
            
            # Rank Display Frame
            self.rank_frame = tk.Frame(self.main_frame, bg=self.bg_color, relief=tk.GROOVE, bd=1)
            self.rank_frame.pack(fill=tk.X, pady=10, padx=10)
            
            # Daily Challenges Frame
            challenge_header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
            challenge_header_frame.pack(fill=tk.X, pady=(15, 5), padx=10)
            
            challenges_title = tk.Label(
                challenge_header_frame,
                text=translate("Daily Challenges"),
                font=("Helvetica", 14, "bold"),
                bg=self.bg_color,
                fg=self.primary_color
            )
            challenges_title.pack(side=tk.LEFT)
            
            # Add a View Challenges button
            self.view_challenges_button = ttk.Button(
                challenge_header_frame,
                text=translate("View"),
                command=self.show_challenges_window,
                width=6
            )
            self.view_challenges_button.pack(side=tk.RIGHT, padx=(0, 10))
            
            # Store reference to points_label so we can update it
            self.points_label = tk.Label(
                challenge_header_frame,
                text=f"{translate('Points')}: 0",
                font=("Helvetica", 12),
                bg=self.bg_color,
                fg=self.secondary_color
            )
            self.points_label.pack(side=tk.RIGHT, padx=(0, 5))
            
            # Mini challenges display frame
            self.challenges_mini_frame = tk.Frame(
                self.main_frame, 
                bg=self.bg_color,
                relief=tk.GROOVE,
                bd=1,
                height=100,
                width=400
            )
            self.challenges_mini_frame.pack(fill=tk.X, pady=5, padx=10)
            
            # Rank Label - shows current rank name
            self.rank_label = tk.Label(
                self.rank_frame,
                text="Rank: Distracted Slacker",
                font=('Helvetica', 14, 'bold'),
                bg=self.bg_color,
                fg=self.primary_color
            )
            self.rank_label.pack(pady=(10, 5))
            
            # Rank Progress Label - shows progress to next rank
            self.rank_progress_label = tk.Label(
                self.rank_frame,
                text="Progress to Focus Beginner: 0% (10 sessions remaining)",
                font=('Helvetica', 10),
                bg=self.bg_color,
                fg=self.fg_color
            )
            self.rank_progress_label.pack(pady=(0, 5))
            
            # Rank Progress Bar
            self.rank_progress_bar = ttk.Progressbar(
                self.rank_frame,
                orient=tk.HORIZONTAL,
                length=400,
                mode='determinate'
            )
            self.rank_progress_bar.pack(pady=(0, 10), padx=20, fill=tk.X)

            # Menu bar
            menubar = tk.Menu(self.root)
            # File menu
            filemenu = tk.Menu(menubar, tearoff=0)
            filemenu.add_command(label=translate("Settings"), command=self.open_settings_panel)
            filemenu.add_command(label=translate("View Stats"), command=self.show_statistics_window)
            filemenu.add_command(label=translate("Export Stats"), command=self.export_statistics)
            filemenu.add_command(label=translate("Import Stats"), command=self.import_statistics)
            if ENHANCED_FEATURES_AVAILABLE:
                filemenu.add_command(label=translate("MCP Plugin Manager"), command=self.show_plugin_manager)
            filemenu.add_separator()
            filemenu.add_command(label=translate("Exit"), command=self.on_closing)
            menubar.add_cascade(label=translate("File"), menu=filemenu)
            # Edit menu (macOS compliance)
            if sys.platform == 'darwin':
                editmenu = tk.Menu(menubar, name='apple', tearoff=0)
                menubar.add_cascade(label="Edit", menu=editmenu)
                # Add standard Edit menu items if needed, e.g., Copy, Paste
                # For now, it makes the app feel more native with an Edit menu

            # Advanced controls and related widgets
            self.advanced_controls_frame_ref = tk.Frame(self.main_frame)
            self.advanced_controls_frame_ref.pack(fill=tk.X, pady=10)
            self.category_button = ttk.Button(
                self.advanced_controls_frame_ref,
                text=translate("Change Category"),
                command=self.show_category_selector,
                width=15
            )
            self.category_button.pack(side=tk.LEFT, padx=10)
            self.category_label = tk.Label(
                self.advanced_controls_frame_ref,
                text=f"{translate('Category')}: Work",
                font=("Helvetica", 10)
            )
            self.category_label.pack(side=tk.LEFT, padx=5)
            self.intensive_button = ttk.Button(
                self.advanced_controls_frame_ref,
                text=translate("Intensive Mode"),
                command=self.toggle_intensive_mode,
                width=15
            )
            self.intensive_button.pack(side=tk.RIGHT, padx=10)
            self.intensive_timer_label = tk.Label(
                self.advanced_controls_frame_ref,
                text="",
                font=("Helvetica", 10, "bold")
            )
            self.intensive_timer_label.pack(side=tk.RIGHT, padx=5)
            self.completed_pomodoros_label = tk.Label(
                self.daily_stats_frame,
                text=f"{translate('Completed Today')}: 0",
                font=('Helvetica', 12)
            )
            self.completed_pomodoros_label.grid(row=0, column=0, padx=10, sticky='w')
            self.total_work_time_label = tk.Label(
                self.daily_stats_frame,
                text=f"{translate('Work time today')}: 0m 0s",
                font=('Helvetica', 12)
            )
            self.total_work_time_label.grid(row=0, column=1, padx=10, sticky='e')
            self.streak_label = tk.Label(self.daily_stats_frame, text=f"{translate('Streak')}: 0 {translate('days')}", font=('Helvetica', 12))
            self.streak_label.grid(row=1, column=0, columnspan=2, padx=10)
            self.rank_frame = tk.Frame(self.main_frame, relief=tk.GROOVE, bd=1)
            self.rank_frame.pack(fill=tk.X, pady=10, padx=10)
            challenge_header_frame = tk.Frame(self.main_frame)
            challenge_header_frame.pack(fill=tk.X, pady=(15, 5), padx=10)
            challenges_title = tk.Label(
                challenge_header_frame,
                text=translate("Daily Challenges"),
                font=("Helvetica", 14, "bold")
            )
            challenges_title.pack(side=tk.LEFT)
            self.view_challenges_button = ttk.Button(
                challenge_header_frame,
                text=translate("View"),
                command=self.show_challenges_window,
                width=6
            )
            self.view_challenges_button.pack(side=tk.RIGHT, padx=(0, 10))
            self.points_label = tk.Label(
                challenge_header_frame,
                text=f"{translate('Points')}: 0",
                font=("Helvetica", 12)
            )
            self.points_label.pack(side=tk.RIGHT, padx=(0, 5))
            self.challenges_mini_frame = tk.Frame(
                self.main_frame,
                relief=tk.GROOVE,
                bd=1,
                height=100,
                width=400
            )
            self.challenges_mini_frame.pack(fill=tk.X, pady=5, padx=10)
            self.rank_label = tk.Label(
                self.rank_frame,
                text="Rank: Distracted Slacker",
                font=('Helvetica', 14, 'bold')
            )
            self.rank_label.pack(pady=(10, 5))
            self.rank_progress_label = tk.Label(
                self.rank_frame,
                text="Progress to Focus Beginner: 0% (10 sessions remaining)",
                font=('Helvetica', 10)
            )
            self.rank_progress_label.pack(pady=(0, 5))
            self.rank_progress_bar = ttk.Progressbar(
                self.rank_frame,
                orient=tk.HORIZONTAL,
                length=400,
                mode='determinate'
            )
            self.rank_progress_bar.pack(pady=(0, 10), padx=20, fill=tk.X)
            
            # Menu bar
            menubar = tk.Menu(self.root)
            # File menu
            filemenu = tk.Menu(menubar, tearoff=0)
            filemenu.add_command(label=translate("Settings"), command=self.open_settings_panel)
            filemenu.add_command(label=translate("View Stats"), command=self.show_statistics_window)
            filemenu.add_command(label=translate("Export Stats"), command=self.export_statistics)
            filemenu.add_command(label=translate("Import Stats"), command=self.import_statistics)
            if ENHANCED_FEATURES_AVAILABLE:
                filemenu.add_command(label=translate("MCP Plugin Manager"), command=self.show_plugin_manager)
            filemenu.add_separator()
            filemenu.add_command(label=translate("Exit"), command=self.on_closing)
            menubar.add_cascade(label=translate("File"), menu=filemenu)
            # Edit menu (macOS compliance)
            if sys.platform == 'darwin':
                editmenu = tk.Menu(menubar, name='apple', tearoff=0)
                menubar.add_cascade(label="Edit", menu=editmenu)
                # Add standard Edit menu items if needed, e.g., Copy, Paste
                # For now, it makes the app feel more native with an Edit menu

            self.root.config(menu=menubar)
            
            # --- Force proper colors for main widgets at the end of setup_ui ---
            if hasattr(self, 'timer_label'):
                self.timer_label.config(fg=self.fg_color, bg=self.bg_color)
            if hasattr(self, 'status_label'):
                self.status_label.config(fg=self.fg_color, bg=self.bg_color)
            if hasattr(self, 'cycles_label'):
                self.cycles_label.config(foreground=self.fg_color, background=self.bg_color)
            
            # Apply styles
            self.apply_styles()
            print("DEBUG: setup_ui completed, all widgets should be visible")
            
            # Apply theme colors to all widgets after they are packed
            if hasattr(self, 'update_ui_colors') and callable(self.update_ui_colors):
                try:
                    self.update_ui_colors()
                    print("DEBUG: update_ui_colors called at end of setup_ui")
                except Exception as e:
                    logger.error(f"Error calling update_ui_colors during setup_ui: {e}", exc_info=True)
                    self.root.deiconify()
                    print("DEBUG: setup_ui completed, all widgets should be visible")
                    if hasattr(self, 'status_label'):
                        self.status_label.config(text=f"Error in setup_ui: {str(e)[:30]}...")
                        self.status_label.config(fg='red')
            
            # Update the timer display
            self.update_timer_display()
        
        # Schedule the next update if the timer is running
        if hasattr(self, 'timer_running') and self.timer_running and not self.paused:
            if hasattr(self.root, 'after'):
                self.timer_id = self.root.after(1000, self.update_timer)
    
    def _update_timer_with_fsm(self):
        """Update the timer using the FSM (Finite State Machine)."""
        if not hasattr(self, 'fsm') or self.fsm is None:
            logger.warning("FSM not initialized, falling back to legacy timer")
            return False
            
        # Don't update if paused
        if self.fsm.is_paused or self.fsm.state == Phase.PAUSED:
            return False
            
        # Update the FSM (this will handle the state transitions)
        phase_completed = self.fsm.tick(1)  # Tick with 1 second
        
        # Update the time left from the FSM
        # Ensure we're using the properly calculated seconds_left value
        if hasattr(self.fsm, 'seconds_left'):
            self.time_left = self.fsm.seconds_left
            # Debug output for FSM timer
            current_state = self.fsm.state.name if hasattr(self.fsm.state, 'name') else str(self.fsm.state)
            print(f"FSM_UPDATE: state={current_state}, time_left={self.time_left}s", flush=True)
        
        # Update the display
        self.update_timer_display()
        
        # If the phase completed, handle it
        if phase_completed:
            self.timer_completed()
            
        # Schedule the next update
        if hasattr(self.root, 'after'):
            self.timer_id = self.root.after(1000, self.update_timer)
            
        return True
    
    def update_timer(self):
        """Update the timer display and check if the current session has ended."""
        # First try to use FSM if available
        if hasattr(self, 'fsm') and self.fsm is not None:
            if self._update_timer_with_fsm():
                return
        
        # Fall back to legacy timer if FSM is not available or failed
        if not hasattr(self, 'timer_running') or not self.timer_running or not hasattr(self, 'time_left'):
            return

        current_time = time.time()
        elapsed = current_time - self.start_time - self.pause_elapsed
        
        # Determine the correct duration based on the current phase
        if self.on_break:
            if hasattr(self, 'current_cycle') and hasattr(self, 'cycles_before_long_break') and \
               self.current_cycle > 0 and self.current_cycle % self.cycles_before_long_break == 0:
                duration = self.long_break_duration  # Long break (already in seconds)
            else:
                duration = self.short_break_duration  # Short break (already in seconds)
        else:
            duration = self.work_duration  # Work duration (already in seconds)
        
        # Update time left based on correct duration
        self.time_left = max(0, duration - int(elapsed))
        
        # Debug output for troubleshooting
        print(f"UPDATE_TIMER: phase={'break' if self.on_break else 'work'}, elapsed={int(elapsed)}s, duration={duration}s, time_left={self.time_left}s", flush=True)
        
        # Update display
        self.update_timer_display()
        
        # Check if timer has reached zero
        if self.time_left <= 0:
            self.timer_completed()
        else:
            # Schedule next update
            if hasattr(self.root, 'after'):
                self.timer_id = self.root.after(1000, self.update_timer)
    
    def show_statistics_window(self):
        """Wrapper method to show the statistics window."""
        logger.info("Showing statistics window")
        try:
            self.show_statistics()
        except Exception as e:
            logger.error(f"Error showing statistics window: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Error loading statistics: {str(e)[:30]}...")
                self.status_label.config(fg='red')
    
    def export_statistics(self):
        """Export statistics to a JSON file."""
        logger.info("Exporting statistics to file")
        
        try:
            # Initialize statistics data if not present
            if not hasattr(self, 'statistics_data'):
                self.statistics_data = {
                    'daily_stats': {},
                    'total_pomodoros': 0,
                    'total_work_time': 0,
                    'total_break_time': 0,
                    'longest_streak': 0,
                    'current_streak': 0,
                    'categories': {},
                    'challenges': self.challenges if hasattr(self, 'challenges') else [],
                    'points': self.points if hasattr(self, 'points') else 0
                }
            
            # Get current date as string for default filename
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            # Ask user where to save the file
            import tkinter.filedialog as filedialog
            filename = filedialog.asksaveasfilename(
                initialdir=os.path.expanduser("~"),
                title=translate("Save Statistics"),
                initialfile=f"pomodoro_stats_{date_str}.json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not filename:  # User cancelled
                return
                
            # Add .json extension if not present
            if not filename.endswith('.json'):
                filename += '.json'
                
            # Convert statistics to JSON and save to file
            import json
            with open(filename, 'w') as f:
                json.dump(self.statistics_data, f, indent=2)
            
            # Show success message
            if hasattr(self, 'status_label'):
                self.status_label.config(text=translate(f"Statistics exported to {os.path.basename(filename)}"))
                
            logger.info(f"Statistics exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting statistics: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Error exporting statistics: {str(e)[:30]}...")
                self.status_label.config(fg='red')
                
    def import_statistics(self):
        """Import statistics from a JSON file."""
        logger.info("Importing statistics from file")
        
        try:
            # Ask user for the file to import
            import tkinter.filedialog as filedialog
            filename = filedialog.askopenfilename(
                initialdir=os.path.expanduser("~"),
                title=translate("Import Statistics"),
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not filename:  # User cancelled
                return
                
            # Load JSON data from file
            import json
            with open(filename, 'r') as f:
                imported_data = json.load(f)
                
            # Validate the imported data (basic checks)
            required_keys = ['daily_stats', 'total_pomodoros', 'total_work_time']
            if not all(key in imported_data for key in required_keys):
                raise ValueError("Invalid statistics file format")
                
            # Confirm with user
            import tkinter.messagebox as messagebox
            result = messagebox.askyesno(
                translate("Import Statistics"),
                translate("This will replace your current statistics. Continue?")
            )
            
            if not result:  # User cancelled
                return
                
            # Update statistics data
            self.statistics_data = imported_data
            
            # Update UI elements with new data
            if hasattr(self, 'points') and 'points' in imported_data:
                self.points = imported_data['points']
                
            if hasattr(self, 'challenges') and 'challenges' in imported_data:
                self.challenges = imported_data['challenges']
                
            if hasattr(self, 'points_label'):
                self.points_label.config(text=f"{translate('Points')}: {self.points}")
                
            # Show success message
            if hasattr(self, 'status_label'):
                self.status_label.config(text=translate(f"Statistics imported from {os.path.basename(filename)}"))
                
            logger.info(f"Statistics imported from {filename}")
            
        except Exception as e:
            logger.error(f"Error importing statistics: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Error importing statistics: {str(e)[:30]}...")
                self.status_label.config(fg='red')
                
    def apply_styles(self):
        """Apply styles to all UI elements."""
        logger.info("Applying UI styles")
        
        try:
            # Ensure theme colors are initialized
            if not hasattr(self, 'bg_color'):
                self._update_theme_colors()
                
            # Create ttk style object if it doesn't exist
            if not hasattr(self, 'style'):
                self.style = ttk.Style()
            
            # Configure the ttk styles with safe defaults
            bg_color = getattr(self, 'bg_color', '#f5f5f5')
            fg_color = getattr(self, 'fg_color', '#212121')
            surface_color = getattr(self, 'surface_color', '#e0e0e0')
            primary_color = getattr(self, 'primary_color', '#4a90e2')
            button_active_bg = getattr(self, 'button_active_bg', '#d0d0d0')
            
            self.style.configure('TFrame', background=bg_color)
            self.style.configure('Custom.TFrame', background=surface_color)
            
            # Button styles
            self.style.configure('TButton', 
                               background=surface_color,
                               foreground=fg_color,
                               font=('Helvetica', 10),
                               borderwidth=1)
            
            # Primary button style (for important actions)
            self.style.configure('Primary.TButton', 
                               background=primary_color, 
                               foreground='white',
                               font=('Helvetica', 12, 'bold'),
                               borderwidth=1)
            
            # Configure button hover/active states
            self.style.map('TButton',
                          background=[('active', button_active_bg)],
                          foreground=[('active', fg_color)])
            
            self.style.map('Primary.TButton',
                          background=[('active', button_active_bg)],
                          foreground=[('active', 'white')])
            
            # Label styles
            self.style.configure('TLabel', 
                               background=bg_color,
                               foreground=fg_color,
                               font=('Helvetica', 10))
            
            # Header label style
            self.style.configure('Header.TLabel', 
                               font=('Helvetica', 16, 'bold'))
            
            # Entry styles
            self.style.configure('TEntry', 
                               fieldbackground=surface_color,
                               foreground=fg_color)
            
            # Apply styles to main window if it exists
            if hasattr(self, 'root') and self.root:
                self.root.configure(bg=bg_color)
            
            # Apply styles to frames using a more robust approach
            for attr_name in dir(self):
                try:
                    if attr_name.endswith('_frame') and hasattr(self, attr_name):
                        frame = getattr(self, attr_name)
                        if frame and hasattr(frame, 'configure'):
                            frame.configure(bg=bg_color)
                except Exception as e:
                    logger.debug(f"Could not style frame {attr_name}: {e}")
            
            # Update specific widgets with their appropriate styles
            for widget_name in ['timer_display', 'status_label']:
                if hasattr(self, widget_name) and getattr(self, widget_name):
                    try:
                        getattr(self, widget_name).configure(bg=bg_color, fg=fg_color)
                    except Exception as e:
                        logger.debug(f"Could not style {widget_name}: {e}")
                
            # Style action button if it exists
            if hasattr(self, 'action_button') and self.action_button:
                try:
                    self.action_button.configure(style='Primary.TButton')
                except Exception as e:
                    logger.debug(f"Could not style action button: {e}")
                
            # Apply styles to other buttons
            standard_buttons = ['skip_reset_button', 'stats_button', 'settings_button', 'category_button']
            for btn_name in standard_buttons:
                if hasattr(self, btn_name) and getattr(self, btn_name):
                    try:
                        getattr(self, btn_name).configure(style='TButton')
                    except Exception as e:
                        logger.debug(f"Could not style button {btn_name}: {e}")
            
            logger.info("UI styles applied successfully")
            
        except Exception as e:
            logger.error(f"Error applying styles: {e}")
            print(f"Error applying styles: {e}")
    
    def on_closing(self):
        """Handle application closure, saving state and statistics."""
        logger.info("Application closing")
        
        try:
            # Save current state and statistics
            self.save_state()
            self.save_settings()
            
            # Stop any ongoing sounds
            if hasattr(self, 'sound_manager') and hasattr(self.sound_manager, 'stop_all'):
                self.sound_manager.stop_all()
                
            # Stop any running threads
            if hasattr(self, 'stop_sound_event'):
                self.stop_sound_event.set()
                
            if hasattr(self, 'sound_thread') and self.sound_thread and self.sound_thread.is_alive():
                self.sound_thread.join(timeout=1.0)
                
            # Clean up any other resources
            if hasattr(self, 'timer_id') and self.timer_id and hasattr(self.root, 'after_cancel'):
                self.root.after_cancel(self.timer_id)
                
            # Destroy the main window
            if hasattr(self, 'root') and self.root:
                self.root.destroy()
                
            logger.info("Application closed gracefully")
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            # Force exit as a last resort
            if hasattr(self, 'root') and self.root:
                self.root.destroy()
    
    def show_plugin_manager(self):
        """Show the MCP plugin manager interface."""
        logger.info("Showing plugin manager")
        
        try:
            # Check if MCP integration is available
            if not hasattr(self, 'mcp_loaded') or not self.mcp_loaded:
                # Create a simple dialog to show the message
                import tkinter.messagebox as messagebox
                messagebox.showinfo(
                    translate("MCP Plugins"),
                    translate("MCP integration is not available. Please ensure you have the enhanced features enabled.")
                )
                return
                
            # Create a window for the plugin manager (stub implementation)
            plugin_window = tk.Toplevel(self.root)
            plugin_window.title(translate("MCP Plugin Manager"))
            plugin_window.geometry("500x400")
            plugin_window.configure(bg=self.bg_color)
            
            # Make the window modal
            plugin_window.transient(self.root)
            plugin_window.grab_set()
            
            # Create a header
            header_label = tk.Label(
                plugin_window,
                text=translate("MCP Plugin Manager"),
                font=("Helvetica", 16, "bold"),
                bg=self.bg_color,
                fg=self.fg_color
            )
            header_label.pack(pady=10)
            
            # Information text
            info_text = translate(
                "The Model Context Protocol (MCP) allows for integration with external AI assistants and tools. "
                "Available plugins will be shown here when the enhanced features are fully implemented."
            )
            
            info_label = tk.Label(
                plugin_window,
                text=info_text,
                wraplength=450,
                justify=tk.LEFT,
                bg=self.bg_color,
                fg=self.fg_color
            )
            info_label.pack(padx=20, pady=10, fill='x')
            
            # Placeholder for plugin list
            plugins_frame = tk.Frame(plugin_window, bg=self.surface_color, padx=10, pady=10)
            plugins_frame.pack(padx=20, pady=10, fill='both', expand=True)
            
            # No plugins message
            no_plugins_label = tk.Label(
                plugins_frame,
                text=translate("No plugins currently available."),
                bg=self.surface_color,
                fg=self.fg_color
            )
            no_plugins_label.pack(pady=30)
            
            # Close button
            close_button = ttk.Button(
                plugin_window,
                text=translate("Close"),
                command=plugin_window.destroy,
                style='Primary.TButton'
            )
            close_button.pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error showing plugin manager: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Error showing plugin manager: {str(e)[:30]}...")
                self.status_label.config(fg='red')
    
    def show_challenges_window(self):
        """Show window with gamification challenges and achievements."""
        logger.info("Showing challenges window")
        
        try:
            # Create default challenges if not present
            if not hasattr(self, 'challenges'):
                self.challenges = [
                    {"id": "first_pomodoro", "name": "First Step", "description": "Complete your first Pomodoro", "points": 10, "completed": False},
                    {"id": "five_pomodoros", "name": "Getting Started", "description": "Complete 5 Pomodoros", "points": 25, "completed": False},
                    {"id": "daily_goal", "name": "Daily Goal", "description": "Reach your daily goal", "points": 50, "completed": False},
                    {"id": "three_day_streak", "name": "Consistency", "description": "Use the app for 3 days in a row", "points": 75, "completed": False},
                    {"id": "week_streak", "name": "Dedication", "description": "Use the app for 7 days in a row", "points": 100, "completed": False},
                ]
            
            # Initialize points if not present
            if not hasattr(self, 'points'):
                self.points = 0
                
            # Create the challenges window
            challenges_window = tk.Toplevel(self.root)
            challenges_window.title(translate("Challenges & Achievements"))
            challenges_window.geometry("500x500")
            challenges_window.configure(bg=self.bg_color)
            
            # Make the window modal
            challenges_window.transient(self.root)
            challenges_window.grab_set()
            
            # Create a header
            header_frame = tk.Frame(challenges_window, bg=self.bg_color)
            header_frame.pack(fill='x', padx=10, pady=10)
            
            # Title
            title_label = tk.Label(
                header_frame, 
                text=translate("Challenges & Achievements"),
                font=("Helvetica", 16, "bold"),
                bg=self.bg_color,
                fg=self.fg_color
            )
            title_label.pack(side='left')
            
            # Points display
            points_frame = tk.Frame(header_frame, bg=self.bg_color)
            points_frame.pack(side='right')
            
            points_label = tk.Label(
                points_frame,
                text=translate("Points:"),
                font=("Helvetica", 12),
                bg=self.bg_color,
                fg=self.fg_color
            )
            points_label.pack(side='left')
            
            points_value = tk.Label(
                points_frame,
                text=str(self.points),
                font=("Helvetica", 14, "bold"),
                bg=self.bg_color,
                fg=self.primary_color
            )
            points_value.pack(side='left', padx=5)
            
            # Create a frame for challenges
            challenges_frame = tk.Frame(challenges_window, bg=self.bg_color)
            challenges_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Header for challenges list
            header = tk.Frame(challenges_frame, bg=self.primary_color)
            header.pack(fill='x', pady=(0, 5))
            
            # Headers
            headers = [("Name", 0.25), ("Description", 0.45), ("Points", 0.15), ("Status", 0.15)]
            for text, width in headers:
                header_label = tk.Label(
                    header,
                    text=translate(text),
                    font=("Helvetica", 12, "bold"),
                    bg=self.primary_color,
                    fg="white",
                    width=int(50 * width)
                )
                header_label.pack(side='left', padx=5, pady=5)
            
            # Create a canvas and scrollbar for the challenges
            canvas_frame = tk.Frame(challenges_frame, bg=self.bg_color)
            canvas_frame.pack(fill='both', expand=True)
            
            canvas = tk.Canvas(canvas_frame, bg=self.bg_color, highlightthickness=0)
            scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=self.bg_color)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add challenges to the scrollable frame
            for i, challenge in enumerate(self.challenges):
                row_frame = tk.Frame(scrollable_frame, bg=self.surface_color if i % 2 == 0 else self.bg_color)
                row_frame.pack(fill='x', pady=1)
                
                # Challenge name
                name_label = tk.Label(
                    row_frame,
                    text=challenge["name"],
                    font=("Helvetica", 10, "bold"),
                    bg=row_frame["bg"],
                    fg=self.fg_color,
                    width=int(50 * 0.25),
                    anchor='w'
                )
                name_label.pack(side='left', padx=5, pady=5)
                
                # Challenge description
                desc_label = tk.Label(
                    row_frame,
                    text=challenge["description"],
                    font=("Helvetica", 10),
                    bg=row_frame["bg"],
                    fg=self.fg_color,
                    width=int(50 * 0.45),
                    anchor='w'
                )
                desc_label.pack(side='left', padx=5, pady=5)
                
                # Challenge points
                points_label = tk.Label(
                    row_frame,
                    text=str(challenge["points"]),
                    font=("Helvetica", 10),
                    bg=row_frame["bg"],
                    fg=self.primary_color,
                    width=int(50 * 0.15),
                    anchor='center'
                )
                points_label.pack(side='left', padx=5, pady=5)
            
            # Close button
            close_button = ttk.Button(
                challenges_window,
                text=translate("Close"),
                command=challenges_window.destroy,
                style='Primary.TButton'
            )
            close_button.pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error showing challenges window: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Error showing challenges: {str(e)[:30]}...")
                self.status_label.config(fg='red')
    
    def toggle_intensive_mode(self):
        """Toggle the intensive mode feature."""
        logger.info("Toggling intensive mode")
        
        try:
            # Initialize intensive mode if not already set
            if not hasattr(self, 'intensive_mode'):
                self.intensive_mode = False
                self.intensive_time_left = 0
                
            # Toggle the mode
            self.intensive_mode = not self.intensive_mode
            logger.info(f"Intensive mode is now {'ON' if self.intensive_mode else 'OFF'}")
            
            # Update UI
            if self.intensive_mode:
                # Turn on intensive mode
                self.intensive_button.config(text=translate("Disable Intensive"))
                if hasattr(self, 'intensive_timer_label'):
                    self.intensive_timer_label.config(text="00:30:00")  # Default time
                    self.intensive_time_left = 30 * 60  # 30 minutes in seconds
            else:
                # Turn off intensive mode
                self.intensive_button.config(text=translate("Intensive Mode"))
                if hasattr(self, 'intensive_timer_label'):
                    self.intensive_timer_label.config(text="")
                self.intensive_time_left = 0
                
            # Show notification
            if hasattr(self, 'status_label'):
                if self.intensive_mode:
                    self.status_label.config(text=translate("Intensive Mode enabled. Focus deeply for 30 minutes."))
                else:
                    self.status_label.config(text=translate("Intensive Mode disabled."))
                    
            # Play sound notification
            if hasattr(self, 'sound_manager') and hasattr(self.sound_manager, 'play'):
                if self.intensive_mode:
                    self.sound_manager.play('start_intensive')
                else:
                    self.sound_manager.play('stop_intensive')
                    
        except Exception as e:
            logger.error(f"Error toggling intensive mode: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Error with intensive mode: {str(e)[:30]}...")
                self.status_label.config(fg='red')
    
    def show_category_selector(self):
        """Show a dialog to select the current task category."""
        logger.info("Showing category selector")
        
        try:
            # Default categories if not already defined
            if not hasattr(self, 'categories') or not self.categories:
                self.categories = ["Work", "Study", "Personal"]
                
            # Default current category if not set
            if not hasattr(self, 'current_category'):
                self.current_category = self.categories[0] if self.categories else "Work"
            
            # Create a toplevel window for category selection
            category_window = tk.Toplevel(self.root)
            category_window.title(translate("Select Category"))
            category_window.geometry("300x400")
            category_window.configure(bg=self.bg_color)
            
            # Make the window modal
            category_window.transient(self.root)
            category_window.grab_set()
            
            # Instructions label
            instructions = ttk.Label(
                category_window,
                text=translate("Select a category for your Pomodoro sessions:"),
                wraplength=280
            )
            instructions.pack(pady=10, padx=10)
            
            # Create a frame for the listbox and scrollbar
            list_frame = tk.Frame(category_window, bg=self.bg_color)
            list_frame.pack(fill='both', expand=True, padx=10, pady=5)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side='right', fill='y')
            
            # Listbox for categories
            category_listbox = tk.Listbox(
                list_frame,
                bg=self.surface_color,
                fg=self.fg_color,
                selectbackground=self.primary_color,
                selectforeground='white',
                height=10,
                width=30,
                yscrollcommand=scrollbar.set
            )
            category_listbox.pack(side='left', fill='both', expand=True)
            scrollbar.config(command=category_listbox.yview)
            
            # Populate the listbox
            for category in self.categories:
                category_listbox.insert(tk.END, category)
            
            # Select the current category
            for i, category in enumerate(self.categories):
                if category == self.current_category:
                    category_listbox.selection_set(i)
                    category_listbox.see(i)
                    break
            
            # Entry for adding new categories
            new_category_frame = tk.Frame(category_window, bg=self.bg_color)
            new_category_frame.pack(fill='x', padx=10, pady=5)
            
            new_category_entry = ttk.Entry(new_category_frame, width=20)
            new_category_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
            
            # Function to add a new category
            def add_category():
                new_cat = new_category_entry.get().strip()
                if new_cat and new_cat not in self.categories:
                    self.categories.append(new_cat)
                    category_listbox.insert(tk.END, new_cat)
                    new_category_entry.delete(0, tk.END)
            
            add_button = ttk.Button(
                new_category_frame,
                text=translate("Add"),
                command=add_category
            )
            add_button.pack(side='right')
            
            # Function to select a category
            def select_category():
                selection = category_listbox.curselection()
                if selection:
                    index = selection[0]
                    selected_category = category_listbox.get(index)
                    self.current_category = selected_category
                    
                    # Update the category label if it exists
                    if hasattr(self, 'current_category_value') and self.current_category_value:
                        self.current_category_value.config(text=selected_category)
                    
                    category_window.destroy()
            
            # Buttons frame
            buttons_frame = tk.Frame(category_window, bg=self.bg_color)
            buttons_frame.pack(fill='x', padx=10, pady=10)
            
            # Select button
            select_button = ttk.Button(
                buttons_frame,
                text=translate("Select"),
                command=select_category,
                style='Primary.TButton'
            )
            select_button.pack(side='left', padx=5)
            
            # Cancel button
            cancel_button = ttk.Button(
                buttons_frame,
                text=translate("Cancel"),
                command=category_window.destroy
            )
            cancel_button.pack(side='right', padx=5)
            
        except Exception as e:
            logger.error(f"Error showing category selector: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Error selecting category: {str(e)[:30]}...")
                self.status_label.config(fg='red')
    
    def show_statistics(self):
        """Show a window with statistics about the user's productivity"""
        # Initialize today_stats if not already set
        if not hasattr(self, 'today_stats'):
            self.today_stats = {'pomodoros_completed': 0, 'work_time_seconds': 0}
            
        stats_window = tk.Toplevel(self.root)
        stats_window.title(translate("Pomodoro Statistics"))
        stats_window.geometry("500x400")
        stats_window.configure(bg=self.bg_color)
        
        # Make the window modal
        stats_window.transient(self.root)
        stats_window.grab_set()
        
        # Create tabs for different statistics views
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Today's stats tab
        today_frame = ttk.Frame(notebook, style='Custom.TFrame')
        notebook.add(today_frame, text=translate("Today"))
        
        # Format data for today's stats
        pomodoros = self.today_stats.get('pomodoros_completed', 0)
        work_time_seconds = self.today_stats.get('work_time_seconds', 0)
        work_hours, work_remainder = divmod(work_time_seconds, 3600)
        work_minutes, work_seconds = divmod(work_remainder, 60)
        work_time_str = f"{work_hours}h {work_minutes}m {work_seconds}s"
        
        # Create labels for today's stats
        tk.Label(today_frame, text=translate("Today's Statistics"), font=("Helvetica", 14, "bold"), bg=self.bg_color, fg=self.fg_color).pack(pady=(20, 10))
        tk.Label(today_frame, text=f"{translate('Pomodoros Completed')}: {pomodoros}", font=("Helvetica", 12), bg=self.bg_color, fg=self.fg_color).pack(pady=5)
        tk.Label(today_frame, text=f"{translate('Total Work Time')}: {work_time_str}", font=("Helvetica", 12), bg=self.bg_color, fg=self.fg_color).pack(pady=5)
        tk.Label(today_frame, text=f"{translate('Daily Goal')}: {self.daily_goal} pomodoros", font=("Helvetica", 12), bg=self.bg_color, fg=self.fg_color).pack(pady=5)
        
        # Goal progress bar
        goal_frame = tk.Frame(today_frame, bg=self.bg_color)
        goal_frame.pack(fill='x', pady=10)
        goal_percent = min(100, int((pomodoros / max(1, self.daily_goal)) * 100))
        
        tk.Label(goal_frame, text=f"{translate('Goal Progress')}: {goal_percent}%", bg=self.bg_color, fg=self.fg_color).pack(anchor='w')
        progress_frame = tk.Frame(goal_frame, bg=self.surface_color, height=20, width=400)
        progress_frame.pack(fill='x', pady=5)
        progress_bar = tk.Frame(progress_frame, bg=self.primary_color, height=20, width=int(400 * goal_percent / 100))
        progress_bar.place(x=0, y=0)
        
        # Weekly stats tab (placeholder for now)
        weekly_frame = tk.Frame(notebook, bg=self.bg_color)
        notebook.add(weekly_frame, text=translate("Weekly"))
        tk.Label(weekly_frame, text=translate("Weekly statistics will be available soon"), font=("Helvetica", 12), bg=self.bg_color, fg=self.fg_color).pack(pady=30)
        
        # All-time stats tab (placeholder for now)
        alltime_frame = tk.Frame(notebook, bg=self.bg_color)
        notebook.add(alltime_frame, text=translate("All Time"))
        tk.Label(alltime_frame, text=translate("All-time statistics will be available soon"), font=("Helvetica", 12), bg=self.bg_color, fg=self.fg_color).pack(pady=30)
        
        # Close button
        tk.Button(
            stats_window, 
            text=translate("Close"), 
            command=stats_window.destroy,
            bg=self.surface_color,
            fg=self.fg_color,
            activebackground=self.button_active_bg,
            font=("Helvetica", 10)
        ).pack(pady=20)
        
        # Center the window on the screen
        stats_window.update_idletasks()
        width = stats_window.winfo_width()
        height = stats_window.winfo_height()
        x = (stats_window.winfo_screenwidth() // 2) - (width // 2)
        y = (stats_window.winfo_screenheight() // 2) - (height // 2)
        stats_window.geometry(f"{width}x{height}+{x}+{y}")
        
        logger.info("Opened statistics window")
        
    def open_settings_panel(self):
        """Open a settings panel to configure the timer settings"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title(translate("Pomodoro Settings"))
        settings_window.geometry("500x600")
        settings_window.configure(bg=self.bg_color)
        
        # Make the window modal
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Create a main frame for settings
        main_frame = tk.Frame(settings_window, bg=self.bg_color)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Add section title
        tk.Label(main_frame, text=translate("Timer Settings"), font=("Helvetica", 14, "bold"), bg=self.bg_color, fg=self.fg_color).pack(anchor='w', pady=(0, 15))
        
        # Timer duration settings
        durations_frame = tk.Frame(main_frame, bg=self.bg_color)
        durations_frame.pack(fill='x', pady=5)
        
        # Work duration
        work_frame = tk.Frame(durations_frame, bg=self.bg_color)
        work_frame.pack(fill='x', pady=5)
        tk.Label(work_frame, text=translate("Work Duration (minutes):"), bg=self.bg_color, fg=self.fg_color, width=25, anchor='w').pack(side='left')
        work_duration_var = tk.IntVar(value=self.work_duration // 60)
        work_spinbox = tk.Spinbox(work_frame, from_=1, to=60, textvariable=work_duration_var, width=5, bg=self.surface_color, fg=self.fg_color)
        work_spinbox.pack(side='right')
        
        # Short break duration
        short_break_frame = tk.Frame(durations_frame, bg=self.bg_color)
        short_break_frame.pack(fill='x', pady=5)
        tk.Label(short_break_frame, text=translate("Short Break Duration (minutes):"), bg=self.bg_color, fg=self.fg_color, width=25, anchor='w').pack(side='left')
        short_break_var = tk.IntVar(value=self.short_break_duration // 60)
        short_break_spinbox = tk.Spinbox(short_break_frame, from_=1, to=30, textvariable=short_break_var, width=5, bg=self.surface_color, fg=self.fg_color)
        short_break_spinbox.pack(side='right')
        
        # Long break duration
        long_break_frame = tk.Frame(durations_frame, bg=self.bg_color)
        long_break_frame.pack(fill='x', pady=5)
        tk.Label(long_break_frame, text=translate("Long Break Duration (minutes):"), bg=self.bg_color, fg=self.fg_color, width=25, anchor='w').pack(side='left')
        long_break_var = tk.IntVar(value=self.long_break_duration // 60)
        long_break_spinbox = tk.Spinbox(long_break_frame, from_=1, to=60, textvariable=long_break_var, width=5, bg=self.surface_color, fg=self.fg_color)
        long_break_spinbox.pack(side='right')
        
        # Long break interval
        interval_frame = tk.Frame(durations_frame, bg=self.bg_color)
        interval_frame.pack(fill='x', pady=5)
        tk.Label(interval_frame, text=translate("Long Break After (pomodoros):"), bg=self.bg_color, fg=self.fg_color, width=25, anchor='w').pack(side='left')
        interval_var = tk.IntVar(value=self.cycles_before_long_break)
        interval_spinbox = tk.Spinbox(interval_frame, from_=1, to=10, textvariable=interval_var, width=5, bg=self.surface_color, fg=self.fg_color)
        interval_spinbox.pack(side='right')
        
        # Daily goal
        daily_goal_frame = tk.Frame(durations_frame, bg=self.bg_color)
        daily_goal_frame.pack(fill='x', pady=5)
        tk.Label(daily_goal_frame, text=translate("Daily Goal (pomodoros):"), bg=self.bg_color, fg=self.fg_color, width=25, anchor='w').pack(side='left')
        daily_goal_var = tk.IntVar(value=self.daily_goal)
        daily_goal_spinbox = tk.Spinbox(daily_goal_frame, from_=1, to=20, textvariable=daily_goal_var, width=5, bg=self.surface_color, fg=self.fg_color)
        daily_goal_spinbox.pack(side='right')
        
        # Add separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # Behavior settings
        tk.Label(main_frame, text=translate("Behavior"), font=("Helvetica", 14, "bold"), bg=self.bg_color, fg=self.fg_color).pack(anchor='w', pady=(0, 15))
        
        behavior_frame = tk.Frame(main_frame, bg=self.bg_color)
        behavior_frame.pack(fill='x')
        
        # Auto-start breaks
        auto_break_var = tk.BooleanVar(value=self.auto_start_break)
        auto_break_check = tk.Checkbutton(
            behavior_frame, 
            text=translate("Auto-start breaks"), 
            variable=auto_break_var,
            bg=self.bg_color, 
            fg=self.fg_color,
            activebackground=self.bg_color,
            selectcolor=self.surface_color
        )
        auto_break_check.pack(anchor='w', pady=5)
        
        # Auto-start pomodoros
        auto_work_var = tk.BooleanVar(value=self.auto_start_work)
        auto_work_check = tk.Checkbutton(
            behavior_frame, 
            text=translate("Auto-start pomodoros"), 
            variable=auto_work_var,
            bg=self.bg_color, 
            fg=self.fg_color,
            activebackground=self.bg_color,
            selectcolor=self.surface_color
        )
        auto_work_check.pack(anchor='w', pady=5)
        
        # Sound settings frame
        sound_frame = tk.Frame(behavior_frame, bg=self.bg_color)
        sound_frame.pack(fill='x', pady=5)
        
        # Sound enabled
        sound_var = tk.BooleanVar(value=self.sound_enabled)
        sound_check = tk.Checkbutton(
            sound_frame, 
            text=translate("Enable sounds"), 
            variable=sound_var,
            bg=self.bg_color, 
            fg=self.fg_color,
            activebackground=self.bg_color,
            selectcolor=self.surface_color,
            command=lambda: sound_pack_menu.config(state=tk.NORMAL if sound_var.get() else tk.DISABLED)
        )
        sound_check.pack(side='left', padx=(0, 10))
        
        # Sound pack selection
        tk.Label(sound_frame, text=translate("Sound pack:"), bg=self.bg_color, fg=self.fg_color).pack(side='left', padx=(0, 5))
        
        # Get available sound packs
        sound_packs = ['default']
        sounds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
        if os.path.exists(sounds_dir):
            sound_packs.extend([d for d in os.listdir(sounds_dir) 
                              if os.path.isdir(os.path.join(sounds_dir, d)) and d != '__pycache__'])
        
        current_pack = getattr(self.settings, 'sound_pack', 'default')
        sound_pack_var = tk.StringVar(value=current_pack)
        sound_pack_menu = ttk.OptionMenu(
            sound_frame, 
            sound_pack_var, 
            current_pack,
            *sound_packs
        )
        sound_pack_menu.config(width=15)
        sound_pack_menu.pack(side='left')
        
        # Disable sound pack menu if sounds are disabled
        if not sound_var.get():
            sound_pack_menu.config(state=tk.DISABLED)
        
        # Notifications enabled
        notif_var = tk.BooleanVar(value=self.notifications_enabled)
        notif_check = tk.Checkbutton(
            behavior_frame, 
            text=translate("Enable notifications"), 
            variable=notif_var,
            bg=self.bg_color, 
            fg=self.fg_color,
            activebackground=self.bg_color,
            selectcolor=self.surface_color
        )
        notif_check.pack(anchor='w', pady=5)
        
        # Add separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=15)
        
        def save_settings():
            # Save timer durations
            self.work_duration = work_duration_var.get() * 60
            self.short_break_duration = short_break_var.get() * 60
            self.long_break_duration = long_break_var.get() * 60
            self.cycles_before_long_break = interval_var.get()
            self.daily_goal = daily_goal_var.get()
            
            # Save behavior settings
            self.auto_start_break = auto_break_var.get()
            self.auto_start_work = auto_work_var.get()
            self.sound_enabled = sound_var.get()
            self.notifications_enabled = notif_var.get()
            
            # Update settings object and save to file
            if hasattr(self, 'settings'):
                if hasattr(self.settings, 'work_duration'):
                    self.settings.work_duration = work_duration_var.get()
                if hasattr(self.settings, 'short_break_duration'):
                    self.settings.short_break_duration = short_break_var.get()
                if hasattr(self.settings, 'long_break_duration'):
                    self.settings.long_break_duration = long_break_var.get()
                if hasattr(self.settings, 'long_break_interval'):
                    self.settings.long_break_interval = interval_var.get()
                if hasattr(self.settings, 'daily_goal'):
                    self.settings.daily_goal = daily_goal_var.get()
                if hasattr(self.settings, 'auto_start_breaks'):
                    self.settings.auto_start_breaks = auto_break_var.get()
                if hasattr(self.settings, 'auto_start_pomodoros'):
                    self.settings.auto_start_pomodoros = auto_work_var.get()
                if hasattr(self.settings, 'sound_enabled'):
                    self.settings.sound_enabled = sound_var.get()
                if hasattr(self.settings, 'notifications'):
                    self.settings.notifications = notif_var.get()
            
            # If the timer is not running, update the current time_left
            if not self.timer_running and not self.paused and not self.on_break:
                self.time_left = self.work_duration
                self.update_timer_display()
                
            self.save_settings()
            logger.info("Settings saved and applied")
            settings_window.destroy()
        
        # Buttons frame
        buttons_frame = tk.Frame(main_frame, bg=self.bg_color)
        buttons_frame.pack(fill='x', pady=15)
        
        # Cancel button
        tk.Button(
            buttons_frame, 
            text=translate("Cancel"), 
            command=settings_window.destroy,
            bg=self.surface_color,
            fg=self.fg_color,
            activebackground=self.button_active_bg,
            font=("Helvetica", 10)
        ).pack(side='left', padx=5)
        
        # Save button
        tk.Button(
            buttons_frame, 
            text=translate("Save"), 
            command=save_settings,
            bg=self.primary_color,
            fg=self.fg_color,
            activebackground=self.button_active_bg,
            font=("Helvetica", 10)
        ).pack(side='right', padx=5)
        
        # Center the window on the screen
        settings_window.update_idletasks()
        width = settings_window.winfo_width()
        height = settings_window.winfo_height()
        x = (settings_window.winfo_screenwidth() // 2) - (width // 2)
        y = (settings_window.winfo_screenheight() // 2) - (height // 2)
        settings_window.geometry(f"{width}x{height}+{x}+{y}")
        
        logger.info("Opened settings panel")
    
    # Removed duplicate update_ui_colors method - using the one defined earlier
    # This helps prevent conflicts and ensures consistent theming
    
    def _update_theme_colors(self):
        """Update theme colors based on system or user preference."""
        try:
            if hasattr(self, 'theme_manager'):
                # Try to get colors from theme manager
                if hasattr(self.theme_manager, 'get_current_theme'):
                    theme = self.theme_manager.get_current_theme()
                    self.bg_color = theme.get('background', '#1e1e1e')
                    self.fg_color = theme.get('foreground', '#ffffff')
                    self.primary_color = theme.get('primary', '#0078d7')
                    self.surface_color = theme.get('surface', '#2d2d2d')
                    self.secondary_color = theme.get('secondary', '#ff8c00')
                    self.button_active_bg = theme.get('button_active_bg', '#3c3c3c')
                    self.work_color = theme.get('work', '#ff8a80')
                    self.break_color = theme.get('break', '#80cbc4')
                else:
                    # Fallback to direct attribute access if get_current_theme doesn't exist
                    self.bg_color = getattr(self.theme_manager, 'bg_color', '#1e1e1e')
                    self.fg_color = getattr(self.theme_manager, 'fg_color', '#ffffff')
                    self.primary_color = getattr(self.theme_manager, 'primary_color', '#0078d7')
                    self.surface_color = getattr(self.theme_manager, 'surface_color', '#2d2d2d')
                    self.secondary_color = getattr(self.theme_manager, 'secondary_color', '#ff8c00')
                    self.button_active_bg = getattr(self.theme_manager, 'button_active_bg', '#3c3c3c')
                    self.work_color = getattr(self.theme_manager, 'work_color', '#ff8a80')
                    self.break_color = getattr(self.theme_manager, 'break_color', '#80cbc4')
        except Exception as e:
            logger.error(f"Error updating theme colors: {e}")
            # Fallback colors
            self.bg_color = '#1e1e1e'
            self.fg_color = '#ffffff'
            self.primary_color = '#0078d7'
            self.surface_color = '#2d2d2d'
            self.secondary_color = '#ff8c00'
            self.button_active_bg = '#3c3c3c'
            self.work_color = '#ff8a80'
            self.break_color = '#80cbc4'
# Initialize and run the Pomodoro Timer application
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = PomodoroTimer(root)
        root.mainloop()
    except Exception as e:
        print(f"Uncaught exception: {e}")
        import traceback
        traceback.print_exc()
        