#!/usr/bin/env python3
"""
Main entry point for the modular ontology mapping tool.
This replaces the original bioportal_cli.py with a modular architecture.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.main import main

if __name__ == '__main__':
    main()
