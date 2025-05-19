"""
Daily challenges system for the Pomodoro Timer application.

This module provides a system for generating and tracking daily challenges 
that motivate users with interesting productivity goals.
"""

import random
import json
import os
from datetime import datetime, timedelta
import uuid


class Challenge:
    """Represents a single challenge with criteria for completion."""
    
    def __init__(self, challenge_id, title, description, reward_points, 
                 challenge_type, target_value=None, expires_in_days=1):
        """
        Initialize a challenge.
        
        Args:
            challenge_id (str): Unique identifier for the challenge
            title (str): Display title for the challenge
            description (str): Detailed description of what to accomplish
            reward_points (int): Points earned for completing the challenge
            challenge_type (str): Type of challenge (e.g., 'sessions', 'duration', 'streak')
            target_value (int, optional): Target value to reach for completion
            expires_in_days (int, optional): Days until the challenge expires
        """
        self.challenge_id = challenge_id
        self.title = title
        self.description = description
        self.reward_points = reward_points
        self.challenge_type = challenge_type
        self.target_value = target_value
        self.expires_in_days = expires_in_days
        self.completed = False
        self.progress = 0
        
        # Set creation and expiration dates
        self.created_date = datetime.now().strftime("%Y-%m-%d")
        expiry_date = datetime.now() + timedelta(days=expires_in_days)
        self.expiry_date = expiry_date.strftime("%Y-%m-%d")
    
    def update_progress(self, value):
        """
        Update challenge progress with a new value.
        
        Args:
            value: Progress increment (type depends on challenge_type)
            
        Returns:
            bool: True if challenge completed, False otherwise
        """
        if self.completed:
            return True
            
        # For counter-type challenges, increment progress
        if self.challenge_type in ['sessions', 'duration', 'streak']:
            self.progress += value
        # For boolean-type challenges, set progress directly
        elif self.challenge_type in ['early_start', 'late_night']:
            self.progress = value
            
        # Check if challenge is completed
        if self.target_value is not None and self.progress >= self.target_value:
            self.completed = True
            return True
        
        return False
    
    def is_expired(self):
        """Check if the challenge has expired."""
        today = datetime.now().strftime("%Y-%m-%d")
        expiry = datetime.strptime(self.expiry_date, "%Y-%m-%d")
        current = datetime.strptime(today, "%Y-%m-%d")
        return current > expiry
    
    def to_dict(self):
        """Convert challenge to dictionary for serialization."""
        return {
            'challenge_id': self.challenge_id,
            'title': self.title,
            'description': self.description,
            'reward_points': self.reward_points,
            'challenge_type': self.challenge_type,
            'target_value': self.target_value,
            'expires_in_days': self.expires_in_days,
            'completed': self.completed,
            'progress': self.progress,
            'created_date': self.created_date,
            'expiry_date': self.expiry_date
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a Challenge instance from a dictionary."""
        challenge = cls(
            data['challenge_id'],
            data['title'],
            data['description'],
            data['reward_points'],
            data['challenge_type'],
            data['target_value'],
            data['expires_in_days']
        )
        challenge.completed = data.get('completed', False)
        challenge.progress = data.get('progress', 0)
        challenge.created_date = data.get('created_date', datetime.now().strftime("%Y-%m-%d"))
        challenge.expiry_date = data.get('expiry_date', 
                                         (datetime.now() + timedelta(days=challenge.expires_in_days)).strftime("%Y-%m-%d"))
        return challenge


class ChallengeManager:
    """Manages the creation, tracking, and completion of challenges."""
    
    def __init__(self, save_path=None):
        """
        Initialize the challenge manager.
        
        Args:
            save_path (str, optional): Path to save challenge data
        """
        self.current_challenges = []
        self.completed_challenges = []
        self.total_points = 0
        
        # Set default save path if not provided
        if save_path is None:
            self.save_path = os.path.join(os.path.expanduser('~'), '.pomodoro_timer', 'challenges.json')
        else:
            self.save_path = save_path
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        
        # Challenge templates for randomly generating challenges
        self.challenge_templates = [
            {
                'title': 'Early Bird',
                'description': 'Complete {target} pomodoro sessions before 10 AM',
                'reward_points': 20,
                'challenge_type': 'sessions',
                'target_range': (2, 4),
                'time_condition': {'before_hour': 10}
            },
            {
                'title': 'Marathon Worker',
                'description': 'Complete {target} pomodoro sessions in a single day',
                'reward_points': 30,
                'challenge_type': 'sessions',
                'target_range': (6, 10)
            },
            {
                'title': 'Deep Focus',
                'description': 'Work for {target} minutes without interruptions',
                'reward_points': 25,
                'challenge_type': 'duration',
                'target_range': (50, 90)
            },
            {
                'title': 'Night Owl',
                'description': 'Complete {target} pomodoro sessions after 8 PM',
                'reward_points': 20,
                'challenge_type': 'sessions',
                'target_range': (2, 3),
                'time_condition': {'after_hour': 20}
            },
            {
                'title': 'Consistency Champion',
                'description': 'Complete at least one pomodoro session for {target} consecutive days',
                'reward_points': 50,
                'challenge_type': 'streak',
                'target_range': (3, 5),
                'expires_in_days': 7
            },
            {
                'title': 'Weekend Warrior',
                'description': 'Complete {target} pomodoro sessions during the weekend',
                'reward_points': 40,
                'challenge_type': 'sessions',
                'target_range': (4, 8),
                'day_condition': {'weekend': True},
                'expires_in_days': 2
            },
            {
                'title': 'Quick Succession',
                'description': 'Complete {target} pomodoro sessions with less than 5-minute breaks between them',
                'reward_points': 35,
                'challenge_type': 'sessions',
                'target_range': (3, 5),
                'break_condition': {'max_minutes': 5}
            },
            {
                'title': 'Morning Momentum',
                'description': 'Start your first pomodoro session within 30 minutes of waking up',
                'reward_points': 15,
                'challenge_type': 'early_start',
                'target_value': 1
            },
            {
                'title': 'Category Master',
                'description': 'Complete {target} pomodoro sessions in the same category',
                'reward_points': 30,
                'challenge_type': 'sessions',
                'target_range': (4, 6),
                'category_condition': {'same': True}
            },
            {
                'title': 'Time Diversifier',
                'description': 'Complete pomodoro sessions in {target} different categories',
                'reward_points': 35,
                'challenge_type': 'sessions',
                'target_range': (3, 4),
                'category_condition': {'different': True}
            }
        ]
    
    def load_challenges(self):
        """Load challenges from file."""
        if not os.path.exists(self.save_path):
            return
            
        try:
            with open(self.save_path, 'r') as f:
                data = json.load(f)
                
                # Load current challenges
                self.current_challenges = [
                    Challenge.from_dict(challenge_data) 
                    for challenge_data in data.get('current_challenges', [])
                ]
                
                # Load completed challenges
                self.completed_challenges = [
                    Challenge.from_dict(challenge_data) 
                    for challenge_data in data.get('completed_challenges', [])
                ]
                
                # Load total points
                self.total_points = data.get('total_points', 0)
                
                # Filter out expired challenges
                self._filter_expired_challenges()
        except Exception as e:
            print(f"Error loading challenges: {e}")
    
    def save_challenges(self):
        """Save challenges to file."""
        try:
            data = {
                'current_challenges': [
                    challenge.to_dict() for challenge in self.current_challenges
                ],
                'completed_challenges': [
                    challenge.to_dict() for challenge in self.completed_challenges
                ],
                'total_points': self.total_points
            }
            
            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving challenges: {e}")
    
    def _filter_expired_challenges(self):
        """Remove expired challenges from current challenges."""
        self.current_challenges = [
            challenge for challenge in self.current_challenges
            if not challenge.is_expired()
        ]
    
    def generate_daily_challenges(self, count=3):
        """
        Generate a set of random daily challenges.
        
        Args:
            count (int): Number of challenges to generate
            
        Returns:
            list: Generated challenges
        """
        self._filter_expired_challenges()
        
        # Don't generate new challenges if we already have enough
        if len(self.current_challenges) >= count:
            return self.current_challenges
            
        # How many challenges to generate
        to_generate = count - len(self.current_challenges)
        
        # Generate random challenges
        new_challenges = []
        for _ in range(to_generate):
            template = random.choice(self.challenge_templates)
            
            # Generate target value if needed
            target_value = None
            if 'target_range' in template:
                min_val, max_val = template['target_range']
                target_value = random.randint(min_val, max_val)
                
            # Generate description with target value
            description = template['description']
            if target_value and '{target}' in description:
                description = description.format(target=target_value)
                
            # Create challenge
            challenge = Challenge(
                challenge_id=str(uuid.uuid4()),
                title=template['title'],
                description=description,
                reward_points=template['reward_points'],
                challenge_type=template['challenge_type'],
                target_value=target_value,
                expires_in_days=template.get('expires_in_days', 1)
            )
            
            new_challenges.append(challenge)
            
        # Add new challenges to current challenges
        self.current_challenges.extend(new_challenges)
        
        # Save changes
        self.save_challenges()
        
        return self.current_challenges
    
    def update_challenge_progress(self, challenge_type, value=1, conditions=None):
        """
        Update progress for all challenges of a certain type.
        
        Args:
            challenge_type (str): Type of challenge to update
            value (int): Progress increment value
            conditions (dict, optional): Additional conditions for updating
            
        Returns:
            list: Challenges that were completed with this update
        """
        completed_challenges = []
        
        for challenge in self.current_challenges:
            if challenge.completed:
                continue
                
            if challenge.challenge_type == challenge_type:
                # Check additional conditions if provided
                if conditions and not self._check_conditions(challenge, conditions):
                    continue
                    
                # Update progress
                was_completed = challenge.update_progress(value)
                
                if was_completed:
                    self.total_points += challenge.reward_points
                    completed_challenges.append(challenge)
                    self.completed_challenges.append(challenge)
                    
        # Remove completed challenges from current challenges
        self.current_challenges = [
            challenge for challenge in self.current_challenges
            if not challenge.completed
        ]
        
        # Save changes
        self.save_challenges()
        
        return completed_challenges
    
    def _check_conditions(self, challenge, conditions):
        """
        Check if a challenge meets additional conditions.
        
        Args:
            challenge: Challenge to check
            conditions: Dictionary of conditions
            
        Returns:
            bool: True if all conditions are met, False otherwise
        """
        if 'time' in conditions:
            hour = datetime.now().hour
            
            if 'before_hour' in conditions['time'] and hour >= conditions['time']['before_hour']:
                return False
                
            if 'after_hour' in conditions['time'] and hour < conditions['time']['after_hour']:
                return False
                
        if 'day' in conditions:
            day = datetime.now().weekday()
            
            if 'weekend' in conditions['day'] and conditions['day']['weekend']:
                # 5 = Saturday, 6 = Sunday
                if day not in [5, 6]:
                    return False
                    
        if 'category' in conditions:
            category = conditions.get('category', {}).get('value')
            
            if 'same' in conditions['category'] and conditions['category']['same']:
                # Check if the category matches the one in the challenge
                challenge_category = getattr(challenge, 'category', None)
                if challenge_category is None:
                    challenge.category = category
                elif challenge_category != category:
                    return False
                    
        return True
    
    def get_active_challenges(self):
        """Get all active challenges that haven't been completed."""
        # Filter out expired challenges first
        self._filter_expired_challenges()
        
        # Return the current challenges
        return self.current_challenges
    
    def get_challenge_stats(self):
        """Get statistics about challenges."""
        total_completed = len(self.completed_challenges)
        total_active = len(self.current_challenges)
        total_points = self.total_points
        
        return {
            'total_completed': total_completed,
            'total_active': total_active,
            'total_points': total_points
        }
