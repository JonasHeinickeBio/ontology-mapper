"""
CLI module for ontology mapping tool.
"""

from .interface import CLIInterface
from .main import get_logger, logger, main

__all__ = ["CLIInterface", "main", "get_logger", "logger"]
