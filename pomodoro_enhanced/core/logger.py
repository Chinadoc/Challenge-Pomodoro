"""
Logging configuration for the Enhanced Pomodoro Timer.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any, Union

from .config import config

class LogLevelFilter(logging.Filter):
    """Filter log records by level."""
    
    def __init__(self, level: int):
        super().__init__()
        self.level = level
    
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.level

def setup_logging(log_level: Optional[Union[str, int]] = None, 
                 log_file: Optional[Union[str, Path]] = None) -> None:
    """Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, logs will be written to stderr.
    """
    # Default log level
    if log_level is None:
        log_level = 'DEBUG' if config.get('debug', False) else 'INFO'
    
    # Convert string log level to int
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if log file is specified
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler (10MB per file, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Capture uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Call the default excepthook for KeyboardInterrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        root_logger.critical(
            "Uncaught exception", 
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name: Logger name. If None, returns the root logger.
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def log_system_info() -> None:
    """Log system information for debugging purposes."""
    import platform
    import sys
    
    logger = get_logger(__name__)
    
    logger.info("System Information:")
    logger.info(f"  OS: {platform.system()} {platform.release()} ({platform.version()})")
    logger.info(f"  Python: {sys.version}")
    logger.info(f"  Executable: {sys.executable}")
    logger.info(f"  Working Directory: {os.getcwd()}")
    logger.info(f"  User: {os.getlogin()}")
    
    # Log environment variables (safely)
    logger.debug("Environment Variables:")
    for key in sorted(os.environ.keys()):
        # Skip sensitive information
        if any(skip in key.lower() for skip in ['pass', 'secret', 'key', 'token']):
            logger.debug(f"  {key} = ********")
        else:
            logger.debug(f"  {key} = {os.environ[key]}")

# Set up default logging when module is imported
if not logging.getLogger().handlers:
    log_dir = Path(config.get('data_dir')) / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'pomodoro.log'
    
    setup_logging(
        log_level='DEBUG' if config.get('debug', False) else 'INFO',
        log_file=log_file
    )
    
    # Log system info at startup
    log_system_info()
