"""Refactored theme management for Pomodoro Timer application.

This module provides a more maintainable and type-safe implementation of theme management,
separating concerns and improving code organization.
"""
from dataclasses import dataclass
from typing import Literal, Mapping, Optional, TypeVar, Any, Dict, Callable
import tkinter as tk
from tkinter import ttk
import logging

# Type variables for better type hints
T = TypeVar('T')
WidgetMap = Mapping[str, tk.Widget]

# Configure logging
logger = logging.getLogger(__name__)

# Type for theme modes
ThemeMode = Literal["light", "dark"]

@dataclass(slots=True)
class ThemeConfig:
    """Dataclass to hold theme configuration values."""
    bg: str
    fg: str
    surface: str
    primary: str
    secondary: str
    button_active_bg: str
    work: str
    brk: str

class ThemeDetector:
    """Handles detection of system theme."""
    
    @staticmethod
    def detect() -> ThemeMode:
        """Detect the system's current theme.
        
        Returns:
            str: 'light' or 'dark' based on system theme
        """
        try:
            import darkdetect
            if darkdetect and (detected_theme := darkdetect.theme()):
                return detected_theme.lower()
        except ImportError:
            logger.debug("darkdetect not installed, using light theme as default")
        except Exception as e:
            logger.debug(f"Error detecting system theme: {e}")
        return "light"

class ThemeConfigFactory:
    """Factory for creating ThemeConfig instances from configuration."""
    
    def __init__(self, config_module):
        """Initialize with the application's config module."""
        self._cfg = config_module
        self._validate_config()

    def _validate_config(self) -> None:
        """Ensure required configuration attributes are present."""
        required_attrs = [
            "BACKGROUND_COLOR", "FOREGROUND_COLOR", 
            "SURFACE_COLOR", "PRIMARY_COLOR", "SECONDARY_COLOR"
        ]
        missing = [attr for attr in required_attrs if not hasattr(self._cfg, attr)]
        if missing:
            raise ValueError(f"Config module missing required attributes: {', '.join(missing)}")

    def _get_with_fallback(self, attr: str, default: T) -> T:
        """Helper to get attribute with fallback to default if not found."""
        return getattr(self._cfg, attr, default)

    def create(self, mode: ThemeMode) -> ThemeConfig:
        """Create a ThemeConfig for the specified mode.
        
        Args:
            mode: The theme mode ('light' or 'dark')
            
        Returns:
            Configured ThemeConfig instance
        """
        cfg = self._cfg
        
        # Light theme defaults with fallbacks
        light_theme = {
            "bg": self._get_with_fallback("BACKGROUND_COLOR_LIGHT", "#f5f5f5"),
            "fg": self._get_with_fallback("FOREGROUND_COLOR_LIGHT", "#212121"),
            "surface": self._get_with_fallback("SURFACE_COLOR_LIGHT", "#ffffff"),
            "primary": self._get_with_fallback("PRIMARY_COLOR_LIGHT", "#007bff"),
            "secondary": self._get_with_fallback("SECONDARY_COLOR_LIGHT", "#ff9800"),
            "button_active_bg": self._get_with_fallback("BUTTON_ACTIVE_BG_LIGHT", "#e0e0e0"),
            "work": self._get_with_fallback("WORK_COLOR_LIGHT", "#d32f2f"),
            "brk": self._get_with_fallback("BREAK_COLOR_LIGHT", "#00796b"),
        }
        
        # Dark theme uses direct config values with fallbacks
        dark_theme = {
            "bg": cfg.BACKGROUND_COLOR,
            "fg": cfg.FOREGROUND_COLOR,
            "surface": cfg.SURFACE_COLOR,
            "primary": cfg.PRIMARY_COLOR,
            "secondary": cfg.SECONDARY_COLOR,
            "button_active_bg": self._get_with_fallback("BUTTON_ACTIVE_BG_DARK", "#3c3c3c"),
            "work": self._get_with_fallback("WORK_COLOR_DARK", "#ff8a80"),
            "brk": self._get_with_fallback("BREAK_COLOR_DARK", "#80cbc4"),
        }
        
        theme_dict = dark_theme if mode == "dark" else light_theme
        return ThemeConfig(**theme_dict)

