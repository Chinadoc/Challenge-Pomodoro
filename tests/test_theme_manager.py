"""Tests for the refactored ThemeManager."""
import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock
from pomodoro_enhanced.core.theme import (
    ThemeManager, 
    ThemeConfig, 
    ThemeDetector,
    ThemeConfigFactory
)

class MockConfig:
    """Mock configuration for testing theme manager."""
    BACKGROUND_COLOR = "#1e1e1e"
    FOREGROUND_COLOR = "#ffffff"
    SURFACE_COLOR = "#2d2d2d"
    PRIMARY_COLOR = "#0078d7"
    SECONDARY_COLOR = "#ff8c00"
    BUTTON_ACTIVE_BG_DARK = "#3c3c3c"
    WORK_COLOR_DARK = "#ff8a80"
    BREAK_COLOR_DARK = "#80cbc4"
    
    # Light theme overrides
    BACKGROUND_COLOR_LIGHT = "#f5f5f5"
    FOREGROUND_COLOR_LIGHT = "#212121"
    SURFACE_COLOR_LIGHT = "#ffffff"
    PRIMARY_COLOR_LIGHT = "#007bff"
    SECONDARY_COLOR_LIGHT = "#ff9800"
    BUTTON_ACTIVE_BG_LIGHT = "#e0e0e0"
    WORK_COLOR_LIGHT = "#d32f2f"
    BREAK_COLOR_LIGHT = "#00796b"

class TestThemeConfig(unittest.TestCase):
    """Tests for ThemeConfig dataclass."""
    
    def test_theme_config_creation(self):
        """Test creating a ThemeConfig instance."""
        config = ThemeConfig(
            bg="#000000",
            fg="#ffffff",
            surface="#111111",
            primary="#007bff",
            secondary="#6c757d",
            button_active_bg="#333333",
            work="#ff0000",
            brk="#00ff00"
        )
        
        self.assertEqual(config.bg, "#000000")
        self.assertEqual(config.fg, "#ffffff")
        self.assertEqual(config.work, "#ff0000")

class TestThemeDetector(unittest.TestCase):
    """Tests for ThemeDetector class."""
    
    @patch('darkdetect.theme')
    def test_detect_dark_theme(self, mock_theme):
        """Test detecting dark theme."""
        mock_theme.return_value = "Dark"
        self.assertEqual(ThemeDetector.detect(), "dark")
    
    @patch('darkdetect.theme')
    def test_detect_light_theme(self, mock_theme):
        """Test detecting light theme."""
        mock_theme.return_value = "Light"
        self.assertEqual(ThemeDetector.detect(), "light")
    
    @patch('darkdetect.theme', side_effect=ImportError)
    def test_detect_import_error(self, _):
        """Test fallback when darkdetect is not available."""
        self.assertEqual(ThemeDetector.detect(), "light")

class TestThemeConfigFactory(unittest.TestCase):
    """Tests for ThemeConfigFactory class."""
    
    def setUp(self):
        """Set up test case with mock config."""
        self.config = MockConfig()
        self.factory = ThemeConfigFactory(self.config)
    
    def test_create_dark_theme(self):
        """Test creating a dark theme config."""
        theme = self.factory.create("dark")
        self.assertIsInstance(theme, ThemeConfig)
        self.assertEqual(theme.bg, self.config.BACKGROUND_COLOR)
        self.assertEqual(theme.primary, self.config.PRIMARY_COLOR)
    
    def test_create_light_theme(self):
        """Test creating a light theme config."""
        theme = self.factory.create("light")
        self.assertIsInstance(theme, ThemeConfig)
        self.assertEqual(theme.bg, self.config.BACKGROUND_COLOR_LIGHT)
        self.assertEqual(theme.primary, self.config.PRIMARY_COLOR_LIGHT)
    
    def test_missing_required_attributes(self):
        """Test validation of required config attributes."""
        class IncompleteConfig:
            pass
            
        with self.assertRaises(ValueError):
            ThemeConfigFactory(IncompleteConfig())

class TestThemeManager(unittest.TestCase):
    """Tests for ThemeManager class."""
    
    def setUp(self):
        """Set up test case with mock root window and config."""
        self.root = tk.Tk()
        self.config = MockConfig()
    
    def tearDown(self):
        """Clean up after each test."""
        self.root.destroy()
    
    @patch('darkdetect.theme', return_value="Dark")
    def test_init_dark_theme(self, _):
        """Test initializing with dark theme detection."""
        manager = ThemeManager(self.root, self.config)
        self.assertEqual(manager.theme.bg, self.config.BACKGROUND_COLOR)
    
    @patch('darkdetect.theme', return_value="Light")
    def test_init_light_theme(self, _):
        """Test initializing with light theme detection."""
        manager = ThemeManager(self.root, self.config)
        self.assertEqual(manager.theme.bg, self.config.BACKGROUND_COLOR_LIGHT)
    
    def test_update_theme_dark(self):
        """Test updating to dark theme."""
        manager = ThemeManager(self.root, self.config)
        manager.update_theme(dark_mode=True)
        self.assertEqual(manager.theme.bg, self.config.BACKGROUND_COLOR)
    
    def test_update_theme_light(self):
        """Test updating to light theme."""
        manager = ThemeManager(self.root, self.config)
        manager.update_theme(dark_mode=False)
        self.assertEqual(manager.theme.bg, self.config.BACKGROUND_COLOR_LIGHT)
    
    def test_apply_theme_to_widgets(self):
        """Test applying theme to widgets."""
        manager = ThemeManager(self.root, self.config)
        
        # Create test widgets
        frame = tk.Frame(self.root)
        label = tk.Label(self.root, text="Test")
        timer_label = tk.Label(self.root, text="Timer")
        
        # Apply theme
        manager.apply({
            "test_frame": frame,
            "test_label": label,
            "timer_label": timer_label,
        }, on_break=False)
        
        # Verify widget colors
        self.assertEqual(frame.cget("bg"), manager.theme.bg)
        self.assertEqual(label.cget("bg"), manager.theme.bg)
        self.assertEqual(label.cget("fg"), manager.theme.fg)
        self.assertEqual(timer_label.cget("fg"), manager.theme.work)
    
    def test_apply_theme_on_break(self):
        """Test applying theme with on_break flag."""
        manager = ThemeManager(self.root, self.config)
        timer_label = tk.Label(self.root, text="Timer")
        
        # Apply theme with on_break=True
        manager.apply({"timer_label": timer_label}, on_break=True)
        self.assertEqual(timer_label.cget("fg"), manager.theme.brk)

if __name__ == "__main__":
    unittest.main()
