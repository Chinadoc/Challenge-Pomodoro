"""
Notification management for the Enhanced Pomodoro Timer.
Handles system and in-app notifications.
"""

import logging
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable

# Try to import platform-specific notification libraries
try:
    import pync  # macOS notifier
except ImportError:
    pync = None

try:
    import win10toast  # Windows 10+ toast notifications
except ImportError:
    win10toast = None

try:
    import gi
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify  # type: ignore  # Linux notifications
except (ImportError, ValueError):
    Notify = None

# Initialize logger
logger = logging.getLogger(__name__)

class Notification:
    """Represents a notification with its properties."""
    
    def __init__(self, 
                 title: str = "",
                 message: str = "",
                 duration: int = 5,
                 sound: bool = False,
                 sound_file: Optional[Union[str, Path]] = None,
                 icon: Optional[Union[str, Path]] = None,
                 actions: Optional[Dict[str, Callable]] = None,
                 on_click: Optional[Callable] = None,
                 on_close: Optional[Callable] = None):
        """Initialize a notification.
        
        Args:
            title: Notification title
            message: Notification message
            duration: Duration in seconds (0 = until dismissed)
            sound: Whether to play a sound
            sound_file: Path to custom sound file
            icon: Path to notification icon
            actions: Dictionary of action labels and their callbacks
            on_click: Callback when notification is clicked
            on_close: Callback when notification is closed
        """
        self.title = title
        self.message = message
        self.duration = max(0, duration)
        self.sound = sound
        self.sound_file = Path(sound_file) if sound_file else None
        self.icon = str(icon) if icon else None
        self.actions = actions or {}
        self.on_click = on_click
        self.on_close = on_close
        self._id = f"notification_{int(datetime.now().timestamp())}"
        self._shown = False
    
    def show(self) -> bool:
        """Display the notification.
        
        Returns:
            bool: True if the notification was shown successfully
        """
        if self._shown:
            logger.warning("Notification already shown")
            return False
        
        self._shown = True
        return NotificationManager.show_notification(self)
    
    def dismiss(self) -> None:
        """Dismiss the notification (if supported)."""
        NotificationManager.dismiss_notification(self._id)
    
    def __str__(self) -> str:
        return f"Notification(title='{self.title}', message='{self.message[:20]}...')"

