"""
Work Categories module for Pomodoro Timer
Allows users to categorize their work sessions and track stats per category
"""

class WorkCategory:
    """Represents a type of work the user can track"""
    def __init__(self, name, color="#1E90FF", icon=None):
        self.name = name
        self.color = color
        self.icon = icon or "📝"  # Default icon
        self.sessions = 0
        self.total_minutes = 0
        self.last_used = None

# Default work categories with emojis and colors
DEFAULT_CATEGORIES = [
    WorkCategory("Work", "#4285F4", "💼"),
    WorkCategory("Study", "#34A853", "📚"),
    WorkCategory("Personal Project", "#FBBC05", "🚀"),
    WorkCategory("Reading", "#EA4335", "📖"),
    WorkCategory("Creative", "#AA00FF", "🎨"),
    WorkCategory("Exercise", "#00BCD4", "💪"),
    WorkCategory("Meditation", "#7986CB", "🧘"),
    WorkCategory("Writing", "#FF9800", "✍️"),
    WorkCategory("Planning", "#795548", "📅")
]

class CategoryManager:
    """Manages work categories for the Pomodoro timer"""
    
    def __init__(self, preferences=None):
        """Initialize with user preferences if available"""
        self.preferences = preferences
        self.categories = {}
        self.current_category = "Work"
        
        # Load default categories
        for category in DEFAULT_CATEGORIES:
            self.categories[category.name] = {
                'color': category.color,
                'icon': category.icon,
                'sessions': 0,
                'total_minutes': 0,
                'last_used': None
            }
        
        # Load saved category stats if available
        if preferences:
            saved_categories = preferences.get('category_stats', {})
            if saved_categories:
                for cat_name, cat_data in saved_categories.items():
                    self.categories[cat_name] = cat_data
    
    def select_category(self, category_name):
        """Set the current work category"""
        if category_name not in self.categories:
            self.add_category(category_name)
        
        self.current_category = category_name
        return True
    
    def add_category(self, category_name, color="#1E90FF", icon="📝"):
        """Add a new category"""
        if not category_name or category_name.strip() == "":
            return False
        
        self.categories[category_name] = {
            'color': color,
            'icon': icon,
            'sessions': 0,
            'total_minutes': 0,
            'last_used': None
        }
        return True
    
    def update_category_stats(self, category_name, minutes_worked):
        """Update statistics for a category after a work session"""
        from datetime import datetime
        
        if category_name not in self.categories:
            self.add_category(category_name)
        
        self.categories[category_name]['sessions'] += 1
        self.categories[category_name]['total_minutes'] += minutes_worked
        self.categories[category_name]['last_used'] = datetime.now().strftime("%Y-%m-%d")
        
        # Save to preferences if available
        if self.preferences:
            self.preferences.set('category_stats', self.categories)
            self.preferences.save()
        
        return self.categories[category_name]
    
    def get_all_categories(self):
        """Get all category names"""
        return list(self.categories.keys())
    
    def get_category_stats(self, category_name=None):
        """Get stats for a specific category or all categories"""
        if category_name:
            return self.categories.get(category_name, None)
        return self.categories
