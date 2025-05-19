""
Task management panel for the Enhanced Pomodoro Timer.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime
import logging

from ..core.models import Task, TaskStatus, TaskPriority

class TaskPanel(ttk.Frame):
    """Panel for managing tasks."""
    
    def __init__(self, parent, data_manager, on_task_selected: Callable[[Optional[Task]], None], *args, **kwargs):
        """Initialize the task panel."""
        super().__init__(parent, *args, **kwargs)
        
        self.data_manager = data_manager
        self.on_task_selected = on_task_selected
        self.logger = logging.getLogger(f"{__name__}.TaskPanel")
        
        # Current task tracking
        self.current_task_id: Optional[str] = None
        
        # Create UI
        self._create_widgets()
        
        # Load initial data
        self.refresh_tasks()
    
    def _create_widgets(self) -> None:
        """Create and arrange the task panel widgets."""
        # Main container with padding
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = ttk.Frame(container)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Add Task button
        add_btn = ttk.Button(
            toolbar,
            text="Add Task",
            command=self._on_add_task
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Edit Task button
        self.edit_btn = ttk.Button(
            toolbar,
            text="Edit Task",
            command=self._on_edit_task,
            state=tk.DISABLED
        )
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        
        # Delete Task button
        self.delete_btn = ttk.Button(
            toolbar,
            text="Delete Task",
            command=self._on_delete_task,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=LEFT, padx=5)
        
        # Complete Task button
        self.complete_btn = ttk.Button(
            toolbar,
            text="Mark Complete",
            command=self._on_complete_task,
            state=tk.DISABLED
        )
        self.complete_btn.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        refresh_btn = ttk.Button(
            toolbar,
            text="Refresh",
            command=self.refresh_tasks
        )
        refresh_btn.pack(side=tk.RIGHT)
        
        # Task list
        self._create_task_list(container)
    
    def _create_task_list(self, parent) -> None:
        """Create the task list treeview."""
        # Create a frame for the treeview and scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('title', 'status', 'priority', 'created', 'pomodoros'),
            show='headings',
            yscrollcommand=scrollbar.set,
            selectmode='browse'
        )
        
        # Configure columns
        self.tree.heading('title', text='Title', command=lambda: self._sort_column('title', False))
        self.tree.heading('status', text='Status', command=lambda: self._sort_column('status', False))
        self.tree.heading('priority', text='Priority', command=lambda: self._sort_column('priority', False))
        self.tree.heading('created', text='Created', command=lambda: self._sort_column('created', False))
        self.tree.heading('pomodoros', text='Pomodoros', command=lambda: self._sort_column('pomodoros', True))
        
        # Set column widths
        self.tree.column('title', width=200, minwidth=150)
        self.tree.column('status', width=100, minwidth=80, anchor=tk.CENTER)
        self.tree.column('priority', width=80, minwidth=60, anchor=tk.CENTER)
        self.tree.column('created', width=120, minwidth=100, anchor=tk.CENTER)
        self.tree.column('pomodoros', width=80, minwidth=60, anchor=tk.CENTER)
        
        # Configure tags for status
        self.tree.tag_configure('completed', foreground='#888888')
        self.tree.tag_configure('in_progress', font=('TkDefaultFont', 9, 'bold'))
        
        # Pack the treeview
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self._on_task_select)
        self.tree.bind('<Double-1>', lambda e: self._on_edit_task())
    
    def refresh_tasks(self) -> None:
        """Refresh the task list from the data manager."""
        # Clear current items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get tasks from data manager
        tasks = self.data_manager.get_tasks()
        
        # Add tasks to the treeview
        for task in tasks:
            self._add_task_to_tree(task)
        
        # Update button states
        self._update_button_states()
    
    def _add_task_to_tree(self, task: Task) -> None:
        """Add a single task to the treeview."""
        # Format dates and other fields
        created_date = task.created_at.strftime('%Y-%m-%d') if task.created_at else ''
        status = task.status.value if hasattr(task.status, 'value') else str(task.status)
        
        # Determine tags based on status
        tags = []
        if task.status == TaskStatus.COMPLETED:
            tags.append('completed')
        elif task.status == TaskStatus.IN_PROGRESS:
            tags.append('in_progress')
        
        # Add the task to the treeview
        self.tree.insert(
            '',
            'end',
            iid=task.id,
            values=(
                task.title,
                status,
                task.priority.name if hasattr(task.priority, 'name') else str(task.priority),
                created_date,
                task.pomodoros_completed
            ),
            tags=tuple(tags)
        )
    
    def _update_button_states(self) -> None:
        """Update the state of action buttons based on selection."""
        selected = bool(self.tree.selection())
        self.edit_btn.config(state=tk.NORMAL if selected else tk.DISABLED)
        self.delete_btn.config(state=tk.NORMAL if selected else tk.DISABLED)
        
        # Only enable complete button for non-completed tasks
        if selected:
            task_id = self.tree.selection()[0]
            task = self.data_manager.get_task(task_id)
            self.complete_btn.config(
                state=tk.NORMAL if task and task.status != TaskStatus.COMPLETED else tk.DISABLED
            )
        else:
            self.complete_btn.config(state=tk.DISABLED)
    
    def _sort_column(self, col: str, numeric: bool = False) -> None:
        """Sort treeview contents when a column header is clicked."""
        # Get all items and their values
        items = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # Sort based on column type
        if numeric:
            items.sort(key=lambda t: int(t[0]) if t[0].isdigit() else 0)
        else:
            items.sort()
        
        # Reorder items in the treeview
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)
    
    # Event handlers
    
    def _on_task_select(self, event=None) -> None:
        """Handle task selection in the treeview."""
        selected = self.tree.selection()
        if selected:
            task_id = selected[0]
            task = self.data_manager.get_task(task_id)
            self.current_task_id = task_id
            self.on_task_selected(task)
        else:
            self.current_task_id = None
            self.on_task_selected(None)
        
        self._update_button_states()
    
    def _on_add_task(self) -> None:
        """Show the add task dialog."""
        dialog = TaskDialog(self, "Add New Task")
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                # Create and save the new task
                task = Task(
                    title=dialog.result['title'],
                    description=dialog.result.get('description', ''),
                    priority=dialog.result.get('priority', TaskPriority.MEDIUM),
                    status=TaskStatus.TODO,
                    pomodoros_completed=0,
                    time_spent=0
                )
                
                self.data_manager.add_task(task)
                self.refresh_tasks()
                
                # Select the new task
                if task.id in self.tree.get_children():
                    self.tree.selection_set(task.id)
                    self.tree.see(task.id)
                
                self.logger.info(f"Added new task: {task.title}")
                
            except Exception as e:
                self.logger.error(f"Error adding task: {e}")
                messagebox.showerror("Error", f"Failed to add task: {e}")
    
    def _on_edit_task(self) -> None:
        """Edit the selected task."""
        if not self.current_task_id:
            return
            
        task = self.data_manager.get_task(self.current_task_id)
        if not task:
            messagebox.showerror("Error", "Selected task not found")
            return
            
        dialog = TaskDialog(self, "Edit Task", task)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                # Update task with new values
                task.title = dialog.result['title']
                task.description = dialog.result.get('description', '')
                task.priority = dialog.result.get('priority', TaskPriority.MEDIUM)
                
                # Only update status if it's different to avoid unnecessary updates
                if 'status' in dialog.result and dialog.result['status'] != task.status:
                    task.status = dialog.result['status']
                
                self.data_manager.update_task(task)
                self.refresh_tasks()
                
                # Reselect the task
                if task.id in self.tree.get_children():
                    self.tree.selection_set(task.id)
                    self.tree.see(task.id)
                
                self.logger.info(f"Updated task: {task.title}")
                
            except Exception as e:
                self.logger.error(f"Error updating task: {e}")
                messagebox.showerror("Error", f"Failed to update task: {e}")
    
    def _on_delete_task(self) -> None:
        """Delete the selected task."""
        if not self.current_task_id:
            return
            
        task = self.data_manager.get_task(self.current_task_id)
        if not task:
            return
            
        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the task '{task.title}'?"
        ):
            try:
                self.data_manager.delete_task(self.current_task_id)
                self.current_task_id = None
                self.refresh_tasks()
                self.on_task_selected(None)
                self.logger.info(f"Deleted task: {task.title}")
            except Exception as e:
                self.logger.error(f"Error deleting task: {e}")
                messagebox.showerror("Error", f"Failed to delete task: {e}")
    
    def _on_complete_task(self) -> None:
        """Mark the selected task as complete."""
        if not self.current_task_id:
            return
            
        task = self.data_manager.get_task(self.current_task_id)
        if not task or task.status == TaskStatus.COMPLETED:
            return
            
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        
        try:
            self.data_manager.update_task(task)
            self.refresh_tasks()
            self.logger.info(f"Marked task as complete: {task.title}")
        except Exception as e:
            self.logger.error(f"Error completing task: {e}")
            messagebox.showerror("Error", f"Failed to mark task as complete: {e}")
    
    def update_task_progress(self, task_id: str, progress: float) -> None:
        """Update the progress of a task in the UI."""
        # This method would be called from the main window to update task progress
        # during a work session
        pass


