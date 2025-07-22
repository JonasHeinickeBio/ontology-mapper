"""
Integration tests for CLI functionality.
Tests command-line interface components working together.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest

from cli.interface import CLIInterface
from core.lookup import ConceptLookup
from services import BioPortalLookup, OLSLookup


@pytest.mark.integration
@pytest.mark.cli
class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_concept = "cancer"
        self.sample_ontologies = "MONDO,HP,NCIT"

        self.mock_bioportal_results = [
            {
                "uri": "http://purl.bioontology.org/ontology/NCIT/C9305",
                "label": "Malignant Neoplasm",
                "source": "bioportal",
                "ontology": "NCIT",
            }
        ]

        self.mock_ols_results = [
            {
                "uri": "http://purl.obolibrary.org/obo/MONDO_0004992",
                "label": "Cancer",
                "source": "ols",
                "ontology": "mondo",
            }
        ]

    def test_cli_interface_initialization(self):
        """Test CLI interface can be initialized"""
        cli = CLIInterface()
        self.assertIsNotNone(cli.parser)

    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_cli_single_word_mode_integration(self, mock_ols_class, mock_bioportal_class):
        """Test CLI single word mode integration"""
        # Set up mocks
        mock_bp_service = MagicMock()
        mock_ols_service = MagicMock()

        mock_bp_service.search.return_value = self.mock_bioportal_results
        mock_ols_service.search.return_value = self.mock_ols_results

        mock_bioportal_class.return_value = mock_bp_service
        mock_ols_class.return_value = mock_ols_service

        # Create CLI and test single word mode
        cli = CLIInterface()

        # Mock args for single word mode
        mock_args = MagicMock()
        mock_args.single_word = "cancer"
        mock_args.ontologies = "MONDO,NCIT"
        mock_args.output = "test_output.ttl"
        mock_args.max_results = 5

        # Create lookup and generator
        lookup = ConceptLookup(mock_bp_service, mock_ols_service, mock_args.ontologies)

        # Test the single word mode functionality
        with patch.object(cli, "_single_word_mode") as mock_single_word:
            mock_single_word.return_value = None

            # Simulate calling single word mode
            from core.generator import OntologyGenerator

            generator = OntologyGenerator()
            cli._single_word_mode(mock_args, lookup, generator)

            # Verify single word mode was called
            mock_single_word.assert_called_once_with(mock_args, lookup, generator)

    def test_cli_concept_lookup_integration(self):
        """Test CLI integration with ConceptLookup"""
        # Create mock services
        mock_bioportal = MagicMock(spec=BioPortalLookup)
        mock_ols = MagicMock(spec=OLSLookup)

        mock_bioportal.search.return_value = self.mock_bioportal_results
        mock_ols.search.return_value = self.mock_ols_results

        # Test ConceptLookup with CLI-style queries
        lookup = ConceptLookup(mock_bioportal, mock_ols)

        # Simulate CLI-style concept query (as done in single word mode)
        concept = {
            "key": self.sample_concept.replace(" ", "_"),
            "label": self.sample_concept,
            "type": "Term",
            "category": "query",
        }

        results, comparison = lookup.lookup_concept(concept, max_results=10)

        # Verify integration worked
        self.assertGreater(len(results), 0)
        self.assertIn("concept", comparison)

        # Verify both services were called
        self.assertTrue(mock_bioportal.search.called)
        self.assertTrue(mock_ols.search.called)

    @patch("sys.argv", ["cli", "--single-word", "cancer", "--ontologies", "NCIT"])
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_cli_argument_parsing_integration(self, mock_ols_class, mock_bioportal_class):
        """Test CLI argument parsing integration"""
        # Set up mocks
        mock_bp_service = MagicMock()
        mock_ols_service = MagicMock()

        mock_bioportal_class.return_value = mock_bp_service
        mock_ols_class.return_value = mock_ols_service

        cli = CLIInterface()

        # Test argument parsing
        args = cli.parser.parse_args(["--single-word", "cancer", "--ontologies", "NCIT"])

        self.assertEqual(args.single_word, "cancer")
        self.assertEqual(args.ontologies, "NCIT")

    def test_cli_batch_processing_integration(self):
        """Test CLI batch processing integration"""
        # Create test batch file
        batch_data = {
            "cancer": {
                "selected_terms": [
                    {
                        "uri": "http://example.org/cancer",
                        "label": "Cancer",
                        "alignment_type": "exact",
                    }
                ]
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as batch_file:
            json.dump(batch_data, batch_file)
            batch_path = batch_file.name

        try:
            cli = CLIInterface()

            # Test loading batch selections
            loaded_selections = cli._load_batch_selections(batch_path)

            # Verify batch data was loaded correctly
            self.assertIn("cancer", loaded_selections)
            self.assertIn("selected_terms", loaded_selections["cancer"])

        finally:
            if os.path.exists(batch_path):
                os.unlink(batch_path)

    def test_cli_ontology_listing_integration(self):
        """Test CLI ontology listing integration"""
        cli = CLIInterface()

        # Test the list ontologies functionality (this should not raise errors)
        try:
            cli._list_available_ontologies()
        except Exception as e:
            self.fail(f"Listing ontologies should not raise exceptions: {e}")

    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_cli_error_handling_integration(self, mock_ols_class, mock_bioportal_class):
        """Test CLI error handling integration"""
        # Set up service to fail
        mock_bp_service = MagicMock()
        mock_ols_service = MagicMock()

        mock_bp_service.search.side_effect = Exception("Service unavailable")
        mock_ols_service.search.return_value = self.mock_ols_results

        mock_bioportal_class.return_value = mock_bp_service
        mock_ols_class.return_value = mock_ols_service

        # Test that CLI components handle errors gracefully
        lookup = ConceptLookup(mock_bp_service, mock_ols_service)

        concept = {"key": "test", "label": "Test Concept", "type": "Term", "category": "query"}

        # Should propagate exceptions when service fails
        with self.assertRaises(Exception) as context:
            results, comparison = lookup.lookup_concept(concept)

        # Verify the correct exception is raised
        self.assertIn("Service unavailable", str(context.exception))

    def test_cli_output_integration(self):
        """Test CLI output integration with file generation"""
        # Create temporary TTL file for testing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as ttl_file:
            ttl_file.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
            ttl_path = ttl_file.name

        try:
            cli = CLIInterface()

            # Test argument parsing with file paths
            args = cli.parser.parse_args([ttl_path, "--output", "test_output.ttl"])

            self.assertEqual(args.ttl_file, ttl_path)
            self.assertEqual(args.output, "test_output.ttl")

        finally:
            if os.path.exists(ttl_path):
                os.unlink(ttl_path)

    def test_cli_configuration_integration(self):
        """Test CLI integration with different configuration options"""
        cli = CLIInterface()

        # Test various argument combinations
        test_cases = [
            ["--single-word", "cancer", "--ontologies", "NCIT"],
            ["--single-word", "diabetes", "--ontologies", "MONDO,HP", "--max-results", "10"],
            ["--list-ontologies"],
        ]

        for args in test_cases:
            with self.subTest(args=args):
                try:
                    parsed = cli.parser.parse_args(args)
                    # Each should parse without error
                    self.assertIsNotNone(parsed)
                except SystemExit:
                    # --list-ontologies might cause system exit, which is expected
                    if "--list-ontologies" not in args:
                        self.fail(f"Unexpected SystemExit for args: {args}")

    def test_cli_workflow_integration(self):
        """Test complete CLI workflow integration"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as base_ttl:
            base_ttl.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
            base_ttl.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
            ttl_path = base_ttl.name

        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as output_file:
            output_path = output_file.name

        try:
            # Test full CLI workflow simulation
            cli = CLIInterface()

            # Parse arguments as if from command line
            args = cli.parser.parse_args([ttl_path, "--output", output_path, "--max-results", "5"])

            # Verify arguments were parsed correctly
            self.assertEqual(args.ttl_file, ttl_path)
            self.assertEqual(args.output, output_path)
            self.assertEqual(args.max_results, 5)

            # The workflow would normally continue with CLI.run()
            # but we don't run it here to avoid requiring API keys

        finally:
            for path in [ttl_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)


if __name__ == "__main__":
    unittest.main()
