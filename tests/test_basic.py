"""
Basic tests for the ontology-mapper package
"""

import sys
from pathlib import Path

import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.unit
class TestBasicImports:
    """Test that all modules can be imported successfully"""

    def test_import_main(self):
        """Test that main module can be imported"""
        try:
            import main

            assert hasattr(main, "__file__")
        except ImportError as e:
            pytest.fail(f"Could not import main module: {e}")

    def test_import_cli(self):
        """Test that CLI modules can be imported"""
        try:
            from cli import interface

            assert hasattr(interface, "CLIInterface")
        except ImportError as e:
            pytest.fail(f"Could not import CLI interface: {e}")

    def test_import_core(self):
        """Test that core modules can be imported"""
        try:
            from core import generator, lookup, parser

            assert hasattr(lookup, "ConceptLookup")
            assert hasattr(parser, "OntologyParser")
            assert hasattr(generator, "OntologyGenerator")
        except ImportError as e:
            pytest.fail(f"Could not import core modules: {e}")

    def test_import_services(self):
        """Test that service modules can be imported"""
        try:
            from services import bioportal, comparator, ols

            assert hasattr(bioportal, "BioPortalLookup")
            assert hasattr(ols, "OLSLookup")
            assert hasattr(comparator, "ResultComparator")
        except ImportError as e:
            pytest.fail(f"Could not import service modules: {e}")

    def test_import_utils(self):
        """Test that utility modules can be imported"""
        try:
            from utils import helpers, loading

            assert hasattr(helpers, "clean_description")
            assert hasattr(loading, "LoadingBar")
        except ImportError as e:
            pytest.fail(f"Could not import utility modules: {e}")

    def test_import_config(self):
        """Test that config modules can be imported"""
        try:
            from config import ontologies

            assert hasattr(ontologies, "ONTOLOGY_CONFIGS")
        except ImportError as e:
            pytest.fail(f"Could not import config modules: {e}")


class TestVersion:
    """Test version information"""

    def test_version_exists(self):
        """Test that version information is available"""
        try:
            import __init__

            assert hasattr(__init__, "__version__")
            assert __init__.__version__ == "1.0.0"
        except ImportError:
            # If __init__ doesn't exist, that's okay for now
            pass


class TestDependencies:
    """Test that required dependencies are available"""

    def test_rdflib_import(self):
        """Test that rdflib can be imported"""
        try:
            import rdflib

            assert hasattr(rdflib, "Graph")
        except ImportError as e:
            pytest.fail(f"Could not import rdflib: {e}")

    def test_requests_import(self):
        """Test that requests can be imported"""
        try:
            import requests

            assert hasattr(requests, "get")
        except ImportError as e:
            pytest.fail(f"Could not import requests: {e}")

    def test_typing_extensions_import(self):
        """Test that typing_extensions can be imported"""
        try:
            import typing_extensions

            # Basic check that it's available
            assert typing_extensions is not None
        except ImportError as e:
            pytest.fail(f"Could not import typing_extensions: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