class NotificationManager:
    """Manages system and in-app notifications."""
    
    _instance = None
    _initialized = False
    _active_notifications: Dict[str, Any] = {}
    _default_icon: Optional[str] = None
    _default_sound: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._initialized_platform = False
            self._platform_notifier = None
            self._initialize_platform()
    
    def _initialize_platform(self) -> None:
        """Initialize platform-specific notification system."""
        if self._initialized_platform:
            return
        
        system = platform.system().lower()
        
        try:
            if system == 'darwin' and pync is not None:
                self._platform_notifier = 'pync'
                logger.info("Using pync for macOS notifications")
            
            elif system == 'windows' and win10toast is not None:
                self._platform_notifier = 'win10toast'
                try:
                    self._win10toast = win10toast.ToastNotifier()
                    logger.info("Using win10toast for Windows notifications")
                except Exception as e:
                    logger.warning(f"Failed to initialize win10toast: {e}")
                    self._platform_notifier = 'fallback'
            
            elif system == 'linux' and Notify is not None:
                try:
                    if Notify.init("Pomodoro Timer"):
                        self._platform_notifier = 'notify2'
                        logger.info("Using libnotify for Linux notifications")
                    else:
                        logger.warning("Failed to initialize libnotify")
                        self._platform_notifier = 'fallback'
                except Exception as e:
                    logger.warning(f"Error initializing libnotify: {e}")
                    self._platform_notifier = 'fallback'
            
            else:
                logger.info("Using fallback notification system")
                self._platform_notifier = 'fallback'
                
            self._initialized_platform = True
            
        except Exception as e:
            logger.error(f"Error initializing notification system: {e}")
            self._platform_notifier = 'fallback'
    
    @classmethod
    def set_default_icon(cls, icon_path: Union[str, Path]) -> None:
        """Set the default notification icon.
        
        Args:
            icon_path: Path to the icon file
        """
        cls._default_icon = str(icon_path)
    
    @classmethod
    def set_default_sound(cls, sound_path: Union[str, Path]) -> None:
        """Set the default notification sound.
        
        Args:
            sound_path: Path to the sound file
        """
        cls._default_sound = str(sound_path)
    
    @classmethod
    def show_notification(cls, notification: Notification) -> bool:
        """Show a notification.
        
        Args:
            notification: Notification to show
            
        Returns:
            bool: True if the notification was shown successfully
        """
        try:
            # Store the notification
            cls._active_notifications[notification._id] = notification
            
            # Play sound if enabled
            if notification.sound:
                sound_file = notification.sound_file or cls._default_sound
                if sound_file and Path(sound_file).exists():
                    cls._play_sound(sound_file)
            
            # Show platform-specific notification
            system = platform.system().lower()
            manager = cls()
            
            if manager._platform_notifier == 'pync' and system == 'darwin':
                return manager._show_macos_notification(notification)
            
            elif manager._platform_notifier == 'win10toast' and system == 'windows':
                return manager._show_windows_notification(notification)
            
            elif manager._platform_notifier == 'notify2' and system == 'linux':
                return manager._show_linux_notification(notification)
            
            else:
                return manager._show_fallback_notification(notification)
            
        except Exception as e:
            logger.error(f"Error showing notification: {e}", exc_info=True)
            return False
    
    def _show_macos_notification(self, notification: Notification) -> bool:
        """Show a notification on macOS using pync."""
        try:
            import pync
            
            # Prepare arguments
            kwargs = {
                'title': notification.title,
                'message': notification.message,
                'appIcon': notification.icon or self._default_icon,
                'timeout': notification.duration if notification.duration > 0 else 10,
                'sound': 'default' if notification.sound else None,
            }
            
            # Remove None values
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            # Show notification
            pync.notify(**kwargs)
            return True
            
        except Exception as e:
            logger.error(f"Error showing macOS notification: {e}")
            return self._show_fallback_notification(notification)
    
    def _show_windows_notification(self, notification: Notification) -> bool:
        """Show a notification on Windows using win10toast."""
        try:
            # Windows toast notifications don't support custom icons in the free version
            # and have limited duration options
            duration = min(max(5, notification.duration), 10)  # 5-10 seconds
            
            self._win10toast.show_toast(
                title=notification.title,
                msg=notification.message,
                duration=duration,
                threaded=True
            )
            return True
            
        except Exception as e:
            logger.error(f"Error showing Windows notification: {e}")
            return self._show_fallback_notification(notification)
    
    def _show_linux_notification(self, notification: Notification) -> bool:
        """Show a notification on Linux using libnotify."""
        try:
            notification = Notify.Notification.new(
                notification.title,
                notification.message,
                notification.icon or self._default_icon or ''
            )
            
            # Set timeout (in milliseconds), 0 = never expire
            timeout = notification.duration * 1000 if notification.duration > 0 else 0
            notification.set_timeout(timeout)
            
            # Show the notification
            notification.show()
            return True
            
        except Exception as e:
            logger.error(f"Error showing Linux notification: {e}")
            return self._show_fallback_notification(notification)
    
    def _show_fallback_notification(self, notification: Notification) -> bool:
        """Show a fallback notification using a simple message box."""
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            # Create a root window and hide it
            root = tk.Tk()
            root.withdraw()
            
            # Show message box
            messagebox.showinfo(
                title=notification.title,
                message=notification.message
            )
            
            # Run the callback if provided
            if notification.on_click:
                try:
                    notification.on_click()
                except Exception as e:
                    logger.error(f"Error in notification click handler: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error showing fallback notification: {e}")
            return False
    
    @classmethod
    def dismiss_notification(cls, notification_id: str) -> None:
        """Dismiss a notification.
        
        Args:
            notification_id: ID of the notification to dismiss
        """
        if notification_id in cls._active_notifications:
            notification = cls._active_notifications.pop(notification_id)
            
            # Call on_close callback if provided
            if notification.on_close:
                try:
                    notification.on_close()
                except Exception as e:
                    logger.error(f"Error in notification close handler: {e}")
    
    @classmethod
    def dismiss_all_notifications(cls) -> None:
        """Dismiss all active notifications."""
        for notification_id in list(cls._active_notifications.keys()):
            cls.dismiss_notification(notification_id)
    
    @classmethod
    def _play_sound(cls, sound_file: Union[str, Path]) -> None:
        """Play a sound file.
        
        Args:
            sound_file: Path to the sound file to play
        """
        try:
            sound_file = str(sound_file)
            system = platform.system().lower()
            
            if system == 'darwin':
                # On macOS, use afplay
                subprocess.Popen(['afplay', sound_file], 
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            
            elif system == 'windows':
                # On Windows, use winsound for WAV files or start for other formats
                if sound_file.lower().endswith('.wav'):
                    import winsound
                    winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    import os
                    os.startfile(sound_file)  # type: ignore
            
            else:  # Linux and others
                # Try various Linux audio players
                for player in ['aplay', 'paplay', 'mpg123', 'mpg321', 'mplayer']:
                    if cls._is_command_available(player):
                        subprocess.Popen([player, sound_file],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                        break
                
        except Exception as e:
            logger.error(f"Error playing sound {sound_file}: {e}")
    
    @staticmethod
    def _is_command_available(command: str) -> bool:
        """Check if a command is available on the system."""
        try:
            return subprocess.call(['which', command], 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL) == 0
        except Exception:
            return False

# Global notification manager instance
notification_manager = NotificationManager()

def get_notification_manager() -> NotificationManager:
    """Get the global notification manager instance."""
    return notification_manager
