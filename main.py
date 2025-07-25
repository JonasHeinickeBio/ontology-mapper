#!/usr/bin/env python3
"""
Main entry point
User-friendly CLI entry point for the modular ontology mapping tool.
Supports both direct and module-based invocation.
"""

import argparse
import os
import sys

# Add the current directory to the Python path for flexible imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.main import main as cli_main
from config.logging_config import setup_logging

# setup_logging(level="INFO", console=True)


def main():
    parser = argparse.ArgumentParser(
        description="Ontology Mapper CLI: Map and improve ontologies using BioPortal and OLS.",
        add_help=False,  # Let downstream parser handle help
    )
    # Only parse known args for logging, forward the rest
    parser.add_argument("--log-level", default="INFO", help="Set logging level (default: INFO)")
    parser.add_argument("--console", action="store_true", help="Enable console logging")
    parser.add_argument("--version", action="version", version="ontology-mapper 1.0.0")

    # Parse only known args, leave the rest for the real CLI
    args, unknown = parser.parse_known_args()

    # Setup logging
    setup_logging(level=args.log_level, console=args.console)

    # Forward all arguments (except logging) to cli_main
    sys.argv = [sys.argv[0]] + unknown
    cli_main()


if __name__ == "__main__":
    main()
