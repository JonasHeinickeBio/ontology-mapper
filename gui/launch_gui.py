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
    """Check if CLI module is available in any likely location"""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidates = [
        os.path.join(base_dir, "ontology_mapping", "bioportal_cli.py"),
        os.path.join(base_dir, "cli", "bioportal_cli.py"),
        os.path.join(base_dir, "bioportal_cli.py"),
        os.path.join(base_dir, "..", "ontology_mapping", "bioportal_cli.py"),
        os.path.join(base_dir, "..", "cli", "bioportal_cli.py"),
    ]
    found = False
    for path in candidates:
        if os.path.exists(path):
            logger.info(f"Found CLI module: {path}")
            found = True
            break
        else:
            logger.debug(f"Checked: {path} (not found)")
    if not found:
        logger.error("CLI module bioportal_cli.py not found in any expected location.")
        logger.error(
            "Please ensure bioportal_cli.py is present in ontology_mapping/ or cli/ or project root."
        )
    return found


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