class TaskDialog(simpledialog.Dialog):
    """Dialog for adding/editing tasks."""
    
    def __init__(self, parent, title: str, task: Optional[Task] = None):
        """Initialize the dialog."""
        self.task = task
        self.result = None
        super().__init__(parent, title)
    
    def body(self, master) -> None:
        """Create the dialog body."""
        # Create form fields
        ttk.Label(master, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar(value=self.task.title if self.task else '')
        title_entry = ttk.Entry(master, textvariable=self.title_var, width=40)
        title_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(master, text="Description:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.desc_var = tk.StringVar(value=self.task.description if self.task else '')
        desc_text = tk.Text(master, width=40, height=5, wrap=tk.WORD)
        desc_text.insert('1.0', self.desc_var.get())
        desc_text.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.desc_text = desc_text
        
        # Priority
        ttk.Label(master, text="Priority:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.priority_var = tk.StringVar(
            value=self.task.priority.name if self.task else TaskPriority.MEDIUM.name
        )
        priority_menu = ttk.OptionMenu(
            master,
            self.priority_var,
            self.priority_var.get(),
            *[p.name for p in TaskPriority]
        )
        priority_menu.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Status (only for editing)
        if self.task:
            ttk.Label(master, text="Status:").grid(row=3, column=0, sticky=tk.W, pady=5)
            self.status_var = tk.StringVar(value=self.task.status.name)
            status_menu = ttk.OptionMenu(
                master,
                self.status_var,
                self.status_var.get(),
                *[s.name for s in TaskStatus]
            )
            status_menu.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Configure grid weights
        master.columnconfigure(1, weight=1)
        master.rowconfigure(1, weight=1)
        
        # Set focus to title field
        return title_entry
    
    def apply(self) -> None:
        """Process the form data when OK is clicked."""
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Validation Error", "Title is required")
            return
            
        self.result = {
            'title': title,
            'description': self.desc_text.get('1.0', tk.END).strip(),
            'priority': TaskPriority[self.priority_var.get()]
        }
        
        # Add status if editing
        if hasattr(self, 'status_var'):
            self.result['status'] = TaskStatus[self.status_var.get()]
        
        super().ok()
