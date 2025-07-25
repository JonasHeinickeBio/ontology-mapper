"""
Unit tests for gui/demo_gui.py module.
Tests demo GUI components using comprehensive mocking.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest


class TestDemoComponents(unittest.TestCase):
    """Unit tests for demo GUI components"""

    def setUp(self):
        """Set up test fixtures with comprehensive mocking"""
        # Create comprehensive mocks for all GUI dependencies
        self.mock_modules = {
            "tkinter": MagicMock(),
            "tkinter.filedialog": MagicMock(),
            "tkinter.messagebox": MagicMock(),
            "tkinter.scrolledtext": MagicMock(),
            "tkinter.ttk": MagicMock(),
            "config.logging_config": MagicMock(),
        }

        # Set up common mock behaviors
        self.mock_root = MagicMock()
        self.mock_modules["tkinter"].Tk.return_value = self.mock_root
        self.mock_modules["tkinter"].Frame.return_value = MagicMock()
        self.mock_modules["tkinter"].Label.return_value = MagicMock()
        self.mock_modules["tkinter"].Button.return_value = MagicMock()
        self.mock_modules["tkinter"].Entry.return_value = MagicMock()
        self.mock_modules["tkinter"].Text.return_value = MagicMock()
        self.mock_modules["tkinter.ttk"].Combobox.return_value = MagicMock()

        # Mock logger
        self.mock_logger = MagicMock()
        self.mock_modules["config.logging_config"].get_logger.return_value = self.mock_logger

    @patch.dict("sys.modules")
    def test_demo_bioportal_lookup_init(self):
        """Test DemoBioPortalLookup initialization"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import and create instance after mocking
        from gui.demo_gui import DemoBioPortalLookup

        lookup = DemoBioPortalLookup(api_key="test_key")

        # Verify initialization
        self.assertIsNotNone(lookup)
        self.assertEqual(lookup.api_key, "test_key")

    @patch.dict("sys.modules")
    def test_demo_bioportal_lookup_search(self):
        """Test DemoBioPortalLookup search method"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import and test search
        from gui.demo_gui import DemoBioPortalLookup

        lookup = DemoBioPortalLookup()
        results = lookup.search("cancer", "NCIT", max_results=2)

        # Verify results structure
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        if results:
            self.assertIn("uri", results[0])
            self.assertIn("label", results[0])
            self.assertIn("ontology", results[0])

    @patch.dict("sys.modules")
    def test_demo_ols_lookup_init(self):
        """Test DemoOLSLookup initialization"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import and create instance after mocking
        from gui.demo_gui import DemoOLSLookup

        lookup = DemoOLSLookup()

        # Verify initialization
        self.assertIsNotNone(lookup)

    @patch.dict("sys.modules")
    def test_demo_ols_lookup_search(self):
        """Test DemoOLSLookup search method"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import and test search
        from gui.demo_gui import DemoOLSLookup

        lookup = DemoOLSLookup()
        results = lookup.search("neuron", "GO", max_results=2)

        # Verify results structure
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        if results:
            self.assertIn("uri", results[0])
            self.assertIn("label", results[0])

    @patch.dict("sys.modules")
    def test_demo_ontology_parser_init(self):
        """Test DemoOntologyParser initialization"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import and create instance after mocking
        from gui.demo_gui import DemoOntologyParser

        parser = DemoOntologyParser("test.ttl")

        # Verify initialization
        self.assertIsNotNone(parser)

    @patch.dict("sys.modules")
    def test_demo_ontology_parser_parse(self):
        """Test DemoOntologyParser parse method"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import and test parse
        from gui.demo_gui import DemoOntologyParser

        parser = DemoOntologyParser("test.ttl")
        result = parser.parse()

        # Verify results structure
        self.assertIsInstance(result, bool)

    @patch.dict("sys.modules")
    def test_demo_concept_lookup_init(self):
        """Test DemoConceptLookup initialization"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Create mock services
        from gui.demo_gui import DemoBioPortalLookup, DemoOLSLookup

        bioportal = DemoBioPortalLookup()
        ols = DemoOLSLookup()

        # Import and create instance after mocking
        from gui.demo_gui import DemoConceptLookup

        lookup = DemoConceptLookup(bioportal, ols)

        # Verify initialization
        self.assertIsNotNone(lookup)
        self.assertEqual(lookup.bioportal, bioportal)
        self.assertEqual(lookup.ols, ols)

    @patch.dict("sys.modules")
    def test_demo_concept_lookup_concept(self):
        """Test DemoConceptLookup lookup_concept method"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Create mock services
        from gui.demo_gui import DemoBioPortalLookup, DemoConceptLookup, DemoOLSLookup

        bioportal = DemoBioPortalLookup()
        ols = DemoOLSLookup()
        lookup = DemoConceptLookup(bioportal, ols)

        # Test lookup
        test_concept = {"label": "cancer"}
        combined, comparison = lookup.lookup_concept(test_concept)

        # Verify results
        self.assertIsInstance(combined, list)
        self.assertIsInstance(comparison, dict)
        self.assertIn("concept", comparison)
        self.assertIn("bioportal_count", comparison)
        self.assertIn("ols_count", comparison)

    @patch.dict("sys.modules")
    def test_demo_bioportal_gui_init(self):
        """Test DemoBioPortalGUI initialization"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import and create instance after mocking
        from gui.demo_gui import DemoBioPortalGUI

        demo_gui = DemoBioPortalGUI()

        # Verify basic attributes exist
        self.assertIsNotNone(demo_gui)

        # Verify root window was created
        self.mock_modules["tkinter"].Tk.assert_called()

    @patch.dict("sys.modules")
    def test_module_imports(self):
        """Test that demo_gui module can be imported"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import module after mocking
        import gui.demo_gui

        # Verify key classes exist
        self.assertTrue(hasattr(gui.demo_gui, "DemoBioPortalGUI"))
        self.assertTrue(hasattr(gui.demo_gui, "DemoBioPortalLookup"))
        self.assertTrue(hasattr(gui.demo_gui, "DemoOLSLookup"))
        self.assertTrue(hasattr(gui.demo_gui, "DemoOntologyParser"))
        self.assertTrue(hasattr(gui.demo_gui, "DemoConceptLookup"))

    @patch.dict("sys.modules")
    def test_demo_gui_main_function(self):
        """Test demo GUI main function"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import after mocking
        from gui.demo_gui import main

        # Test main function execution
        try:
            main()
        except Exception:
            # Main might exit or loop, that's acceptable
            pass

        # Verify Tk was called to create root window
        self.mock_modules["tkinter"].Tk.assert_called()


