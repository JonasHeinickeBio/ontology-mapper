"""
Logging configuration for the ontology mapper.
Provides structured logging for debugging and monitoring.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_level: str = None,
    log_to_file: bool = None,
    log_file: str = None,
    verbose: bool = False
):
    """
    Configure logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Enable logging to file
        log_file: Path to log file
        verbose: Enable verbose logging (DEBUG level)
    """
    # Get configuration from environment if not provided
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'WARNING')
    
    if log_to_file is None:
        log_to_file = os.getenv('ERROR_LOG_TO_FILE', 'false').lower() in ('true', '1', 'yes')
    
    if log_file is None:
        log_file = os.getenv('ERROR_LOG_PATH', 'logs/ontology_mapper.log')
    
    # Override level if verbose is True
    if verbose or os.getenv('ERROR_VERBOSE', 'false').lower() in ('true', '1', 'yes'):
        log_level = 'DEBUG'
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.WARNING)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always enabled, but less verbose)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only show warnings and errors on console
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        try:
            # Create log directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use rotating file handler to prevent log files from growing too large
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # Log that file logging is enabled
            root_logger.info(f"File logging enabled: {log_file}")
            
        except Exception as e:
            root_logger.warning(f"Could not set up file logging: {e}")
    
    # Log startup message
    root_logger.info(f"Logging initialized - Level: {log_level}, File: {log_to_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Name for the logger (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_error_with_context(logger: logging.Logger, error: Exception, context: str = None):
    """
    Log an error with additional context information
    
    Args:
        logger: Logger instance
        error: Exception to log
        context: Additional context about what was being attempted
    """
    import traceback
    
    error_details = {
        'type': type(error).__name__,
        'message': str(error),
        'context': context
    }
    
    logger.error(f"Error occurred: {error_details}")
    logger.debug(f"Traceback: {traceback.format_exc()}")


def log_performance_metric(logger: logging.Logger, operation: str, duration: float, success: bool = True):
    """
    Log performance metrics for operations
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        duration: Duration in seconds
        success: Whether the operation succeeded
    """
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Performance: {operation} - {status} - {duration:.2f}s")


# Initialize logging on module import if environment variable is set
if os.getenv('AUTO_INIT_LOGGING', 'false').lower() in ('true', '1', 'yes'):
    setup_logging()