class ThemeManager:
    """Manages theme detection, resolution, and application for Tkinter applications."""
    
    def __init__(self, root: tk.Tk, config_module):
        """Initialize the theme manager.
        
        Args:
            root: The root Tkinter window
            config_module: Module containing theme configuration
        """
        self._root = root
        self._cfg = config_module
        self._style = ttk.Style()
        self._factory = ThemeConfigFactory(config_module)
        self.theme = self._factory.create(ThemeDetector.detect())
        self._register_ttk_styles()

    def apply(self, widgets: WidgetMap, *, on_break: bool = False) -> None:
        """Apply the current theme to the provided widgets and root window.
        
        Args:
            widgets: Mapping of widget names to Tkinter widgets
            on_break: If True, use break color for timer labels
        """
        t = self.theme
        timer_fg = t.brk if on_break else t.work
        
        # Widget type to configuration mapping
        widget_configs = {
            tk.Frame: {"bg": t.bg},
            tk.Label: {
                "bg": t.bg, 
                "fg": lambda name: timer_fg if name == "timer_label" else t.fg
            },
            # Add more widget types as needed
        }

        # Apply configurations to each widget
        for name, widget in widgets.items():
            try:
                config = widget_configs.get(type(widget))
                if config:
                    kwargs = {k: v(name) if callable(v) else v 
                            for k, v in config.items()}
                    widget.configure(**kwargs)
            except tk.TclError as exc:
                logger.debug("Widget %s could not be themed: %s", name, exc)

        # Update root window
        self._root.configure(bg=t.bg)
        self._root.update_idletasks()

    def update_theme(self, dark_mode: Optional[bool] = None) -> None:
        """Update the current theme based on preference or system detection.
        
        Args:
            dark_mode: If specified, forces light (False) or dark (True) mode.
                      If None, detects system theme.
        """
        mode: ThemeMode = "dark" if dark_mode else "light" if dark_mode is not None else ThemeDetector.detect()
        self.theme = self._factory.create(mode)
        self._register_ttk_styles()

    def _register_ttk_styles(self) -> None:
        """Register and configure ttk styles for the current theme."""
        self._style.theme_use("clam")
        t = self.theme
        
        # Base style configuration
        base_style = {
            ".": {
                "configure": {
                    "background": t.bg,
                    "foreground": t.fg,
                    "fieldbackground": t.surface,
                    "troughcolor": t.surface,
                    "selectbackground": t.primary,
                    "selectforeground": t.fg,
                    "insertcolor": t.fg,
                    "highlightthickness": 0,
                    "borderwidth": 0,
                }
            },
            "TButton": {
                "configure": {
                    "background": t.surface,
                    "foreground": t.fg,
                    "font": ("Helvetica", 10),
                    "relief": tk.FLAT,
                    "borderwidth": 1,
                    "padding": 6,
                },
                "map": {
                    "background": [
                        ("active", t.button_active_bg), 
                        ("pressed", t.button_active_bg), 
                        ("disabled", t.surface)
                    ],
                    "foreground": [
                        ("active", t.fg), 
                        ("disabled", f"{t.fg}80")
                    ],
                }
            },
            "Primary.TButton": {
                "configure": {
                    "font": ("Helvetica", 12, "bold"),
                    "background": t.primary,
                    "foreground": t.fg,
                    "relief": tk.RAISED,
                    "borderwidth": 2,
                    "padding": 8,
                },
                "map": {
                    "background": [
                        ("active", t.secondary), 
                        ("pressed", t.secondary), 
                        ("disabled", f"{t.primary}80")
                    ],
                }
            },
            "TLabel": {
                "configure": {
                    "background": t.bg, 
                    "foreground": t.fg, 
                    "font": ("Helvetica", 10), 
                    "padding": 2
                }
            },
            "TFrame": {
                "configure": {"background": t.bg}
            },
            "TNotebook": {
                "configure": {"background": t.bg, "borderwidth": 0}
            },
            "TNotebook.Tab": {
                "configure": {
                    "padding": [10, 4],
                    "background": t.surface,
                    "foreground": t.fg,
                },
                "map": {
                    "background": [("selected", t.primary), ("active", t.button_active_bg)],
                    "foreground": [("selected", t.fg), ("active", t.fg)],
                }
            },
            "TEntry": {
                "configure": {
                    "fieldbackground": t.surface,
                    "foreground": t.fg,
                    "insertcolor": t.fg,
                    "borderwidth": 1,
                    "padding": 4,
                },
                "map": {
                    "fieldbackground": [("readonly", t.bg)],
                    "foreground": [("readonly", t.fg)],
                }
            },
            "TCombobox": {
                "configure": {
                    "fieldbackground": t.surface,
                    "foreground": t.fg,
                    "selectbackground": t.primary,
                    "selectforeground": t.fg,
                    "arrowcolor": t.fg,
                    "arrowsize": 12,
                },
                "map": {
                    "fieldbackground": [("readonly", t.surface)],
                    "foreground": [("readonly", t.fg)],
                    "selectbackground": [("readonly", t.primary)],
                    "selectforeground": [("readonly", t.fg)],
                }
            },
            "TCheckbutton": {
                "configure": {
                    "background": t.bg,
                    "foreground": t.fg,
                    "indicatormargin": 4,
                }
            },
            "TRadiobutton": {
                "configure": {
                    "background": t.bg,
                    "foreground": t.fg,
                    "indicatormargin": 4,
                }
            },
            "TScale": {
                "configure": {
                    "background": t.bg,
                    "troughcolor": t.surface,
                    "bordercolor": t.fg,
                    "darkcolor": t.primary,
                    "lightcolor": t.primary,
                }
            },
            "TScrollbar": {
                "configure": {
                    "background": t.surface,
                    "troughcolor": t.bg,
                    "bordercolor": t.fg,
                    "darkcolor": t.primary,
                    "lightcolor": t.primary,
                    "arrowcolor": t.fg,
                    "arrowsize": 12,
                }
            },
            "TProgressbar": {
                "configure": {
                    "background": t.primary,
                    "troughcolor": t.surface,
                    "bordercolor": t.fg,
                    "lightcolor": t.primary,
                    "darkcolor": t.primary,
                }
            },
            "Horizontal.TProgressbar": {
                "configure": {
                    "background": t.primary,
                    "troughcolor": t.surface,
                    "bordercolor": t.fg,
                    "lightcolor": t.primary,
                    "darkcolor": t.primary,
                }
            },
            "Vertical.TProgressbar": {
                "configure": {
                    "background": t.primary,
                    "troughcolor": t.surface,
                    "bordercolor": t.fg,
                    "lightcolor": t.primary,
                    "darkcolor": t.primary,
                }
            },
            "TNotebook": {
                "configure": {
                    "background": t.bg,
                    "tabmargins": [2, 5, 2, 0],
                }
            },
            "TNotebook.Tab": {
                "configure": {
                    "padding": [10, 5],
                    "background": t.surface,
                    "foreground": t.fg,
                    "font": ("Helvetica", 10, "normal"),
                },
                "map": {
                    "background": [("selected", t.primary), ("active", t.button_active_bg)],
                    "foreground": [("selected", t.fg), ("active", t.fg)],
                }
            },
            "Treeview": {
                "configure": {
                    "background": t.surface,
                    "foreground": t.fg,
                    "fieldbackground": t.surface,
                    "bordercolor": t.fg,
                    "lightcolor": t.primary,
                    "darkcolor": t.primary,
                },
                "map": {
                    "background": [("selected", t.primary)],
                    "foreground": [("selected", t.fg)],
                }
            },
            "Treeview.Item": {
                "configure": {
                    "padding": [2, 4],
                }
            },
            "Treeview.Heading": {
                "configure": {
                    "background": t.primary,
                    "foreground": t.fg,
                    "font": ("Helvetica", 10, "bold"),
                    "relief": "raised",
                    "borderwidth": 1,
                }
            },
            "Treeview.Cell": {
                "configure": {
                    "padding": [4, 2],
                }
            },
            "Treeview.Row": {
                "configure": {
                    "padding": [2, 1],
                }
            },
            "Treeview.Column": {
                "configure": {
                    "padding": [4, 2],
                }
            },
            "Treeview.Field": {
                "configure": {
                    "padding": [4, 2],
                }
            },
            "Treeview.Item": {
                "configure": {
                    "padding": [2, 4],
                }
            },
        }

        # Apply all styles
        for style_name, config in base_style.items():
            if "configure" in config:
                self._style.configure(style_name, **config["configure"])
            if "map" in config:
                self._style.map(style_name, **config["map"])

        # Configure root window
        self._root.configure(bg=t.bg)