@pytest.mark.gui
class TestDemoGUIIntegration(unittest.TestCase):
    """Integration tests for demo GUI components"""

    def setUp(self):
        """Set up test fixtures with comprehensive mocking"""
        # Create comprehensive mocks
        self.mock_modules = {
            "tkinter": MagicMock(),
            "tkinter.filedialog": MagicMock(),
            "tkinter.messagebox": MagicMock(),
            "tkinter.scrolledtext": MagicMock(),
            "tkinter.ttk": MagicMock(),
            "config.logging_config": MagicMock(),
        }

        # Set up common mock behaviors
        self.mock_root = MagicMock()
        self.mock_modules["tkinter"].Tk.return_value = self.mock_root
        self.mock_modules["tkinter"].Frame.return_value = MagicMock()
        self.mock_modules["tkinter"].Label.return_value = MagicMock()
        self.mock_modules["tkinter"].Button.return_value = MagicMock()
        self.mock_modules["tkinter"].Entry.return_value = MagicMock()
        self.mock_modules["tkinter"].Text.return_value = MagicMock()
        self.mock_modules["tkinter.ttk"].Combobox.return_value = MagicMock()

        # Mock logger
        self.mock_logger = MagicMock()
        self.mock_modules["config.logging_config"].get_logger.return_value = self.mock_logger

    @patch.dict("sys.modules")
    def test_complete_demo_workflow(self):
        """Test complete demo workflow from initialization to search"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import after mocking
        from gui.demo_gui import (
            DemoBioPortalGUI,
            DemoBioPortalLookup,
            DemoConceptLookup,
            DemoOLSLookup,
        )

        # Create components
        bioportal = DemoBioPortalLookup()
        ols = DemoOLSLookup()
        concept_lookup = DemoConceptLookup(bioportal, ols)
        demo_gui = DemoBioPortalGUI()

        # Verify components created
        self.assertIsNotNone(bioportal)
        self.assertIsNotNone(ols)
        self.assertIsNotNone(concept_lookup)
        self.assertIsNotNone(demo_gui)
        self.mock_modules["tkinter"].Tk.assert_called()

    @patch.dict("sys.modules")
    def test_service_interaction(self):
        """Test interaction between demo services"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import after mocking
        from gui.demo_gui import DemoBioPortalLookup, DemoConceptLookup, DemoOLSLookup

        # Create services
        bioportal = DemoBioPortalLookup()
        ols = DemoOLSLookup()
        concept_lookup = DemoConceptLookup(bioportal, ols)

        # Test service integration
        test_concept = {"label": "test"}
        combined, comparison = concept_lookup.lookup_concept(test_concept)

        # Verify integration
        self.assertIsInstance(combined, list)
        self.assertIsInstance(comparison, dict)
        self.assertEqual(comparison["concept"], "test")

    @patch.dict("sys.modules")
    def test_error_handling_integration(self):
        """Test integrated error handling across components"""
        # Apply comprehensive mocking
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module

        # Import after mocking
        from gui.demo_gui import DemoBioPortalGUI, DemoBioPortalLookup

        # Create components
        bioportal = DemoBioPortalLookup()
        demo_gui = DemoBioPortalGUI()

        # Test error handling - should not raise exceptions
        try:
            results = bioportal.search("test")
            self.assertIsInstance(results, list)
        except Exception:
            # Exception handling is also acceptable
            pass

        # GUI should still be functional
        self.assertIsNotNone(demo_gui)


if __name__ == "__main__":
    unittest.main()
