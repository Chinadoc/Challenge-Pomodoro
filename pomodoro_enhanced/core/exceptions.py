"""
Custom exceptions and error handling for the Enhanced Pomodoro Timer.
"""

import logging
import sys
import traceback
from typing import Any, Dict, Optional, Type, TypeVar, cast

# Initialize logger
logger = logging.getLogger(__name__)

# Type variable for exception handling
E = TypeVar('E', bound=Exception)

class PomodoroError(Exception):
    """Base exception class for all application-specific exceptions."""
    
    def __init__(self, message: str = "An error occurred", 
                 code: int = 0, 
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        """Initialize the exception.
        
        Args:
            message: Human-readable error message
            code: Application-specific error code
            details: Additional error details
            cause: The original exception that caused this one
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause
        
        # Log the error
        logger.error(f"{self.__class__.__name__}: {message}")
        if cause:
            logger.debug(f"Caused by: {cause}", exc_info=True)
    
    def __str__(self) -> str:
        if self.code:
            return f"{self.message} (code: {self.code})"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary."""
        return {
            'error': self.message,
            'code': self.code,
            'type': self.__class__.__name__,
            'details': self.details,
            'cause': str(self.cause) if self.cause else None
        }

# Specific application exceptions
class ConfigError(PomodoroError):
    """Raised when there is an error in the application configuration."""
    def __init__(self, message: str = "Configuration error", 
                 code: int = 1000, 
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message, code, details, cause)

class DatabaseError(PomodoroError):
    """Raised when there is an error accessing the database."""
    def __init__(self, message: str = "Database error", 
                 code: int = 2000, 
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message, code, details, cause)

class AuthError(PomodoroError):
    """Raised when there is an authentication or authorization error."""
    def __init__(self, message: str = "Authentication error", 
                 code: int = 3000, 
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message, code, details, cause)

class ValidationError(PomodoroError):
    """Raised when input validation fails."""
    def __init__(self, message: str = "Validation error", 
                 code: int = 4000, 
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message, code, details, cause)

class ResourceNotFoundError(PomodoroError):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str = "resource", 
                 resource_id: Optional[Any] = None,
                 message: Optional[str] = None,
                 code: int = 4040, 
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        if not message:
            message = f"{resource_type} not found"
            if resource_id is not None:
                message += f" with ID: {resource_id}"
        
        if details is None:
            details = {}
        
        details['resource_type'] = resource_type
        if resource_id is not None:
            details['resource_id'] = resource_id
            
        super().__init__(message, code, details, cause)

class NetworkError(PomodoroError):
    """Raised when there is a network-related error."""
    def __init__(self, message: str = "Network error", 
                 code: int = 5000, 
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message, code, details, cause)

class TimeoutError(PomodoroError):
    """Raised when an operation times out."""
    def __init__(self, message: str = "Operation timed out", 
                 code: int = 5040, 
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message, code, details, cause)

class NotSupportedError(PomodoroError):
    """Raised when a feature is not supported."""
    def __init__(self, feature: str, 
                 message: Optional[str] = None,
                 code: int = 5050, 
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        if not message:
            message = f"Feature not supported: {feature}"
            
        if details is None:
            details = {}
            
        details['feature'] = feature
        super().__init__(message, code, details, cause)

class ApplicationError(Exception):
    """Base class for application-specific exceptions."""
    def __init__(self, message: str = "An application error occurred"):
        self.message = message
        super().__init__(message)

def handle_error(error: Exception, 
                context: Optional[Dict[str, Any]] = None,
                reraise: bool = True) -> None:
    """Handle an exception, log it, and optionally re-raise it.
    
    Args:
        error: The exception to handle
        context: Additional context to include in the log
        reraise: Whether to re-raise the exception after handling
    """
    # Log the error with context
    log_message = [f"Unhandled exception: {error}"]
    
    if context:
        log_message.append(f"Context: {context}")
    
    # Include the full traceback in debug logs
    log_message.append("\n" + "".join(traceback.format_exception(
        type(error), error, error.__traceback__
    )))
    
    logger.error("\n".join(log_message))
    
    # Re-raise the exception if requested
    if reraise:
        raise error

def catch_errors(func):
    """Decorator to catch and log exceptions in a function."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_error(e, {
                'function': f"{func.__module__}.{func.__name__}",
                'args': args,
                'kwargs': kwargs
            })
    return wrapper

class ErrorContext:
    """Context manager for handling exceptions with additional context."""
    
    def __init__(self, 
                context: Optional[Dict[str, Any]] = None,
                reraise: bool = True,
                exception_types: tuple[Type[Exception], ...] = (Exception,)):
        """Initialize the error context.
        
        Args:
            context: Additional context to include in error logs
            reraise: Whether to re-raise the exception after handling
            exception_types: Tuple of exception types to catch
        """
        self.context = context or {}
        self.reraise = reraise
        self.exception_types = exception_types
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None and issubclass(exc_type, self.exception_types):
            # Log the error with context
            log_message = [f"Caught exception: {exc_val}"]
            
            if self.context:
                log_message.append(f"Context: {self.context}")
            
            log_message.append("\n" + "".join(traceback.format_exception(
                exc_type, exc_val, exc_tb
            )))
            
            logger.error("\n".join(log_message))
            
            # Re-raise the exception if requested
            return not self.reraise
        
        return False

def ignore_errors(*exception_types: Type[Exception]):
    """Decorator to silently ignore specified exceptions."""
    if not exception_types:
        exception_types = (Exception,)
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                logger.debug(f"Ignored error in {func.__name__}: {e}")
                return None
        return wrapper
    return decorator

def retry_on_exception(retries: int = 3, 
                      delay: float = 1.0,
                      backoff: float = 2.0,
                      exceptions: tuple[Type[Exception], ...] = (Exception,),
                      logger: Optional[logging.Logger] = None):
    """Decorator to retry a function on exception.
    
    Args:
        retries: Number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay between retries
        exceptions: Tuple of exceptions to catch and retry on
        logger: Optional logger to use for retry messages
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == retries:
                        logger.error(f"Failed after {attempt} attempts: {e}")
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt} failed: {e}. "
                        f"Retrying in {current_delay:.1f} seconds..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached due to the raise in the except block
            raise last_exception  # type: ignore
            
        return wrapper
    return decorator
