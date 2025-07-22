#!/usr/bin/env python3
"""
BioPortal GUI Launcher

Simple launcher script that ensures proper setup and launches the GUI.
"""

import os
import subprocess  # nosec B404
import sys

from config.logging_config import get_logger, setup_logging

# Setup logging for the GUI launcher
setup_logging(level="INFO", console=True)
logger = get_logger(__name__)


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Installing requirements...")
        try:
            subprocess.check_call(  # nosec B603
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            )
            return True
        except subprocess.CalledProcessError:
            logger.error("Failed to install dependencies")
            return False


def check_cli_module():
    """Check if CLI module is available"""
    cli_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "ontology_mapping", "bioportal_cli.py"
    )
    if os.path.exists(cli_path):
        logger.info(f"Found CLI module: {cli_path}")
        return True
    else:
        logger.error(f"CLI module not found: {cli_path}")
        logger.error("Please ensure bioportal_cli.py is in the parent ontology_mapping folder")
        return False


def main():
    """Main launcher"""
    logger.info("BioPortal GUI Launcher")
    logger.info("=" * 30)

    # Check dependencies
    if not check_dependencies():
        logger.error("Cannot proceed without required dependencies")
        sys.exit(1)

    # Check CLI module
    if not check_cli_module():
        logger.error("Cannot proceed without CLI module")
        sys.exit(1)

    # Launch GUI
    logger.info("Launching BioPortal GUI...")
    try:
        from gui.bioportal_gui import main as gui_main

        gui_main()
    except Exception as e:
        logger.error(f"Error launching GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
