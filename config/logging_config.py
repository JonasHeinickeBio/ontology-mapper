#!/usr/bin/env python3
"""
Logging configuration for the ontology-mapper project.
Provides centralized logging setup with different handlers for different use cases.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # Add color to the level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # Format the message
        formatted = super().format(record)

        # Reset levelname for other formatters
        record.levelname = levelname

        return formatted


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    console: bool = True,
    json_format: bool = False,
    quiet: bool = False,
    verbose: bool = False,
) -> logging.Logger:
    """
    Set up logging configuration for the ontology-mapper project.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        console: Whether to log to console
        json_format: Whether to use JSON format for file logging
        quiet: Suppress INFO and DEBUG messages
        verbose: Enable DEBUG level logging

    Returns:
        Configured root logger
    """
    # Determine log level
    if quiet:
        log_level = logging.WARNING
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = getattr(logging, level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    if console and not quiet:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # Use colored formatter for console
        console_format = "%(levelname)s - %(name)s - %(message)s"
        console_formatter = ColoredFormatter(console_format)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)  # Always capture all levels to file

        file_formatter: logging.Formatter
        if json_format:
            file_formatter = JSONFormatter()
        else:
            file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            file_formatter = logging.Formatter(file_format)

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Error handler (stderr for warnings and errors)
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.WARNING)
    error_format = "%(levelname)s - %(name)s - %(message)s"
    error_formatter = ColoredFormatter(error_format)
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(func_name: str, args: dict[str, Any], logger: logging.Logger):
    """
    Log function call with arguments.

    Args:
        func_name: Name of the function
        args: Function arguments
        logger: Logger instance
    """
    logger.debug(f"Calling {func_name} with args: {args}")


def log_api_request(service: str, endpoint: str, params: dict[str, Any], logger: logging.Logger):
    """
    Log API request details.

    Args:
        service: Service name (e.g., 'BioPortal', 'OLS')
        endpoint: API endpoint
        params: Request parameters
        logger: Logger instance
    """
    logger.debug(f"API Request - {service}: {endpoint} | params: {params}")


def log_api_response(service: str, status_code: int, response_size: int, logger: logging.Logger):
    """
    Log API response details.

    Args:
        service: Service name
        status_code: HTTP status code
        response_size: Size of response in bytes
        logger: Logger instance
    """
    logger.debug(f"API Response - {service}: {status_code} | size: {response_size} bytes")


def log_performance(operation: str, duration: float, logger: logging.Logger):
    """
    Log performance metrics.

    Args:
        operation: Operation name
        duration: Duration in seconds
        logger: Logger instance
    """
    logger.info(f"Performance - {operation}: {duration:.2f}s")


def log_progress(current: int, total: int, operation: str, logger: logging.Logger):
    """
    Log progress information.

    Args:
        current: Current progress
        total: Total items
        operation: Operation description
        logger: Logger instance
    """
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info(f"Progress - {operation}: {current}/{total} ({percentage:.1f}%)")


# Default logger configuration
DEFAULT_CONFIG: dict[str, Any] = {
    "level": "INFO",
    "log_file": None,
    "console": True,
    "json_format": False,
    "quiet": False,
    "verbose": False,
}

# Initialize default logging
_default_logger = None


def get_default_logger() -> logging.Logger:
    """Get the default configured logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging(**DEFAULT_CONFIG)
    return _default_logger
