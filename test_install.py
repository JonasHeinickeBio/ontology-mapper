#!/usr/bin/env python3
"""
Test script to verify the ontology mapping tool works
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from cli.interface import CLIInterface
        print("✓ CLI interface imported successfully")
    except Exception as e:
        print(f"✗ Failed to import CLI interface: {e}")
        return False
    
    try:
        from services.bioportal import BioPortalLookup
        print("✓ BioPortal service imported successfully")
    except Exception as e:
        print(f"✗ Failed to import BioPortal service: {e}")
        return False
    
    try:
        from services.ols import OLSLookup
        print("✓ OLS service imported successfully")
    except Exception as e:
        print(f"✗ Failed to import OLS service: {e}")
        return False
    
    try:
        from core.lookup import ConceptLookup
        print("✓ Concept lookup imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Concept lookup: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality without API calls"""
    try:
        from config.ontologies import ONTOLOGY_CONFIGS
        print(f"✓ Ontology configs loaded: {len(ONTOLOGY_CONFIGS)} ontologies")
    except Exception as e:
        print(f"✗ Failed to load ontology configs: {e}")
        return False
    
    return True

def main():
    print("Testing Ontology Mapping Tool...")
    print("=" * 40)
    
    if not test_imports():
        print("\n❌ Import tests failed")
        return False
    
    if not test_basic_functionality():
        print("\n❌ Basic functionality tests failed")
        return False
    
    print("\n✅ All tests passed!")
    print("\nTo run the tool:")
    print("  CLI: python main.py")
    print("  GUI: python gui/launch_gui.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
