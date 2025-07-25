"""
Simple unit tests for main.py and cli/main.py modules.
"""

import unittest
from unittest.mock import Mock, patch

import cli


class TestMainSimple(unittest.TestCase):
    """Simple unit tests for main entry points"""

    def test_main_py_file_structure(self):
        """Test main.py file has expected structure"""
        with open("main.py") as f:
            content = f.read()

        # Should have required elements
        self.assertIn("#!/usr/bin/env python3", content)
        self.assertIn("from cli.main import main", content)
        self.assertIn("from config.logging_config import setup_logging", content)
        self.assertIn('if __name__ == "__main__":', content)

    def test_main_py_docstring(self):
        """Test main.py has docstring"""
        import main as main_module

        docstring = main_module.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("Main entry point", docstring)

    @patch("cli.main.CLIInterface")
    @patch("cli.main.get_logger")
    def test_cli_main_basic_execution(self, mock_get_logger, mock_cli_interface):
        """Test CLI main function basic execution"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_cli = Mock()
        mock_cli_interface.return_value = mock_cli

        cli.main()

        # Should create CLI interface and run it
        mock_cli_interface.assert_called_once()
        mock_cli.run.assert_called_once()

    def test_cli_main_module_docstring(self):
        """Test cli.main module has docstring"""
        import cli.main as cli_main_module

        docstring = cli_main_module.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("Main", docstring)
            self.assertIn("entry point", docstring)

    def test_configure_logging_file_structure(self):
        """Test configure_logging.py file has expected structure"""
        with open("configure_logging.py") as f:
            content = f.read()

        # Should have required elements
        self.assertIn("#!/usr/bin/env python3", content)
        self.assertIn("from config.logging_config import setup_logging", content)
        self.assertIn("def main():", content)

    def test_configure_logging_docstring(self):
        """Test configure_logging module has docstring"""
        import configure_logging as config_module

        docstring = config_module.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("Configure logging", docstring)

    def test_init_version_metadata(self):
        """Test __init__.py version and metadata"""
        import __init__ as init_module

        self.assertEqual(init_module.__version__, "1.0.0")
        self.assertEqual(init_module.__author__, "Jonas Immanuel Heinicke")

    def test_init_all_exports(self):
        """Test __init__.py __all__ exports"""
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


if __name__ == "__main__":
    unittest.main()
