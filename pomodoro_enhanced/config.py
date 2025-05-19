"""Central configuration constants for the Pomodoro Timer project."""
from __future__ import annotations

import os

# General --------------------------------------------------------------------
APP_ID: str = "pomodoro-timer"

# Paths ----------------------------------------------------------------------
CONFIG_DIR: str = os.path.expanduser("~/.codeium/windsurf/")
CONFIG_FILE: str = os.path.join(CONFIG_DIR, "mcp_config.json")

# Default values -------------------------------------------------------------
DEFAULT_WORK_DURATION_MIN: int = 25
DEFAULT_SHORT_BREAK_MIN: int = 5
DEFAULT_LONG_BREAK_MIN: int = 15
DEFAULT_LONG_BREAK_INTERVAL: int = 4
DEFAULT_SOUND_PACK: str = "elevenlabs"

# Available MCP plugins ------------------------------------------------------
AVAILABLE_PLUGINS: list[str] = [
    "notification_service",
    "cloud_sync",
    "sound_enhancer",
    "theme_provider",
    "analytics",
]

# Colours (cosmic-theme defaults) --------------------------------------------
PRIMARY_COLOR: str = "#9F7AEA"  # violet-600
SECONDARY_COLOR: str = "#FBBF24"  # amber-400
BACKGROUND_COLOR: str = "#0F172A"  # slate-900
SURFACE_COLOR: str = "#1E293B"  # slate-800
FOREGROUND_COLOR: str = "#F1F5F9"  # slate-100

# Detailed Theme Colors (Dark Theme - extending cosmic)
BUTTON_ACTIVE_BG_DARK: str = '#3c3c3c'
WORK_COLOR_DARK: str = '#ff8a80'
BREAK_COLOR_DARK: str = '#80cbc4'

# Detailed Theme Colors (Light Theme)
BACKGROUND_COLOR_LIGHT: str = '#f5f5f5'
FOREGROUND_COLOR_LIGHT: str = '#212121'
SURFACE_COLOR_LIGHT: str = '#ffffff'
PRIMARY_COLOR_LIGHT: str = '#007bff'
SECONDARY_COLOR_LIGHT: str = '#ff9800'
BUTTON_ACTIVE_BG_LIGHT: str = '#e0e0e0'
WORK_COLOR_LIGHT: str = '#d32f2f'
BREAK_COLOR_LIGHT: str = '#00796b'
