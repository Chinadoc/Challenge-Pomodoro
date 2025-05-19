"""Demo script for the ThemeManager.

This script demonstrates how to use the ThemeManager to apply themes to a Tkinter application.
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the ThemeManager
from pomodoro_enhanced.core.theme import ThemeManager

# Mock config with theme colors
class Config:
    # Dark theme colors
    BACKGROUND_COLOR = "#1e1e1e"
    FOREGROUND_COLOR = "#ffffff"
    SURFACE_COLOR = "#2d2d2d"
    PRIMARY_COLOR = "#0078d7"
    SECONDARY_COLOR = "#ff8c00"
    BUTTON_ACTIVE_BG_DARK = "#3c3c3c"
    WORK_COLOR_DARK = "#ff8a80"
    BREAK_COLOR_DARK = "#80cbc4"
    
    # Light theme colors (with fallbacks)
    BACKGROUND_COLOR_LIGHT = "#f5f5f5"
    FOREGROUND_COLOR_LIGHT = "#212121"
    SURFACE_COLOR_LIGHT = "#ffffff"
    PRIMARY_COLOR_LIGHT = "#007bff"
    SECONDARY_COLOR_LIGHT = "#ff9800"
    BUTTON_ACTIVE_BG_LIGHT = "#e0e0e0"
    WORK_COLOR_LIGHT = "#d32f2f"
    BREAK_COLOR_LIGHT = "#00796b"

class ThemeDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("Theme Manager Demo")
        self.root.geometry("600x400")
        
        # Create a frame for the main content
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a frame for the controls
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add theme toggle button
        self.theme_var = tk.BooleanVar(value=False)
        self.theme_toggle = ttk.Checkbutton(
            self.control_frame,
            text="Dark Mode",
            variable=self.theme_var,
            command=self.toggle_theme,
            style="Switch.TCheckbutton"
        )
        self.theme_toggle.pack(side=tk.LEFT, padx=5)
        
        # Add break mode toggle
        self.break_var = tk.BooleanVar(value=False)
        self.break_toggle = ttk.Checkbutton(
            self.control_frame,
            text="Break Mode",
            variable=self.break_var,
            command=self.update_theme
        )
        self.break_toggle.pack(side=tk.LEFT, padx=5)
        
        # Create a notebook for different widget demos
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Basic Widgets
        self.basic_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_tab, text="Basic Widgets")
        self.setup_basic_widgets()
        
        # Tab 2: Form Elements
        self.form_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.form_tab, text="Form Elements")
        self.setup_form_elements()
        
        # Tab 3: Data Display
        self.data_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.data_tab, text="Data Display")
        self.setup_data_display()
        
        # Initialize the theme manager
        self.theme_manager = ThemeManager(root, Config())
        
        # Store widgets for theming
        self.widgets = {
            # Basic Widgets
            "basic_frame": self.basic_tab,
            "label1": self.label1,
            "label2": self.label2,
            "button1": self.button1,
            "button2": self.button2,
            "entry1": self.entry1,
            "check1": self.check1,
            "radio1": self.radio1,
            "radio2": self.radio2,
            "scale1": self.scale1,
            "progress1": self.progress1,
            "timer_label": self.timer_label,
            
            # Form Elements
            "form_frame": self.form_tab,
            "name_label": self.name_label,
            "name_entry": self.name_entry,
            "email_label": self.email_label,
            "email_entry": self.email_entry,
            "gender_label": self.gender_label,
            "gender_combo": self.gender_combo,
            "subscribe_var": self.subscribe_var,
            "subscribe_check": self.subscribe_check,
            "submit_button": self.submit_button,
            
            # Data Display
            "data_frame": self.data_tab,
            "tree": self.tree,
            "scrollbar": self.scrollbar,
        }
        
        # Apply the initial theme
        self.update_theme()
    
    def setup_basic_widgets(self):
        """Set up basic widgets in the first tab."""
        # Create a frame for the timer display
        timer_frame = ttk.Frame(self.basic_tab)
        timer_frame.pack(fill=tk.X, pady=10)
        
        # Add a timer label
        self.timer_label = ttk.Label(
            timer_frame, 
            text="25:00",
            font=("Helvetica", 24, "bold")
        )
        self.timer_label.pack(pady=10)
        
        # Add some sample widgets
        frame = ttk.LabelFrame(self.basic_tab, text="Sample Widgets", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Labels
        self.label1 = ttk.Label(frame, text="This is a label")
        self.label1.pack(pady=5, anchor=tk.W)
        
        self.label2 = ttk.Label(frame, text="This is a secondary label")
        self.label2.pack(pady=5, anchor=tk.W)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.button1 = ttk.Button(btn_frame, text="Primary Button", style="Primary.TButton")
        self.button1.pack(side=tk.LEFT, padx=5)
        
        self.button2 = ttk.Button(btn_frame, text="Secondary Button")
        self.button2.pack(side=tk.LEFT, padx=5)
        
        # Entry
        self.entry1 = ttk.Entry(frame)
        self.entry1.insert(0, "Type something...")
        self.entry1.pack(fill=tk.X, pady=5)
        
        # Checkbutton and Radiobuttons
        check_frame = ttk.Frame(frame)
        check_frame.pack(fill=tk.X, pady=5)
        
        self.check1 = ttk.Checkbutton(check_frame, text="Check me")
        self.check1.pack(side=tk.LEFT, padx=5)
        
        radio_frame = ttk.Frame(check_frame)
        radio_frame.pack(side=tk.RIGHT)
        
        self.radio1 = ttk.Radiobutton(radio_frame, text="Option 1", value=1)
        self.radio1.pack(side=tk.LEFT, padx=5)
        
        self.radio2 = ttk.Radiobutton(radio_frame, text="Option 2", value=2)
        self.radio2.pack(side=tk.LEFT, padx=5)
        
        # Scale
        self.scale1 = ttk.Scale(frame, from_=0, to=100, orient=tk.HORIZONTAL)
        self.scale1.set(50)
        self.scale1.pack(fill=tk.X, pady=5)
        
        # Progress bar
        self.progress1 = ttk.Progressbar(frame, mode="determinate", value=75)
        self.progress1.pack(fill=tk.X, pady=5)
    
    def setup_form_elements(self):
        """Set up form elements in the second tab."""
        form_frame = ttk.Frame(self.form_tab, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name field
        self.name_label = ttk.Label(form_frame, text="Name:")
        self.name_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.name_entry = ttk.Entry(form_frame, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Email field
        self.email_label = ttk.Label(form_frame, text="Email:")
        self.email_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.email_entry = ttk.Entry(form_frame, width=30)
        self.email_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Gender dropdown
        self.gender_label = ttk.Label(form_frame, text="Gender:")
        self.gender_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.gender_combo = ttk.Combobox(
            form_frame, 
            values=["Male", "Female", "Other", "Prefer not to say"],
            state="readonly",
            width=27
        )
        self.gender_combo.current(0)
        self.gender_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Subscribe checkbox
        self.subscribe_var = tk.BooleanVar(value=True)
        self.subscribe_check = ttk.Checkbutton(
            form_frame, 
            text="Subscribe to newsletter",
            variable=self.subscribe_var
        )
        self.subscribe_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Submit button
        self.submit_button = ttk.Button(
            form_frame, 
            text="Submit", 
            style="Primary.TButton"
        )
        self.submit_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
    
    def setup_data_display(self):
        """Set up data display elements in the third tab."""
        # Create a frame with a treeview and scrollbar
        tree_frame = ttk.Frame(self.data_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a treeview with scrollbars
        self.tree = ttk.Treeview(tree_frame, columns=("Name", "Email", "Status"), show="headings")
        
        # Configure the columns
        self.tree.heading("Name", text="Name")
        self.tree.heading("Email", text="Email")
        self.tree.heading("Status", text="Status")
        
        # Set column widths
        self.tree.column("Name", width=150)
        self.tree.column("Email", width=200)
        self.tree.column("Status", width=100, anchor=tk.CENTER)
        
        # Add some sample data
        sample_data = [
            ("John Doe", "john@example.com", "Active"),
            ("Jane Smith", "jane@example.com", "Active"),
            ("Bob Johnson", "bob@example.com", "Inactive"),
            ("Alice Brown", "alice@example.com", "Active"),
            ("Charlie Wilson", "charlie@example.com", "Away"),
        ]
        
        for item in sample_data:
            self.tree.insert("", tk.END, values=item)
        
        # Add a scrollbar
        self.scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.scrollbar.grid(row=0, column=1, sticky=tk.NS)
        
        # Configure grid weights
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.theme_manager.update_theme(dark_mode=self.theme_var.get())
        self.update_theme()
    
    def update_theme(self):
        """Update the theme for all widgets."""
        self.theme_manager.apply(self.widgets, on_break=self.break_var.get())

def main():
    """Run the theme demo."""
    root = tk.Tk()
    app = ThemeDemo(root)
    root.mainloop()

if __name__ == "__main__":
    main()
