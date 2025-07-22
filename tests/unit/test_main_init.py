"""
Unit tests for __init__.py module.
"""

import unittest


class TestMainInit(unittest.TestCase):
    """Unit tests for main __init__.py module"""

    def test_version_and_metadata(self):
        """Test package metadata constants"""
        import __init__ as init_module

        self.assertEqual(init_module.__version__, "1.0.0")
        self.assertEqual(init_module.__author__, "Jonas Immanuel Heinicke")

    def test_all_exports(self):
        """Test __all__ contains expected exports"""
        import __init__ as init_module

        expected_exports = [
            "main",
            "OntologyParser",
            "ConceptLookup",
            "OntologyGenerator",
            "BioPortalLookup",
            "OLSLookup",
            "ResultComparator",
            "LoadingBar",
            "clean_description",
            "deduplicate_synonyms",
            "ONTOLOGY_CONFIGS",
            "ONTOLOGY_COMBINATIONS",
        ]

        self.assertEqual(set(init_module.__all__), set(expected_exports))

    def test_docstring_content(self):
        """Test module docstring contains expected content"""
        import __init__ as init_module

        docstring = init_module.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("Modular ontology mapping tool", docstring)
            self.assertIn("BioPortal and OLS integration", docstring)

    def test_module_imports_successfully(self):
        """Test module can be imported without errors"""
        try:
            import __init__  # noqa: F401

            success = True
        except ImportError:
            success = False
        self.assertTrue(success)

    def test_path_handling(self):
        """Test that sys.path is modified correctly"""
        import sys
        from pathlib import Path

        import __init__ as init_module

        # The current directory should be in sys.path
        current_dir = str(Path(init_module.__file__).parent)
        self.assertIn(current_dir, sys.path)

    def test_import_fallback_handling(self):
        """Test that import fallbacks work"""
        import __init__ as init_module

        # If imports failed, some attributes may be None
        # But the module should still have __all__ defined
        self.assertTrue(hasattr(init_module, "__all__"))
        self.assertTrue(hasattr(init_module, "__version__"))
        self.assertTrue(hasattr(init_module, "__author__"))

    def test_required_constants(self):
        """Test required constants are defined"""
        import __init__ as init_module

        self.assertTrue(hasattr(init_module, "__version__"))
        self.assertTrue(hasattr(init_module, "__author__"))
        self.assertTrue(hasattr(init_module, "__all__"))

    def test_module_structure(self):
        """Test __init__.py has expected structure"""
        with open("__init__.py") as f:
            content = f.read()

        # Should have required elements
        self.assertIn('__version__ = "1.0.0"', content)
        self.assertIn('__author__ = "Jonas Immanuel Heinicke"', content)
        self.assertIn("__all__ = [", content)
        self.assertIn("sys.path.insert", content)


if __name__ == "__main__":
    unittest.main()
