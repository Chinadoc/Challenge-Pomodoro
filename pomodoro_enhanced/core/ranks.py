"""
Rank system for the Pomodoro Timer application.
Inspired by productivity challenge apps that use ranks to motivate users.
"""

class Rank:
    def __init__(self, id, name, description, required_sessions, icon_filename=None):
        """
        Initialize a rank with its attributes.
        
        Args:
            id (str): Unique identifier for the rank
            name (str): Display name of the rank
            description (str): Description explaining how to achieve or what the rank means
            required_sessions (int): Number of pomodoro sessions required to achieve this rank
            icon_filename (str, optional): Path to the icon file for this rank
        """
        self.id = id
        self.name = name
        self.description = description
        self.required_sessions = required_sessions
        self.icon_filename = icon_filename or f"assets/ranks/{id}.png"
    
    def __repr__(self):
        return f"Rank({self.id}, {self.name}, sessions={self.required_sessions})"
    
    def __lt__(self, other):
        """Enable sorting ranks by required_sessions"""
        return self.required_sessions < other.required_sessions


# Define all ranks in the system
def get_ranks():
    """
    Return all available ranks in the system, ordered by progression.
    Uses a cosmic evolution theme where users progress from cosmic dust to galactic core.
    
    Returns:
        list: List of Rank objects ordered by required_sessions
    """
    ranks = [
        Rank("cosmic_dust", "Cosmic Dust", "The fundamental building blocks of productivity, waiting to coalesce.", 0),
        Rank("asteroid", "Asteroid", "Small but with significant potential impact on your productivity journey.", 10),
        Rank("planetary_moon", "Planetary Moon", "You've established a stable orbit of productivity habits.", 25),
        Rank("terrestrial_planet", "Terrestrial Planet", "A solid foundation with the right elements for productivity.", 50),
        Rank("gas_giant", "Gas Giant", "Your productivity influence is expanding to impressive proportions.", 100),
        Rank("stellar_dwarf", "Stellar Dwarf", "You're beginning to shine with consistent productivity energy.", 200),
        Rank("main_sequence_star", "Main Sequence Star", "Balanced, bright, and providing steady productivity energy.", 350),
        Rank("red_giant", "Red Giant", "Your productive capacity has expanded to illuminate everything around you.", 500),
        Rank("nebula_former", "Nebula Former", "Your productivity creates environments where new stars of achievement can form.", 750),
        Rank("galactic_core", "Galactic Core", "The central productive force with massive influence - a productivity singularity!", 1000)
    ]
    return sorted(ranks, key=lambda r: r.required_sessions)


def get_rank_for_sessions(completed_sessions):
    """
    Determine the current rank based on completed pomodoro sessions.
    
    Args:
        completed_sessions (int): Total number of completed pomodoro sessions
        
    Returns:
        Rank: The current rank object
    """
    all_ranks = get_ranks()
    current_rank = all_ranks[0]  # Default to lowest rank
    
    for rank in all_ranks:
        if completed_sessions >= rank.required_sessions:
            current_rank = rank
        else:
            break
            
    return current_rank


def get_next_rank(completed_sessions):
    """
    Get the next rank to achieve based on current completed sessions.
    
    Args:
        completed_sessions (int): Total number of completed pomodoro sessions
        
    Returns:
        Rank or None: The next rank to achieve, or None if at max rank
    """
    all_ranks = get_ranks()
    current_rank = get_rank_for_sessions(completed_sessions)
    
    # Find current rank index
    current_index = next((i for i, r in enumerate(all_ranks) if r.id == current_rank.id), -1)
    
    # Return next rank if available
    if current_index < len(all_ranks) - 1:
        return all_ranks[current_index + 1]
    return None  # Already at max rank


def calculate_rank_progress(completed_sessions):
    """
    Calculate progress percentage toward the next rank.
    
    Args:
        completed_sessions (int): Total number of completed pomodoro sessions
        
    Returns:
        float: Percentage progress toward next rank (0-100)
        int: Sessions remaining to next rank
    """
    current_rank = get_rank_for_sessions(completed_sessions)
    next_rank = get_next_rank(completed_sessions)
    
    if next_rank is None:
        return 100.0, 0  # Already at max rank
    
    sessions_for_current = current_rank.required_sessions
    sessions_for_next = next_rank.required_sessions
    
    sessions_needed = sessions_for_next - sessions_for_current
    sessions_completed = completed_sessions - sessions_for_current
    
    remaining = sessions_for_next - completed_sessions
    percentage = (sessions_completed / sessions_needed) * 100
    
    return min(percentage, 100.0), remaining
