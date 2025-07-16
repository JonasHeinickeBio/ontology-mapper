#!/usr/bin/env python3
"""
BioPortal GUI Launcher

Simple launcher script that ensures proper setup and launches the GUI.
"""

import os
import subprocess  # nosec B404
import sys


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing requirements...")
        try:
            subprocess.check_call(  # nosec B603
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            )
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False


def check_cli_module():
    """Check if CLI module is available"""
    cli_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "ontology_mapping", "bioportal_cli.py"
    )
    if os.path.exists(cli_path):
        print(f"✅ Found CLI module: {cli_path}")
        return True
    else:
        print(f"❌ CLI module not found: {cli_path}")
        print("Please ensure bioportal_cli.py is in the parent ontology_mapping folder")
        return False


def main():
    """Main launcher"""
    print("🚀 BioPortal GUI Launcher")
    print("=" * 30)

    # Check dependencies
    if not check_dependencies():
        print("❌ Cannot proceed without required dependencies")
        sys.exit(1)

    # Check CLI module
    if not check_cli_module():
        print("❌ Cannot proceed without CLI module")
        sys.exit(1)

    # Launch GUI
    print("🖥️ Launching BioPortal GUI...")
    try:
        from gui.bioportal_gui import main as gui_main

        gui_main()
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
