"""
End-to-end CLI workflow tests.
Tests complete command-line interface workflows from argument parsing to output generation.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli.interface import CLIInterface


@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.cli
class TestCLIE2EWorkflows(unittest.TestCase):
    """End-to-end CLI workflow tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)

        # Create sample TTL file for testing
        self.sample_ttl_content = """@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

<http://example.org/ontology> a owl:Ontology .

<http://example.org/cancer> a owl:Class ;
    rdfs:label "Cancer" ;
    rdfs:comment "A malignant neoplasm" .

<http://example.org/diabetes> a owl:Class ;
    rdfs:label "Diabetes" ;
    rdfs:comment "A metabolic disorder" .

<http://example.org/hypertension> a owl:Class ;
    rdfs:label "Hypertension" ;
    rdfs:comment "High blood pressure" .
"""

        self.sample_ttl_file = self.temp_dir_path / "sample_ontology.ttl"
        self.sample_ttl_file.write_text(self.sample_ttl_content)

        # Create sample batch selection file
        self.sample_batch_selections = {
            "cancer": [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0004992",
                    "label": "Cancer",
                    "ontology": "MONDO",
                    "description": "A disease characterized by...",
                    "synonyms": ["malignancy", "neoplasm"],
                    "source": "ols",
                    "relationship": "skos:exactMatch",
                }
            ],
            "diabetes": [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0005015",
                    "label": "Diabetes mellitus",
                    "ontology": "MONDO",
                    "description": "A metabolic disorder...",
                    "synonyms": ["diabetes"],
                    "source": "ols",
                    "relationship": "skos:exactMatch",
                }
            ],
        }

        self.batch_file = self.temp_dir_path / "batch_selections.json"
        self.batch_file.write_text(json.dumps(self.sample_batch_selections, indent=2))

        # Output files
        self.output_ttl = self.temp_dir_path / "output.ttl"
        self.report_file = self.temp_dir_path / "report.json"

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_invalid_arguments_workflow(self):
        """Test workflow with invalid command line arguments"""
        cli = CLIInterface()

        # Test missing required arguments - use sys.argv directly
        with patch("sys.argv", ["cli"]):  # No ttl_file or --single-word
            with patch("sys.exit") as mock_exit:
                with patch("cli.interface.logger") as mock_logger:
                    with patch.object(cli.parser, "print_help") as mock_help:  # noqa: F841
                        cli.run()

                        # Check that any validation error was logged
                        error_calls = mock_logger.error.call_args_list
                        error_messages = [call[0][0] for call in error_calls]

                        # Check for either validation error
                        self.assertTrue(
                            any(
                                "Either provide a TTL file or use --single-word option" in msg
                                for msg in error_messages
                            )
                            or any("No selections made. Exiting." in msg for msg in error_messages),
                            f"Expected validation error, got: {error_messages}",
                        )
                        mock_exit.assert_called_with(1)

    @patch("os.path.exists")
    def test_nonexistent_file_workflow(self, mock_exists):
        """Test workflow with non-existent TTL file"""
        mock_exists.return_value = False

        cli = CLIInterface()

        # Use sys.argv to simulate command line args
        with patch("sys.argv", ["cli", "nonexistent.ttl"]):
            with patch("sys.exit") as mock_exit:
                with patch("cli.interface.logger") as mock_logger:
                    cli.run()

                    # Check that any file-related error was logged
                    error_calls = mock_logger.error.call_args_list
                    error_messages = [call[0][0] for call in error_calls]

                    # Check for either file not found error or parser error
                    self.assertTrue(
                        any("File nonexistent.ttl not found" in msg for msg in error_messages)
                        or any("No selections made. Exiting." in msg for msg in error_messages),
                        f"Expected file error, got: {error_messages}",
                    )
                    mock_exit.assert_called_with(1)

    @patch("sys.argv")
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.OntologyParser")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_single_word_query_workflow(
        self, mock_ols, mock_bioportal, mock_parser, mock_generator, mock_lookup, mock_argv
    ):
        """Test complete single word query workflow"""
        # Setup mocks
        mock_argv.__getitem__ = lambda self, index: [
            "cli",
            "--single-word",
            "cancer",
            "--ontologies",
            "MONDO,HP",
            "--output",
            str(self.output_ttl),
            "--terminal-only",
        ][index]
        mock_argv.__len__ = lambda self: 6

        mock_bioportal_instance = MagicMock()
        mock_ols_instance = MagicMock()
        mock_lookup_instance = MagicMock()
        mock_generator_instance = MagicMock()

        mock_bioportal.return_value = mock_bioportal_instance
        mock_ols.return_value = mock_ols_instance
        mock_lookup.return_value = mock_lookup_instance
        mock_generator.return_value = mock_generator_instance

        # Mock lookup results
        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0004992",
                    "label": "Cancer",
                    "source": "ols",
                    "ontology": "MONDO",
                    "description": "A disease of cellular proliferation",
                    "synonyms": ["malignancy", "neoplasm"],
                },
                {
                    "uri": "http://purl.bioontology.org/ontology/NCIT/C9305",
                    "label": "Malignant Neoplasm",
                    "source": "bioportal",
                    "ontology": "NCIT",
                    "description": "A malignant tumor",
                    "synonyms": ["cancer"],
                },
            ],
            {"discrepancies": [], "bioportal_count": 1, "ols_count": 1},
        )

        # Mock user input for selection
        with patch("builtins.input", return_value="1,2"):
            cli = CLIInterface()

            # Override parser to use our test args
            test_args = cli.parser.parse_args(
                [
                    "--single-word",
                    "cancer",
                    "--ontologies",
                    "MONDO,HP",
                    "--output",
                    str(self.output_ttl),
                    "--terminal-only",
                ]
            )

            with patch.object(cli.parser, "parse_args", return_value=test_args):
                # Run the CLI
                cli.run()

        # Verify interactions
        mock_lookup.assert_called_once()
        mock_lookup_instance.lookup_concept.assert_called_once()

        # Verify the concept passed to lookup
        concept_arg = mock_lookup_instance.lookup_concept.call_args[0][0]
        self.assertEqual(concept_arg["label"], "cancer")
        self.assertEqual(concept_arg["key"], "cancer")

    @patch("sys.argv")
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.OntologyParser")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    @patch("os.path.exists")
    def test_ttl_file_batch_mode_workflow(
        self,
        mock_exists,
        mock_ols,
        mock_bioportal,
        mock_parser,
        mock_generator,
        mock_lookup,
        mock_argv,
    ):
        """Test complete TTL file processing with batch mode workflow"""
        # Setup mocks
        mock_exists.return_value = True
        mock_argv.__getitem__ = lambda self, index: [
            "cli",
            str(self.sample_ttl_file),
            "--batch-mode",
            str(self.batch_file),
            "--output",
            str(self.output_ttl),
            "--report",
            str(self.report_file),
        ][index]
        mock_argv.__len__ = lambda self: 7

        mock_bioportal_instance = MagicMock()
        mock_ols_instance = MagicMock()
        mock_lookup_instance = MagicMock()
        mock_generator_instance = MagicMock()
        mock_parser_instance = MagicMock()

        mock_bioportal.return_value = mock_bioportal_instance
        mock_ols.return_value = mock_ols_instance
        mock_lookup.return_value = mock_lookup_instance
        mock_generator.return_value = mock_generator_instance
        mock_parser.return_value = mock_parser_instance

        # Mock parser methods
        mock_parser_instance.parse.return_value = True
        mock_parser_instance.get_priority_concepts.return_value = [
            {"key": "cancer", "label": "Cancer", "type": "class", "category": "test"}
        ]

        cli = CLIInterface()

        # Override parser to use our test args
        test_args = cli.parser.parse_args(
            [
                str(self.sample_ttl_file),
                "--batch-mode",
                str(self.batch_file),
                "--output",
                str(self.output_ttl),
                "--report",
                str(self.report_file),
            ]
        )

        with patch.object(cli.parser, "parse_args", return_value=test_args):
            # Run the CLI
            cli.run()

        # Verify interactions
        mock_parser.assert_called_once_with(str(self.sample_ttl_file))
        mock_parser_instance.parse.assert_called_once()
        mock_parser_instance.get_priority_concepts.assert_called_once()
        mock_generator_instance.generate_improved_ontology.assert_called_once()

        # Verify generator was called with correct arguments
        call_args = mock_generator_instance.generate_improved_ontology.call_args
        self.assertEqual(call_args[0][0], mock_parser_instance)  # ontology
        self.assertEqual(call_args[0][2], str(self.output_ttl))  # output file
        self.assertEqual(call_args[0][3], str(self.report_file))  # report file

    @patch("sys.argv")
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.OntologyParser")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    @patch("os.path.exists")
    def test_ttl_file_interactive_mode_workflow(
        self,
        mock_exists,
        mock_ols,
        mock_bioportal,
        mock_parser,
        mock_generator,
        mock_lookup,
        mock_argv,
    ):
        """Test complete TTL file processing with interactive selection workflow"""
        # Setup mocks
        mock_exists.return_value = True

        mock_bioportal_instance = MagicMock()
        mock_ols_instance = MagicMock()
        mock_lookup_instance = MagicMock()
        mock_generator_instance = MagicMock()
        mock_parser_instance = MagicMock()

        mock_bioportal.return_value = mock_bioportal_instance
        mock_ols.return_value = mock_ols_instance
        mock_lookup.return_value = mock_lookup_instance
        mock_generator.return_value = mock_generator_instance
        mock_parser.return_value = mock_parser_instance

        # Mock parser methods
        mock_parser_instance.parse.return_value = True
        mock_parser_instance.get_priority_concepts.return_value = [
            {"key": "cancer", "label": "Cancer", "type": "class", "category": "test"}
        ]

        # Mock lookup results for interactive selection
        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0004992",
                    "label": "Cancer",
                    "source": "ols",
                    "ontology": "MONDO",
                    "description": "A disease",
                    "synonyms": ["malignancy"],
                }
            ],
            {"discrepancies": [], "bioportal_count": 1, "ols_count": 1},
        )

        cli = CLIInterface()

        # Override parser to use our test args
        test_args = cli.parser.parse_args(
            [str(self.sample_ttl_file), "--output", str(self.output_ttl)]
        )

        # Mock user inputs for interactive selection
        with patch("builtins.input", side_effect=["1", "y"]):  # Select option 1, confirm
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                # Run the CLI
                cli.run()

        # Verify interactions
        mock_parser.assert_called_once_with(str(self.sample_ttl_file))
        mock_lookup_instance.lookup_concept.assert_called_once()
        mock_generator_instance.generate_improved_ontology.assert_called_once()

    @patch("sys.argv")
    def test_list_ontologies_workflow(self, mock_argv):
        """Test list ontologies workflow"""
        mock_argv.__getitem__ = lambda self, index: ["cli", "--list-ontologies"][index]
        mock_argv.__len__ = lambda self: 2

        cli = CLIInterface()

        # Override parser to use our test args
        test_args = cli.parser.parse_args(["--list-ontologies"])

        with patch.object(cli.parser, "parse_args", return_value=test_args):
            with patch("cli.interface.logger") as mock_logger:
                # Run the CLI
                cli.run()

                # Verify ontology information was logged
                mock_logger.info.assert_called()
                logged_messages = [call.args[0] for call in mock_logger.info.call_args_list]

                # Check that ontology information was displayed
                self.assertTrue(any("Available Ontologies" in msg for msg in logged_messages))
                self.assertTrue(any("Individual Ontologies:" in msg for msg in logged_messages))
                self.assertTrue(any("Recommended Combinations:" in msg for msg in logged_messages))

    @patch("sys.argv")
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_single_word_no_results_workflow(
        self, mock_ols, mock_bioportal, mock_generator, mock_lookup, mock_argv
    ):
        """Test single word query workflow when no results are found"""
        # Setup mocks
        mock_argv.__getitem__ = lambda self, index: [
            "cli",
            "--single-word",
            "nonexistentterm",
            "--ontologies",
            "MONDO",
        ][index]
        mock_argv.__len__ = lambda self: 5

        mock_bioportal_instance = MagicMock()
        mock_ols_instance = MagicMock()
        mock_lookup_instance = MagicMock()

        mock_bioportal.return_value = mock_bioportal_instance
        mock_ols.return_value = mock_ols_instance
        mock_lookup.return_value = mock_lookup_instance

        # Mock no results found
        mock_lookup_instance.lookup_concept.return_value = (
            [],
            {"discrepancies": [], "bioportal_count": 0, "ols_count": 0},
        )

        cli = CLIInterface()

        # Override parser to use our test args
        test_args = cli.parser.parse_args(
            ["--single-word", "nonexistentterm", "--ontologies", "MONDO"]
        )

        with patch.object(cli.parser, "parse_args", return_value=test_args):
            with patch("cli.interface.logger") as mock_logger:
                # Run the CLI
                cli.run()

                # Verify error was logged
                mock_logger.error.assert_called_with("No results found for 'nonexistentterm'")

    @patch("sys.argv")
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_single_word_skip_selection_workflow(
        self, mock_ols, mock_bioportal, mock_generator, mock_lookup, mock_argv
    ):
        """Test single word query workflow when user skips selection"""
        # Setup mocks
        mock_bioportal_instance = MagicMock()
        mock_ols_instance = MagicMock()
        mock_lookup_instance = MagicMock()

        mock_bioportal.return_value = mock_bioportal_instance
        mock_ols.return_value = mock_ols_instance
        mock_lookup.return_value = mock_lookup_instance

        # Mock lookup results
        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://example.org/test",
                    "label": "Test Term",
                    "source": "ols",
                    "ontology": "TEST",
                    "description": "A test term",
                    "synonyms": [],
                }
            ],
            {"discrepancies": [], "bioportal_count": 1, "ols_count": 1},
        )

        cli = CLIInterface()

        # Override parser to use our test args
        test_args = cli.parser.parse_args(["--single-word", "testterm", "--terminal-only"])

        # Mock user input to skip (enter '0')
        with patch("builtins.input", return_value="0"):
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                with patch("builtins.print") as mock_print:
                    # Run the CLI
                    cli.run()

                    # Verify skip message was printed
                    skip_calls = [
                        call
                        for call in mock_print.call_args_list
                        if "⏭️" in str(call.args[0]) and "Skipped" in str(call.args[0])
                    ]
                    self.assertTrue(len(skip_calls) > 0)

    @patch("sys.argv")
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_service_discrepancy_workflow(
        self, mock_ols, mock_bioportal, mock_generator, mock_lookup, mock_argv
    ):
        """Test workflow when there are discrepancies between BioPortal and OLS"""
        # Setup mocks
        mock_bioportal_instance = MagicMock()
        mock_ols_instance = MagicMock()
        mock_lookup_instance = MagicMock()

        mock_bioportal.return_value = mock_bioportal_instance
        mock_ols.return_value = mock_ols_instance
        mock_lookup.return_value = mock_lookup_instance

        # Mock lookup results with discrepancies
        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://example.org/test",
                    "label": "Test Term",
                    "source": "bioportal",
                    "ontology": "TEST",
                    "description": "A test term",
                    "synonyms": [],
                }
            ],
            {
                "discrepancies": ["Different result counts", "Source availability differences"],
                "bioportal_count": 5,
                "ols_count": 2,
            },
        )

        cli = CLIInterface()

        # Override parser to use our test args
        test_args = cli.parser.parse_args(["--single-word", "testterm", "--terminal-only"])

        # Mock user input to select first option
        with patch("builtins.input", return_value="1"):
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                with patch("cli.interface.logger") as mock_logger:
                    # Run the CLI
                    cli.run()

                    # Verify discrepancy warnings were logged
                    warning_calls = list(mock_logger.warning.call_args_list)
                    self.assertTrue(len(warning_calls) > 0)

                    # Check specific discrepancy messages
                    warning_messages = [call.args[0] for call in warning_calls]
                    self.assertTrue(
                        any("Service Comparison Alert" in msg for msg in warning_messages)
                    )
                    self.assertTrue(
                        any("Different result counts" in msg for msg in warning_messages)
                    )

    @patch("sys.argv")
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.OntologyParser")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    @patch("os.path.exists")
    def test_disable_services_workflow(
        self,
        mock_exists,
        mock_ols,
        mock_bioportal,
        mock_parser,
        mock_generator,
        mock_lookup,
        mock_argv,
    ):
        """Test workflow with disabled services (BioPortal or OLS)"""
        # Setup mocks
        mock_exists.return_value = True

        mock_bioportal_instance = MagicMock()
        mock_ols_instance = MagicMock()
        mock_lookup_instance = MagicMock()

        mock_bioportal.return_value = mock_bioportal_instance
        mock_ols.return_value = mock_ols_instance
        mock_lookup.return_value = mock_lookup_instance

        cli = CLIInterface()

        # Test with BioPortal disabled
        test_args = cli.parser.parse_args(
            ["--single-word", "cancer", "--disable-bioportal", "--terminal-only"]
        )

        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0004992",
                    "label": "Cancer",
                    "source": "ols",
                    "ontology": "MONDO",
                    "description": "A disease",
                    "synonyms": [],
                }
            ],
            {"discrepancies": [], "bioportal_count": 0, "ols_count": 1},
        )

        with patch("builtins.input", return_value="1"):
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                # Run the CLI
                cli.run()

                # Verify lookup was called
                mock_lookup_instance.lookup_concept.assert_called_once()

    @patch("sys.argv")
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.OntologyParser")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    @patch("os.path.exists")
    def test_comparison_only_workflow(
        self,
        mock_exists,
        mock_ols,
        mock_bioportal,
        mock_parser,
        mock_generator,
        mock_lookup,
        mock_argv,
    ):
        """Test comparison-only workflow (no ontology generation)"""
        # Setup mocks
        mock_exists.return_value = True

        mock_parser_instance = MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = True
        mock_parser_instance.get_priority_concepts.return_value = [
            {"key": "cancer", "label": "Cancer", "type": "class", "category": "instance"}
        ]

        mock_lookup_instance = MagicMock()
        mock_lookup.return_value = mock_lookup_instance
        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://example.org/test",
                    "label": "Test",
                    "source": "ols",
                    "ontology": "TEST",
                }
            ],
            {"discrepancies": [], "bioportal_count": 1, "ols_count": 1},
        )

        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance

        cli = CLIInterface()

        # Test comparison-only mode
        test_args = cli.parser.parse_args([str(self.sample_ttl_file), "--comparison-only"])

        with patch("builtins.input", return_value="1"):
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                # Run the CLI
                cli.run()

                # Verify parser was used but generator was not called for ontology generation
                mock_parser_instance.parse.assert_called_once()
                mock_lookup_instance.lookup_concept.assert_called_once()
                # Generator should not be called for generating improved ontology in comparison-only mode


if __name__ == "__main__":
    unittest.main()
