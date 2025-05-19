"""
Analytics and telemetry for the Enhanced Pomodoro Timer.
Handles collecting and reporting anonymous usage statistics.
"""

import json
import logging
import platform
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Initialize logger
logger = logging.getLogger(__name__)

class AnalyticsEvent:
    """Represents an analytics event."""
    
    def __init__(self, 
                 name: str, 
                 params: Optional[Dict[str, Any]] = None,
                 timestamp: Optional[float] = None):
        """Initialize an analytics event.
        
        Args:
            name: Event name (e.g., 'app_launch', 'timer_start')
            params: Optional event parameters
            timestamp: Optional event timestamp (defaults to current time)
        """
        self.name = name
        self.params = params or {}
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary."""
        return {
            'name': self.name,
            'params': self.params,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat()
        }
    
    def __str__(self) -> str:
        return f"Event(name='{self.name}', params={self.params})"

class AnalyticsManager:
    """Manages analytics and telemetry data collection."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnalyticsManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._enabled: bool = False
            self._session_id: str = str(uuid.uuid4())
            self._user_id: Optional[str] = None
            self._app_version: str = "unknown"
            self._events: List[AnalyticsEvent] = []
            self._persist_path: Optional[Path] = None
            self._last_flush_time: float = 0
            self._flush_interval: float = 60.0  # seconds
            self._max_events: int = 1000
            self._initialized = True
    
    def initialize(self, 
                  app_version: str,
                  user_id: Optional[str] = None,
                  persist_path: Optional[Union[str, Path]] = None,
                  enabled: bool = True) -> None:
        """Initialize the analytics manager.
        
        Args:
            app_version: Application version string
            user_id: Optional user ID (for anonymous tracking)
            persist_path: Optional path to persist events
            enabled: Whether analytics are enabled
        """
        self._enabled = enabled
        self._app_version = app_version
        self._user_id = user_id or str(uuid.uuid4())
        
        if persist_path:
            self._persist_path = Path(persist_path)
            self._load_events()
        
        # Log system information
        self._log_system_info()
        
        # Log app launch event
        self.log_event('app_launch')
    
    def _log_system_info(self) -> None:
        """Log system information as an event."""
        try:
            import platform
            import sys
            
            system_info = {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'python_implementation': platform.python_implementation(),
                'python_compiler': platform.python_compiler(),
                'system': platform.system(),
                'node': platform.node(),
                'python_build': platform.python_build(),
            }
            
            self.log_event('system_info', system_info)
            
        except Exception as e:
            logger.error(f"Error collecting system info: {e}")
    
    def log_event(self, name: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Log an analytics event.
        
        Args:
            name: Event name
            params: Optional event parameters
        """
        if not self._enabled:
            return
        
        try:
            event = AnalyticsEvent(name, params)
            self._events.append(event)
            
            # Log the event
            logger.debug(f"Logged event: {event}")
            
            # Flush events if needed
            self._auto_flush()
            
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def log_timing(self, category: str, name: str, duration_ms: float, 
                  params: Optional[Dict[str, Any]] = None) -> None:
        """Log a timing event.
        
        Args:
            category: Timing category
            name: Timing name
            duration_ms: Duration in milliseconds
            params: Additional parameters
        """
        timing_params = {
            'category': category,
            'name': name,
            'duration_ms': duration_ms,
        }
        
        if params:
            timing_params.update(params)
        
        self.log_event('timing', timing_params)
    
    def log_error(self, error: Union[str, Exception], 
                 context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error.
        
        Args:
            error: Error message or exception
            context: Additional context
        """
        error_params = {
            'error': str(error),
            'error_type': error.__class__.__name__ if isinstance(error, Exception) else 'string',
        }
        
        if context:
            error_params['context'] = context
        
        self.log_event('error', error_params)
    
    def _auto_flush(self) -> None:
        """Flush events if needed."""
        current_time = time.time()
        
        # Flush if we've reached the max number of events
        if len(self._events) >= self._max_events:
            self.flush()
        # Or if the flush interval has passed
        elif current_time - self._last_flush_time >= self._flush_interval:
            self.flush()
    
    def flush(self) -> None:
        """Flush events to storage or server."""
        if not self._enabled or not self._events:
            return
        
        try:
            # If we have a persist path, save to disk
            if self._persist_path:
                self._save_events()
            
            # Here you would typically send events to your analytics server
            # For example:
            # self._send_events_to_server()
            
            # Clear the events that were just flushed
            self._events = []
            self._last_flush_time = time.time()
            
        except Exception as e:
            logger.error(f"Error flushing analytics: {e}")
    
    def _load_events(self) -> None:
        """Load events from persistent storage."""
        if not self._persist_path or not self._persist_path.exists():
            return
        
        try:
            with open(self._persist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Only load events if they're from the same session
                if data.get('session_id') == self._session_id:
                    events_data = data.get('events', [])
                    self._events = [
                        AnalyticsEvent(
                            name=event['name'],
                            params=event.get('params', {}),
                            timestamp=event.get('timestamp')
                        )
                        for event in events_data
                    ]
            
            logger.debug(f"Loaded {len(self._events)} events from {self._persist_path}")
            
        except Exception as e:
            logger.error(f"Error loading analytics events: {e}")
    
    def _save_events(self) -> None:
        """Save events to persistent storage."""
        if not self._persist_path:
            return
        
        try:
            # Ensure the directory exists
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data to save
            data = {
                'session_id': self._session_id,
                'user_id': self._user_id,
                'app_version': self._app_version,
                'timestamp': time.time(),
                'events': [event.to_dict() for event in self._events]
            }
            
            # Save to file
            with open(self._persist_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self._events)} events to {self._persist_path}")
            
        except Exception as e:
            logger.error(f"Error saving analytics events: {e}")
    
    def enable(self) -> None:
        """Enable analytics collection."""
        self._enabled = True
        logger.info("Analytics enabled")
    
    def disable(self) -> None:
        """Disable analytics collection and flush any pending events."""
        if self._enabled:
            self.flush()
            self._enabled = False
            logger.info("Analytics disabled")
    
    def is_enabled(self) -> bool:
        """Check if analytics are enabled."""
        return self._enabled
    
    def clear_events(self) -> None:
        """Clear all stored events."""
        self._events = []
        
        # Also clear the persisted events file if it exists
        if self._persist_path and self._persist_path.exists():
            try:
                self._persist_path.unlink()
                logger.info(f"Cleared analytics data at {self._persist_path}")
            except Exception as e:
                logger.error(f"Error clearing analytics data: {e}")
    
    def get_session_id(self) -> str:
        """Get the current session ID."""
        return self._session_id
    
    def get_user_id(self) -> Optional[str]:
        """Get the anonymous user ID."""
        return self._user_id
    
    def set_user_id(self, user_id: str) -> None:
        """Set the anonymous user ID."""
        self._user_id = user_id
    
    def get_events(self) -> List[AnalyticsEvent]:
        """Get all stored events."""
        return self._events.copy()
    
    def __del__(self) -> None:
        """Clean up and ensure all events are flushed."""
        if self._enabled:
            self.flush()

# Global analytics manager instance
analytics_manager = AnalyticsManager()

def get_analytics_manager() -> AnalyticsManager:
    """Get the global analytics manager instance."""
    return analytics_manager

def track_event(name: str, params: Optional[Dict[str, Any]] = None) -> None:
    """Track an analytics event.
    
    Args:
        name: Event name
        params: Optional event parameters
    """
    analytics_manager.log_event(name, params)

def track_timing(category: str, name: str, duration_ms: float, 
                params: Optional[Dict[str, Any]] = None) -> None:
    """Track a timing event.
    
    Args:
        category: Timing category
        name: Timing name
        duration_ms: Duration in milliseconds
        params: Additional parameters
    """
    analytics_manager.log_timing(category, name, duration_ms, params)

def track_error(error: Union[str, Exception], 
               context: Optional[Dict[str, Any]] = None) -> None:
    """Track an error.
    
    Args:
        error: Error message or exception
        context: Additional context
    """
    analytics_manager.log_error(error, context)
