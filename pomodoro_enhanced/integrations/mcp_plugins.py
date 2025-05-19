"""
MCP (Multi-Cloud Plugins) integration for the Pomodoro Timer
Allows connections to third-party services for enhanced functionality
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any, Optional

# Define plugin configuration paths
MCP_CONFIG_DIR = os.path.expanduser("~/.codeium/windsurf/")
MCP_CONFIG_FILE = os.path.join(MCP_CONFIG_DIR, "mcp_config.json")

class MCPPluginManager:
    """
    Manages MCP plugins for the Pomodoro Timer
    """
    
    def __init__(self, app_id="pomodoro-timer"):
        self.app_id = app_id
        self.plugins = {}
        self.config = {}
        self.available_plugins = [
            "notification_service",
            "cloud_sync",
            "sound_enhancer",
            "theme_provider",
            "analytics"
        ]
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Load MCP configuration from file
        
        Returns:
            bool: True if config loaded successfully, False otherwise
        """
        try:
            if os.path.exists(MCP_CONFIG_FILE):
                with open(MCP_CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
                print(f"Loaded MCP config from {MCP_CONFIG_FILE}")
                return True
            else:
                print(f"MCP config file not found at {MCP_CONFIG_FILE}")
                self.config = {"plugins": {}}
                return False
        except Exception as e:
            print(f"Error loading MCP config: {e}")
            self.config = {"plugins": {}}
            return False
    
    def save_config(self) -> bool:
        """
        Save MCP configuration to file
        
        Returns:
            bool: True if config saved successfully, False otherwise
        """
        try:
            os.makedirs(MCP_CONFIG_DIR, exist_ok=True)
            with open(MCP_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Saved MCP config to {MCP_CONFIG_FILE}")
            return True
        except Exception as e:
            print(f"Error saving MCP config: {e}")
            return False
    
    def install_plugin(self, plugin_name: str) -> bool:
        """
        Install an MCP plugin
        
        Args:
            plugin_name (str): Name of the plugin to install
        
        Returns:
            bool: True if plugin installed successfully, False otherwise
        """
        if plugin_name not in self.available_plugins:
            print(f"Plugin {plugin_name} is not available")
            return False
        
        try:
            # Simulated plugin installation
            print(f"Installing plugin: {plugin_name}")
            
            # Add plugin to configuration
            if "plugins" not in self.config:
                self.config["plugins"] = {}
            
            self.config["plugins"][plugin_name] = {
                "installed": True,
                "version": "1.0.0",
                "enabled": True,
                "config": {}
            }
            
            # Save updated config
            self.save_config()
            print(f"Plugin {plugin_name} installed successfully")
            return True
        except Exception as e:
            print(f"Error installing plugin {plugin_name}: {e}")
            return False
    
    def is_plugin_installed(self, plugin_name: str) -> bool:
        """
        Check if a plugin is installed
        
        Args:
            plugin_name (str): Name of the plugin to check
        
        Returns:
            bool: True if plugin is installed, False otherwise
        """
        return (
            "plugins" in self.config and 
            plugin_name in self.config["plugins"] and 
            self.config["plugins"][plugin_name].get("installed", False)
        )
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """
        Check if a plugin is enabled
        
        Args:
            plugin_name (str): Name of the plugin to check
        
        Returns:
            bool: True if plugin is enabled, False otherwise
        """
        return (
            self.is_plugin_installed(plugin_name) and
            self.config["plugins"][plugin_name].get("enabled", False)
        )
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable an installed plugin
        
        Args:
            plugin_name (str): Name of the plugin to enable
        
        Returns:
            bool: True if plugin enabled successfully, False otherwise
        """
        if not self.is_plugin_installed(plugin_name):
            print(f"Plugin {plugin_name} is not installed")
            return False
        
        try:
            self.config["plugins"][plugin_name]["enabled"] = True
            self.save_config()
            print(f"Plugin {plugin_name} enabled successfully")
            return True
        except Exception as e:
            print(f"Error enabling plugin {plugin_name}: {e}")
            return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable an installed plugin
        
        Args:
            plugin_name (str): Name of the plugin to disable
        
        Returns:
            bool: True if plugin disabled successfully, False otherwise
        """
        if not self.is_plugin_installed(plugin_name):
            print(f"Plugin {plugin_name} is not installed")
            return False
        
        try:
            self.config["plugins"][plugin_name]["enabled"] = False
            self.save_config()
            print(f"Plugin {plugin_name} disabled successfully")
            return True
        except Exception as e:
            print(f"Error disabling plugin {plugin_name}: {e}")
            return False
    
    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """
        Get list of available plugins
        
        Returns:
            List[Dict[str, Any]]: List of plugin information dictionaries
        """
        plugins_info = []
        for plugin_name in self.available_plugins:
            plugins_info.append({
                "name": plugin_name,
                "installed": self.is_plugin_installed(plugin_name),
                "enabled": self.is_plugin_enabled(plugin_name),
                "description": self._get_plugin_description(plugin_name)
            })
        return plugins_info
    
    def _get_plugin_description(self, plugin_name: str) -> str:
        """
        Get description for a plugin
        
        Args:
            plugin_name (str): Name of the plugin
        
        Returns:
            str: Plugin description
        """
        descriptions = {
            "notification_service": "Provides enhanced notifications across devices",
            "cloud_sync": "Syncs your progress and settings across multiple devices",
            "sound_enhancer": "Provides additional high-quality sound effects",
            "theme_provider": "Adds additional cosmic-themed UI elements",
            "analytics": "Provides insights into your productivity patterns"
        }
        return descriptions.get(plugin_name, "No description available")
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get configuration for a plugin
        
        Args:
            plugin_name (str): Name of the plugin
        
        Returns:
            Dict[str, Any]: Plugin configuration
        """
        if not self.is_plugin_installed(plugin_name):
            return {}
        
        return self.config["plugins"][plugin_name].get("config", {})
    
    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """
        Set configuration for a plugin
        
        Args:
            plugin_name (str): Name of the plugin
            config (Dict[str, Any]): Configuration to set
        
        Returns:
            bool: True if configuration set successfully, False otherwise
        """
        if not self.is_plugin_installed(plugin_name):
            print(f"Plugin {plugin_name} is not installed")
            return False
        
        try:
            self.config["plugins"][plugin_name]["config"] = config
            self.save_config()
            print(f"Configuration for plugin {plugin_name} updated successfully")
            return True
        except Exception as e:
            print(f"Error setting configuration for plugin {plugin_name}: {e}")
            return False


def show_plugin_manager_window(parent, plugin_manager: MCPPluginManager):
    """
    Show a window for managing MCP plugins
    
    Args:
        parent: Parent tkinter window
        plugin_manager: MCPPluginManager instance
    """
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    dialog = tk.Toplevel(parent)
    dialog.title("MCP Plugin Manager")
    dialog.geometry("500x400")
    dialog.minsize(500, 400)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center the dialog
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
    dialog.geometry(f"+{x}+{y}")
    
    # Main frame
    main_frame = ttk.Frame(dialog, padding=15)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Header with title
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill=tk.X, pady=(0, 15))
    
    title_label = ttk.Label(
        header_frame, 
        text="MCP Plugin Manager", 
        font=("Helvetica", 16, "bold")
    )
    title_label.pack(side=tk.LEFT)
    
    # Create scrollable frame for plugins
    container = ttk.Frame(main_frame)
    container.pack(fill=tk.BOTH, expand=True)
    
    canvas = tk.Canvas(container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Get available plugins
    available_plugins = plugin_manager.get_available_plugins()
    
    # Functions for plugin management
    def install_plugin(plugin_name):
        if plugin_manager.install_plugin(plugin_name):
            messagebox.showinfo("Success", f"Plugin '{plugin_name}' installed successfully!")
            refresh_plugins()
        else:
            messagebox.showerror("Error", f"Failed to install plugin '{plugin_name}'")
    
    def enable_plugin(plugin_name):
        if plugin_manager.enable_plugin(plugin_name):
            messagebox.showinfo("Success", f"Plugin '{plugin_name}' enabled successfully!")
            refresh_plugins()
        else:
            messagebox.showerror("Error", f"Failed to enable plugin '{plugin_name}'")
    
    def disable_plugin(plugin_name):
        if plugin_manager.disable_plugin(plugin_name):
            messagebox.showinfo("Success", f"Plugin '{plugin_name}' disabled successfully!")
            refresh_plugins()
        else:
            messagebox.showerror("Error", f"Failed to disable plugin '{plugin_name}'")
    
    def refresh_plugins():
        nonlocal available_plugins
        available_plugins = plugin_manager.get_available_plugins()
        
        # Clear existing plugins
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        
        # Display plugins
        for i, plugin in enumerate(available_plugins):
            plugin_frame = ttk.Frame(scrollable_frame, padding=5)
            plugin_frame.pack(fill=tk.X, pady=5, padx=5)
            
            # Plugin name and description
            info_frame = ttk.Frame(plugin_frame)
            info_frame.pack(fill=tk.X, expand=True, side=tk.LEFT)
            
            name_label = ttk.Label(
                info_frame,
                text=plugin["name"].replace("_", " ").title(),
                font=("Helvetica", 12, "bold")
            )
            name_label.pack(anchor=tk.W)
            
            desc_label = ttk.Label(
                info_frame,
                text=plugin["description"],
                wraplength=300,
                justify=tk.LEFT
            )
            desc_label.pack(anchor=tk.W, pady=(0, 5))
            
            # Status indicator
            status_text = "Enabled" if plugin["enabled"] else "Disabled" if plugin["installed"] else "Not Installed"
            status_color = "green" if plugin["enabled"] else "orange" if plugin["installed"] else "gray"
            
            status_label = ttk.Label(
                info_frame,
                text=f"Status: {status_text}",
                foreground=status_color
            )
            status_label.pack(anchor=tk.W)
            
            # Action buttons
            buttons_frame = ttk.Frame(plugin_frame)
            buttons_frame.pack(side=tk.RIGHT, padx=(10, 0))
            
            if not plugin["installed"]:
                install_button = ttk.Button(
                    buttons_frame,
                    text="Install",
                    command=lambda name=plugin["name"]: install_plugin(name)
                )
                install_button.pack(pady=2)
            elif plugin["enabled"]:
                disable_button = ttk.Button(
                    buttons_frame,
                    text="Disable",
                    command=lambda name=plugin["name"]: disable_plugin(name)
                )
                disable_button.pack(pady=2)
            else:
                enable_button = ttk.Button(
                    buttons_frame,
                    text="Enable",
                    command=lambda name=plugin["name"]: enable_plugin(name)
                )
                enable_button.pack(pady=2)
            
            # Add separator
            if i < len(available_plugins) - 1:
                separator = ttk.Separator(scrollable_frame, orient="horizontal")
                separator.pack(fill=tk.X, pady=5, padx=5)
    
    # Display plugins
    refresh_plugins()
    
    # Footer with buttons
    footer_frame = ttk.Frame(main_frame)
    footer_frame.pack(fill=tk.X, pady=(15, 0))
    
    close_button = ttk.Button(
        footer_frame,
        text="Close",
        command=dialog.destroy
    )
    close_button.pack(side=tk.RIGHT)
    
    # Wait for the dialog to close
    parent.wait_window(dialog)
