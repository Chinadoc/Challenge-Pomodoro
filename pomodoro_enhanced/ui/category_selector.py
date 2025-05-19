"""
Category selector UI component for the Pomodoro Timer
"""

import tkinter as tk
from tkinter import ttk, simpledialog

def show_category_selector(parent, categories, current_category, callback):
    """
    Display a popup dialog for selecting a work category
    
    Args:
        parent: Parent tkinter window
        categories: List of available categories
        current_category: Currently selected category
        callback: Function to call when a category is selected
    """
    dialog = tk.Toplevel(parent)
    dialog.title("Select Work Category")
    dialog.geometry("300x400")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center the dialog
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
    dialog.geometry(f"+{x}+{y}")
    
    # Create main frame
    main_frame = ttk.Frame(dialog, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Add title
    title_label = ttk.Label(main_frame, text="Work Categories", font=("Helvetica", 14, "bold"))
    title_label.pack(pady=(0, 10))
    
    # Create scrollable frame for categories
    container = ttk.Frame(main_frame)
    container.pack(fill=tk.BOTH, expand=True, pady=5)
    
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
    
    # Category list
    for i, category in enumerate(categories):
        category_frame = ttk.Frame(scrollable_frame)
        category_frame.pack(fill=tk.X, pady=2)
        
        # Highlight current category
        bg_color = "#f0f0f0" if category != current_category else "#e1f5fe"
        category_frame.configure(style="Selected.TFrame" if category == current_category else "TFrame")
        
        # Category button
        cat_button = ttk.Button(
            category_frame, 
            text=category,
            command=lambda cat=category: select_category(cat)
        )
        cat_button.pack(fill=tk.X, padx=5, pady=2)
    
    # Add custom category button
    separator = ttk.Separator(main_frame, orient="horizontal")
    separator.pack(fill=tk.X, pady=10)
    
    add_button = ttk.Button(
        main_frame,
        text="+ Add Custom Category",
        command=add_custom_category
    )
    add_button.pack(fill=tk.X, pady=5)
    
    # Close button
    close_button = ttk.Button(main_frame, text="Close", command=dialog.destroy)
    close_button.pack(fill=tk.X, pady=10)
    
    def select_category(category):
        """Handle category selection"""
        callback(category)
        dialog.destroy()
    
    def add_custom_category():
        """Create a new custom category"""
        new_category = simpledialog.askstring(
            "New Category",
            "Enter a name for your new work category:",
            parent=dialog
        )
        
        if new_category and new_category.strip():
            callback(new_category.strip())
            dialog.destroy()
    
    # Wait for the dialog to close
    parent.wait_window(dialog)
