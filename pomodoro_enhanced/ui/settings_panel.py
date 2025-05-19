"""
Settings panel for the Enhanced Pomodoro Timer.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Dict, Any, Optional
import json
import os
import logging
from pathlib import Path

from ..core.models import TimerSettings
from ..core.i18n import _ as translate
from ..core.notifications import NotificationManager
from ..core.analytics import get_analytics_manager
from ..core.preferences import PreferenceManager
from ..core.exceptions import ApplicationError

class SettingsPanel(ttk.Frame):
    """Panel for application settings."""
    
    def __init__(self, parent, timer_service, data_manager, *args, **kwargs):
        """Initialize the settings panel."""
        super().__init__(parent, *args, **kwargs)
        
        self.timer_service = timer_service
        self.data_manager = data_manager
        self.logger = logging.getLogger(f"{__name__}.SettingsPanel")
        self.analytics = get_analytics_manager()
        
        # Load current settings
        self.settings = self.data_manager.get_settings()
        
        # Hook keyboard shortcuts after widgets are created
        self.bind("<Map>", lambda e: self._setup_keyboard_shortcuts())
        
        # Create UI
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create and arrange the settings panel widgets."""
        # Main container with padding
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Setup context menu
        self._setup_context_menu()
        
        # Canvas and scrollbar for scrollable content
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure canvas scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Create a window in the canvas for the scrollable frame
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create settings sections
        self._create_timer_section(scrollable_frame)
        self._create_appearance_section(scrollable_frame)
        self._create_notifications_section(scrollable_frame)
        self._create_data_section(scrollable_frame)
        
        # Apply button
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text=translate("Apply Settings"),
            command=self._on_apply_settings,
            style='Accent.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text=translate("Reset to Defaults"),
            command=self._on_reset_defaults
        ).pack(side=tk.RIGHT, padx=5)
    
    def _create_timer_section(self, parent) -> None:
        """Create the timer settings section."""
        frame = ttk.LabelFrame(parent, text=translate("Timer Settings"), padding=10)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Work duration
        ttk.Label(frame, text=translate("Work Duration (minutes):")).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.work_duration = tk.IntVar(value=self.settings.work_duration)
        ttk.Spinbox(
            frame, 
            from_=1, 
            to=120, 
            textvariable=self.work_duration,
            width=5
        ).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Short break duration
        ttk.Label(frame, text=translate("Short Break (minutes):")).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.short_break_duration = tk.IntVar(value=self.settings.short_break_duration)
        ttk.Spinbox(
            frame, 
            from_=1, 
            to=60, 
            textvariable=self.short_break_duration,
            width=5
        ).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Long break duration
        ttk.Label(frame, text=translate("Long Break (minutes):")).grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.long_break_duration = tk.IntVar(value=self.settings.long_break_duration)
        ttk.Spinbox(
            frame, 
            from_=1, 
            to=120, 
            textvariable=self.long_break_duration,
            width=5
        ).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Long break interval
        ttk.Label(frame, text=translate("Work Sessions Before Long Break:")).grid(
            row=3, column=0, sticky=tk.W, pady=5, padx=5)
        self.long_break_interval = tk.IntVar(value=self.settings.long_break_interval)
        ttk.Spinbox(
            frame, 
            from_=1, 
            to=10, 
            textvariable=self.long_break_interval,
            width=5
        ).grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Auto-start settings
        ttk.Label(frame, text=translate("Auto-start:")).grid(
            row=4, column=0, sticky=tk.W, pady=5, padx=5)
        
        auto_start_frame = ttk.Frame(frame)
        auto_start_frame.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.auto_start_breaks = tk.BooleanVar(value=self.settings.auto_start_breaks)
        ttk.Checkbutton(
            auto_start_frame,
            text=translate("Breaks"),
            variable=self.auto_start_breaks
        ).pack(side=tk.LEFT, padx=5)
        
        self.auto_start_pomodoros = tk.BooleanVar(value=self.settings.auto_start_pomodoros)
        ttk.Checkbutton(
            auto_start_frame,
            text=translate("Pomodoros"),
            variable=self.auto_start_pomodoros
        ).pack(side=tk.LEFT, padx=5)
        
        # Notifications
        self.notifications = tk.BooleanVar(value=self.settings.notifications)
        ttk.Checkbutton(
            frame,
            text=translate("Enable Notifications"),
            variable=self.notifications
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5, padx=5)
    
    def _create_appearance_section(self, parent) -> None:
        """Create the appearance settings section."""
        frame = ttk.LabelFrame(parent, text=translate("Appearance"), padding=10)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Theme selection
        ttk.Label(frame, text="Theme:").grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5)
        
        self.theme_var = tk.StringVar(value=self.settings.theme)
        theme_frame = ttk.Frame(frame)
        theme_frame.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        themes = ["light", "dark", "system"]
        for i, theme in enumerate(themes):
            ttk.Radiobutton(
                theme_frame,
                text=theme.capitalize(),
                variable=self.theme_var,
                value=theme
            ).pack(side=tk.LEFT, padx=5)
        
        # Font size
        ttk.Label(frame, text="Font Size:").grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5)
        
        self.font_size = tk.StringVar(value=str(self.settings.font_size))
        ttk.Combobox(
            frame,
            textvariable=self.font_size,
            values=["10", "12", "14", "16", "18", "20"],
            state="readonly",
            width=5
        ).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
    
    def _create_notifications_section(self, parent) -> None:
        """Create the notifications settings section."""
        frame = ttk.LabelFrame(parent, text=translate("Notifications"), padding=10)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Desktop notifications
        self.desktop_notifications = tk.BooleanVar(value=getattr(self.settings, 'desktop_notifications', True))
        ttk.Checkbutton(
            frame,
            text=translate("Enable Desktop Notifications"),
            variable=self.desktop_notifications
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5, padx=5)
        
        # Notification sound
        ttk.Label(frame, text=translate("Notification Sound:")).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5)
        
        self.notification_sound = tk.StringVar(value=getattr(self.settings, 'notification_sound', 'default'))
        sounds = ["default", "chime", "bell", "none"]
        ttk.Combobox(
            frame,
            textvariable=self.notification_sound,
            values=sounds,
            state="readonly",
            width=15
        ).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Volume
        ttk.Label(frame, text=translate("Volume:")).grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=5)
        
        volume_frame = ttk.Frame(frame)
        volume_frame.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.notification_volume = tk.IntVar(value=getattr(self.settings, 'notification_volume', 75))
        volume_scale = ttk.Scale(
            volume_frame,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.notification_volume,
            length=150
        )
        volume_scale.pack(side=tk.LEFT)
        
        ttk.Label(volume_frame, textvariable=self.notification_volume).pack(side=tk.LEFT, padx=10)
        
        # Test notification button
        ttk.Button(
            frame,
            text=translate("Test Notification"),
            command=self._on_test_notification
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10, padx=5)
        
    def _create_data_section(self, parent) -> None:
        """Create the data management section."""
        frame = ttk.LabelFrame(parent, text=translate("Data Management"), padding=10)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Export data button
        ttk.Button(
            frame,
            text=translate("Export Data..."),
            command=self._on_export_data,
            width=20
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Import data button
        ttk.Button(
            frame,
            text=translate("Import Data..."),
            command=self._on_import_data,
            width=20
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Clear data button
        ttk.Button(
            frame,
            text=translate("Clear All Data"),
            command=self._on_clear_data,
            style="Danger.TButton"
        ).pack(side=tk.RIGHT, padx=5, pady=5)
    
    def _on_test_notification(self) -> None:
        """Send a test notification."""
        try:
            # Get notification settings
            sound = self.notification_sound.get() if hasattr(self, 'notification_sound') else "default"
            volume = self.notification_volume.get() / 100 if hasattr(self, 'notification_volume') else 0.75
            
            # Create and show notification
            notification = NotificationManager.create_notification(
                title=translate("Test Notification"),
                message=translate("This is a test notification from the Pomodoro Timer"),
                sound=sound if sound != "none" else None,
                volume=volume
            )
            
            success = NotificationManager.show_notification(notification)
            if not success:
                messagebox.showwarning(
                    translate("Notification Test"),
                    translate("The notification might not have been displayed. Please check your system notification settings.")
                )
            
            # Track in analytics
            self.analytics.track_event("notification_test", {
                "success": success,
                "sound": sound,
                "volume": volume
            })
            
        except Exception as e:
            self.logger.error(f"Failed to send test notification: {str(e)}")
            messagebox.showerror(
                translate("Error"),
                translate(f"Failed to send notification: {str(e)}")
            )
    
    def _on_import_data(self) -> None:
        """Import application data from a file."""
        try:
            file_path = filedialog.askopenfilename(
                title=translate("Import Data"),
                filetypes=[(translate("JSON Files"), "*.json"), (translate("All Files"), "*.*")]
            )

            if not file_path:
                return  # User canceled

            self.data_manager.import_data(file_path)

            # Track import in analytics
            self.analytics.track_event("data_imported", {"source": "file"})

            messagebox.showinfo(translate("Import Successful"), translate("Data imported successfully!"))
        except ApplicationError as e:
            self.logger.error(f"Failed to import data: {str(e)}")
            messagebox.showerror(translate("Error"), translate(f"Failed to import data: {str(e)}"))
        except Exception as e:
            self.logger.error(f"Unexpected error importing data: {str(e)}")
            messagebox.showerror(translate("Error"), translate("An unexpected error occurred."))

    def _on_reset_defaults(self) -> None:
        """Reset settings to defaults."""
        if messagebox.askyesno(translate("Reset Settings"), translate("Are you sure you want to reset all settings to defaults?")):
            # Reset to defaults
            self.settings = TimerSettings()

            # Update UI
            self.work_duration.set(self.settings.work_duration)
            self.short_break_duration.set(self.settings.short_break_duration)
            self.long_break_duration.set(self.settings.long_break_duration)
            self.long_break_interval.set(self.settings.long_break_interval)
            self.auto_start_breaks.set(self.settings.auto_start_breaks)
            self.auto_start_pomodoros.set(self.settings.auto_start_pomodoros)
            self.notifications.set(self.settings.notifications)

            # Reset notification settings
            self.desktop_notifications.set(True)
            self.notification_sound.set("default")
            self.notification_volume.set(75)

            self.theme_var.set("light")
            self.font_size.set("14")

            # Track reset in analytics
            self.analytics.track_event("settings_reset_to_defaults", {})
            
            messagebox.showinfo(translate("Settings"), translate("Settings reset to defaults."))

    def _on_apply_settings(self) -> None:
        """Apply the current settings."""
        try:
            # Update settings object
            self.settings.work_duration = self.work_duration.get()
            self.settings.short_break_duration = self.short_break_duration.get()
            self.settings.long_break_duration = self.long_break_duration.get()
            self.settings.long_break_interval = self.long_break_interval.get()
            self.settings.auto_start_breaks = self.auto_start_breaks.get()
            self.settings.auto_start_pomodoros = self.auto_start_pomodoros.get()
            self.settings.notifications = self.notifications.get()
            self.settings.theme = self.theme_var.get()
            self.settings.font_size = int(self.font_size.get())
            
            # Update notification settings
            self.settings.notification_sound = self.notification_sound.get()
            self.settings.notification_volume = self.notification_volume.get()
            self.settings.desktop_notifications = self.desktop_notifications.get()
            
            # Save settings
            self.data_manager.save_settings(self.settings)
            
            # Apply theme if changed
            self._apply_theme()
            
            # Track settings change in analytics
            self.analytics.track_event("settings_updated", {
                "work_duration": self.settings.work_duration,
                "short_break_duration": self.settings.short_break_duration,
                "long_break_duration": self.settings.long_break_duration,
                "notifications_enabled": self.settings.notifications
            })
            
            messagebox.showinfo(translate("Settings"), translate("Settings saved successfully!"))
        except ApplicationError as e:
            self.logger.error(f"Failed to save settings: {str(e)}")
            messagebox.showerror(translate("Error"), translate(f"Failed to save settings: {str(e)}"))
        except Exception as e:
            self.logger.error(f"Unexpected error saving settings: {str(e)}")
            messagebox.showerror(translate("Error"), translate("An unexpected error occurred."))

    def _apply_theme(self) -> None:
        """Apply the selected theme to the application."""
        try:
            theme = self.theme_var.get().lower()
            
            # Apply theme to the root window
            if hasattr(self, 'master') and hasattr(self.master, 'master') and hasattr(self.master.master, 'master'):
                root = self.master.master.master
                
                # Update color scheme based on theme
                if theme == 'dark':
                    bg_color = '#2b2b2b'
                    fg_color = '#ffffff'
                elif theme == 'light':
                    bg_color = '#f5f5f5'
                    fg_color = '#000000'
                else:  # system
                    # Try to detect system theme
                    try:
                        import darkdetect
                        if darkdetect.isDark():
                            bg_color = '#2b2b2b'
                            fg_color = '#ffffff'
                        else:
                            bg_color = '#f5f5f5'
                            fg_color = '#000000'
                    except ImportError:
                        # Fallback to dark theme if detection fails
                        bg_color = '#2b2b2b'
                        fg_color = '#ffffff'
                
                # Apply colors to root window
                root.configure(bg=bg_color)
                
                # Track theme change
                self.analytics.track_event("theme_changed", {"theme": theme})
            
            # Update any other theme-dependent UI elements
            self._update_theme_colors()
            
        except Exception as e:
            self.logger.error(f"Error applying theme: {e}")
    
    def _update_theme_colors(self) -> None:
        """Update theme-dependent colors in the UI."""
        theme = self.theme_var.get().lower()
        
        if theme == 'dark':
            text_color = '#ffffff'
            bg_color = '#2b2b2b'
            accent_color = '#4a90e2'
        else:  # light or system
            text_color = '#000000'
            bg_color = '#f5f5f5'
            accent_color = '#2980b9'
            
        # Apply colors to various UI elements if needed
        # This is left as a placeholder for future UI color updates
        # based on the current theme
        pass
        
    def _setup_context_menu(self) -> None:
        """Set up a context menu for the settings panel."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label=translate("Reset to Defaults"), command=self._on_reset_defaults)
        self.context_menu.add_command(label=translate("Apply Settings"), command=self._on_apply_settings)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=translate("Test Notification"), 
                                    command=self._on_test_notification)
        
        # Bind right-click to show context menu
        self.bind("<Button-3>", self._show_context_menu)
        
    def _show_context_menu(self, event) -> None:
        """Show the context menu at the cursor position."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
            
    def _setup_keyboard_shortcuts(self) -> None:
        """Set up keyboard shortcuts for the settings panel."""
        if hasattr(self, 'master'):
            self.master.bind("<Control-a>", lambda event: self._on_apply_settings())
            self.master.bind("<Control-r>", lambda event: self._on_reset_defaults())
            self.master.bind("<Control-t>", lambda event: self._on_test_notification())
            self.master.bind("<Escape>", lambda event: self.master.destroy())
