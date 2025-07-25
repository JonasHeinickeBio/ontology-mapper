"""
Unit tests for cli.interface module.
"""

import argparse
import logging
import unittest
from unittest.mock import Mock, patch

import pytest

from cli.interface import CLIInterface


@pytest.mark.unit
class TestCLIInterface(unittest.TestCase):
    """Test cases for CLIInterface class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = logging.getLogger(__name__)
        self.interface = CLIInterface()

    def test_init(self):
        """Test CLIInterface initialization."""
        self.assertIsNotNone(self.interface.parser)
        self.assertIsInstance(self.interface.parser, argparse.ArgumentParser)

    def test_create_parser(self):
        """Test that argument parser is created correctly."""
        parser = self.interface._create_parser()

        self.assertIsInstance(parser, argparse.ArgumentParser)
        self.assertEqual(parser.description, "BioPortal Ontology Alignment CLI Tool")

    def test_list_available_ontologies(self):
        """Test _list_available_ontologies method."""
        with patch("cli.interface.logger") as mock_logger:
            self.interface._list_available_ontologies()

            # Should log available ontologies
            mock_logger.info.assert_called()
            call_args = [call.args[0] for call in mock_logger.info.call_args_list]
            self.assertTrue(any("Available Ontologies" in str(arg) for arg in call_args))

    def test_parser_single_word_argument(self):
        """Test that parser handles single-word argument correctly."""
        args = self.interface.parser.parse_args(["--single-word", "covid"])

        self.assertEqual(args.single_word, "covid")
        self.assertIsNone(args.ttl_file)  # Should be None when using single-word

    def test_parser_ttl_file_argument(self):
        """Test that parser handles TTL file argument correctly."""
        args = self.interface.parser.parse_args(["test.ttl"])

        self.assertEqual(args.ttl_file, "test.ttl")
        self.assertIsNone(args.single_word)  # Should be None when not specified

    def test_parser_output_argument(self):
        """Test that parser handles output argument correctly."""
        args = self.interface.parser.parse_args(["--output", "custom.ttl", "test.ttl"])

        self.assertEqual(args.output, "custom.ttl")
        self.assertEqual(args.ttl_file, "test.ttl")

    def test_parser_default_output(self):
        """Test that parser has correct default output."""
        args = self.interface.parser.parse_args(["test.ttl"])

        self.assertEqual(args.output, "improved_ontology.ttl")

    def test_parser_api_key_argument(self):
        """Test that parser handles API key argument correctly."""
        args = self.interface.parser.parse_args(["--api-key", "test_key", "test.ttl"])

        self.assertEqual(args.api_key, "test_key")

    def test_parser_ontologies_argument(self):
        """Test that parser handles ontologies argument correctly."""
        args = self.interface.parser.parse_args(["--ontologies", "HP,NCIT", "test.ttl"])

        self.assertEqual(args.ontologies, "HP,NCIT")

    def test_parser_batch_mode_argument(self):
        """Test that parser handles batch mode argument correctly."""
        args = self.interface.parser.parse_args(["--batch-mode", "selections.json", "test.ttl"])

        self.assertEqual(args.batch_mode, "selections.json")

    def test_parser_terminal_only_argument(self):
        """Test that parser handles terminal-only argument correctly."""
        args = self.interface.parser.parse_args(["--terminal-only", "test.ttl"])

        self.assertTrue(args.terminal_only)

    def test_parser_report_argument(self):
        """Test that parser handles report argument correctly."""
        args = self.interface.parser.parse_args(["--report", "test.ttl"])

        self.assertTrue(args.report)

    @patch("sys.argv", ["prog", "--single-word", "covid"])
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    def test_single_word_mode_called(self, mock_generator, mock_lookup):
        """Test that single word mode is called correctly."""
        mock_lookup_instance = Mock()
        mock_generator_instance = Mock()
        mock_lookup.return_value = mock_lookup_instance
        mock_generator.return_value = mock_generator_instance

        with patch.object(self.interface, "_single_word_mode") as mock_single_word:
            with patch("sys.exit"):
                self.interface.run()

            mock_single_word.assert_called_once()

    @patch("sys.argv", ["prog", "test.ttl"])
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyParser")
    @patch("cli.interface.OntologyGenerator")
    def test_ttl_processing_mode(self, mock_generator, mock_parser, mock_lookup):
        """Test that TTL processing mode works correctly."""
        mock_ontology = Mock()
        mock_ontology.parse.return_value = True
        mock_ontology.get_priority_concepts.return_value = [
            {"key": "covid", "label": "COVID-19", "type": "Disease", "category": "instance"}
        ]
        mock_parser.return_value = mock_ontology

        mock_lookup_instance = Mock()
        mock_lookup.return_value = mock_lookup_instance

        with patch.object(self.interface, "_interactive_selection") as mock_selection:
            mock_selection.return_value = {
                "covid": [{"uri": "test", "label": "test", "ontology": "TEST"}]
            }

            with patch("sys.exit"):
                self.interface.run()

            mock_ontology.parse.assert_called_once()
            mock_ontology.get_priority_concepts.assert_called_once()
            mock_selection.assert_called_once()

    @patch("sys.argv", ["prog", "nonexistent.ttl"])
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyParser")
    @patch("cli.interface.OntologyGenerator")
    def test_ttl_parse_failure(self, mock_generator, mock_parser, mock_lookup):
        """Test behavior when TTL parsing fails."""
        mock_ontology = Mock()
        mock_ontology.parse.return_value = False
        mock_ontology.get_priority_concepts.return_value = []
        mock_parser.return_value = mock_ontology

        with patch("sys.exit") as mock_exit:
            self.interface.run()
            mock_exit.assert_called_with(1)

    @patch("sys.argv", ["prog", "test.ttl"])
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyParser")
    @patch("cli.interface.OntologyGenerator")
    def test_no_priority_concepts(self, mock_generator, mock_parser, mock_lookup):
        """Test behavior when no priority concepts are found."""
        mock_ontology = Mock()
        mock_ontology.parse.return_value = True
        mock_ontology.get_priority_concepts.return_value = []
        mock_parser.return_value = mock_ontology

        with patch("sys.exit") as mock_exit:
            with patch("cli.interface.logger") as mock_logger:
                self.interface.run()

            mock_exit.assert_called_with(1)
            mock_logger.error.assert_called()

    def test_load_batch_selections_valid_file(self):
        """Test loading batch selections from valid file."""
        import json
        import tempfile

        test_selections = {
            "covid": [{"uri": "http://example.org/covid", "label": "COVID-19", "ontology": "TEST"}]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_selections, f)
            temp_file = f.name

        try:
            result = self.interface._load_batch_selections(temp_file)
            self.assertEqual(result, test_selections)
        finally:
            import os

            os.unlink(temp_file)

    def test_load_batch_selections_invalid_file(self):
        """Test loading batch selections from invalid file."""
        result = self.interface._load_batch_selections("nonexistent.json")
        self.assertEqual(result, {})  # Should return empty dict on error

    def test_load_batch_selections_invalid_json(self):
        """Test loading batch selections from file with invalid JSON."""
        import json
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            temp_file = f.name

        try:
            result = self.interface._load_batch_selections(temp_file)
            self.assertEqual(result, {})  # Should return empty dict on error
        finally:
            import os

            os.unlink(temp_file)

    @patch("builtins.input")
    def test_interactive_selection_quit(self, mock_input):
        """Test interactive selection with quit command."""
        mock_input.return_value = "q"

        concepts = [
            {"key": "covid", "label": "COVID-19", "type": "Disease", "category": "instance"}
        ]

        mock_lookup = Mock()
        mock_lookup.lookup_concept.return_value = ([], {})  # Return tuple of empty list and dict

        result = self.interface._interactive_selection(concepts, mock_lookup)

        self.assertEqual(result, {})

    @patch("builtins.input")
    def test_interactive_selection_skip(self, mock_input):
        """Test interactive selection with skip command."""
        mock_input.side_effect = ["s", "q"]  # Skip first, then quit

        concepts = [
            {"key": "covid", "label": "COVID-19", "type": "Disease", "category": "instance"},
            {"key": "fatigue", "label": "Fatigue", "type": "Symptom", "category": "instance"},
        ]

        mock_lookup = Mock()
        mock_lookup.lookup_concept.return_value = ([], {})  # Return tuple of empty list and dict

        result = self.interface._interactive_selection(concepts, mock_lookup)

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
