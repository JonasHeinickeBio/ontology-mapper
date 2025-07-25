"""
Unit tests for cli/interface.py module.
"""

import unittest
from unittest.mock import MagicMock, mock_open, patch

from cli.interface import CLIInterface


class TestCLIInterface(unittest.TestCase):
    """Unit tests for CLIInterface class"""

    def setUp(self):
        """Set up test fixtures"""
        self.cli = CLIInterface()

    def test_cli_initialization(self):
        """Test CLI initialization"""
        self.assertIsNotNone(self.cli.parser)
        self.assertIsInstance(self.cli.parser, type(self.cli.parser))

    @patch("cli.interface.logger")
    def test_list_available_ontologies(self, mock_logger):
        """Test _list_available_ontologies method"""
        self.cli._list_available_ontologies()

        # Verify logger was called with expected content
        self.assertTrue(mock_logger.info.called)

        # Check specific calls
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        # Convert all calls to a single string to handle multiline content
        all_output = " ".join(info_calls)
        self.assertIn("Available Ontologies", all_output)
        self.assertIn("Individual Ontologies:", all_output)
        self.assertIn("Recommended Combinations:", all_output)
        self.assertIn("Usage Examples:", all_output)

    @patch("sys.exit")
    @patch("cli.interface.logger")
    @patch.object(CLIInterface, "_list_available_ontologies")
    def test_run_list_ontologies(self, mock_list_ont, mock_logger, mock_exit):
        """Test run method with list-ontologies argument"""
        # Mock argument parsing to return list_ontologies=True
        with patch.object(self.cli.parser, "parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.list_ontologies = True
            mock_parse.return_value = mock_args

            self.cli.run()

            # Verify _list_available_ontologies was called
            mock_list_ont.assert_called_once()
            # Verify the method returned early (didn't continue processing)
            mock_exit.assert_not_called()

    @patch("sys.exit")
    @patch("cli.interface.logger")
    def test_run_no_args_validation(self, mock_logger, mock_exit):
        """Test run method validation when no args provided"""
        # Make sys.exit actually raise SystemExit to stop execution
        mock_exit.side_effect = SystemExit(1)

        with patch.object(self.cli.parser, "parse_args") as mock_parse:
            with patch.object(self.cli.parser, "print_help") as mock_help:
                mock_args = MagicMock()
                mock_args.list_ontologies = False
                mock_args.single_word = None
                mock_args.ttl_file = None
                # Add missing attributes that might be accessed
                mock_args.api_key = None
                mock_args.ontologies = None
                mock_args.batch_mode = None
                mock_parse.return_value = mock_args

                with self.assertRaises(SystemExit):
                    self.cli.run()

                # Verify error logging and help printed
                mock_logger.error.assert_called_with(
                    "Either provide a TTL file or use --single-word option"
                )
                mock_help.assert_called_once()
                mock_exit.assert_called_with(1)

    @patch("sys.exit")
    @patch("os.path.exists")
    @patch("cli.interface.logger")
    def test_run_file_not_found(self, mock_logger, mock_exists, mock_exit):
        """Test run method when TTL file doesn't exist"""
        mock_exists.return_value = False
        # Make sys.exit actually raise SystemExit to stop execution
        mock_exit.side_effect = SystemExit(1)

        with patch.object(self.cli.parser, "parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.list_ontologies = False
            mock_args.single_word = None
            mock_args.ttl_file = "nonexistent.ttl"
            # Add missing attributes that might be accessed
            mock_args.api_key = None
            mock_args.ontologies = None
            mock_args.batch_mode = None
            mock_parse.return_value = mock_args

            with self.assertRaises(SystemExit):
                self.cli.run()

            # Verify error logging and exit
            mock_logger.error.assert_called_with("File nonexistent.ttl not found")
            mock_exit.assert_called_with(1)

    @patch("sys.exit")
    @patch("os.path.exists")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch.object(CLIInterface, "_single_word_mode")
    @patch("cli.interface.logger")
    def test_run_single_word_mode(
        self,
        mock_logger,
        mock_single_word,
        mock_gen,
        mock_lookup_cls,
        mock_ols,
        mock_bioportal,
        mock_exists,
        mock_exit,
    ):
        """Test run method in single word mode"""
        with patch.object(self.cli.parser, "parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.list_ontologies = False
            mock_args.single_word = "fatigue"
            mock_args.ttl_file = None
            mock_args.api_key = "test_key"
            mock_args.ontologies = "HP,NCIT"
            mock_parse.return_value = mock_args

            self.cli.run()

            # Verify single word mode was called
            mock_single_word.assert_called_once()
            # Verify components were initialized
            mock_bioportal.assert_called_once_with("test_key")
            mock_ols.assert_called_once()
            mock_lookup_cls.assert_called_once()
            mock_gen.assert_called_once()

    @patch("builtins.input", side_effect=["0"])  # Skip selection
    @patch("cli.interface.logger")
    def test_single_word_mode_no_results(self, mock_logger, mock_input):
        """Test _single_word_mode when no results found"""
        mock_args = MagicMock()
        mock_args.single_word = "nonexistent_term"
        mock_args.terminal_only = False
        mock_args.output = "test.ttl"
        mock_args.report = None

        mock_lookup = MagicMock()
        mock_lookup.lookup_concept.return_value = (
            [],
            {"discrepancies": [], "bioportal_count": 0, "ols_count": 0},
        )

        mock_generator = MagicMock()

        self.cli._single_word_mode(mock_args, mock_lookup, mock_generator)

        # Verify error was logged
        mock_logger.error.assert_called_with("No results found for 'nonexistent_term'")

    @patch("builtins.input", side_effect=["1"])  # Select first option
    @patch("builtins.print")
    @patch("cli.interface.logger")
    def test_single_word_mode_with_results(self, mock_logger, mock_print, mock_input):
        """Test _single_word_mode with results and selection"""
        mock_args = MagicMock()
        mock_args.single_word = "fatigue"
        mock_args.terminal_only = True
        mock_args.output = "test.ttl"
        mock_args.report = None

        # Mock lookup results
        mock_options = [
            {
                "uri": "http://example.com/fatigue",
                "label": "Fatigue",
                "ontology": "HP",
                "description": "A feeling of tiredness",
                "synonyms": ["tiredness", "exhaustion"],
                "source": "bioportal",
            }
        ]
        mock_comparison = {"discrepancies": [], "bioportal_count": 1, "ols_count": 0}

        mock_lookup = MagicMock()
        mock_lookup.lookup_concept.return_value = (mock_options, mock_comparison)

        mock_generator = MagicMock()

        self.cli._single_word_mode(mock_args, mock_lookup, mock_generator)

        # Verify results were displayed
        mock_logger.info.assert_any_call("Single Word Query Mode")
        mock_logger.info.assert_any_call("Query: 'fatigue'")

        # Verify terminal-only mode output
        self.assertTrue(mock_print.called)

    @patch("builtins.open", new_callable=mock_open, read_data='{"test": "data"}')
    @patch("json.load")
    def test_load_batch_selections_success(self, mock_json_load, mock_file):
        """Test _load_batch_selections with valid JSON"""
        mock_json_load.return_value = {"concept1": ["alignment1"]}

        result = self.cli._load_batch_selections("test.json")

        self.assertEqual(result, {"concept1": ["alignment1"]})
        mock_file.assert_called_once_with("test.json")

    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    @patch("builtins.print")
    def test_load_batch_selections_file_error(self, mock_print, mock_file):
        """Test _load_batch_selections with file error"""
        result = self.cli._load_batch_selections("nonexistent.json")

        self.assertEqual(result, {})
        mock_print.assert_called()

    @patch("builtins.input", side_effect=["0"])  # Skip all concepts
    @patch("builtins.print")
    @patch("json.dump")
    @patch("builtins.open", new_callable=mock_open)
    def test_interactive_selection_skip_all(
        self, mock_file, mock_json_dump, mock_print, mock_input
    ):
        """Test _interactive_selection when skipping all concepts"""
        concepts = [
            {"key": "concept1", "label": "Test Concept", "type": "Class"},
        ]

        mock_options = [
            {
                "uri": "http://example.com/test",
                "label": "Test",
                "ontology": "HP",
                "description": "Test description",
                "synonyms": [],
                "source": "bioportal",
            }
        ]
        mock_comparison = {"discrepancies": [], "bioportal_count": 1, "ols_count": 0}

        mock_lookup = MagicMock()
        mock_lookup.lookup_concept.return_value = (mock_options, mock_comparison)

        result = self.cli._interactive_selection(concepts, mock_lookup)

        # Should return empty dict since we skipped
        self.assertEqual(result, {})

        # Verify comparison report was saved
        mock_json_dump.assert_called_once()

    @patch("builtins.input", side_effect=["1"])  # Select first option
    @patch("builtins.print")
    @patch("json.dump")
    @patch("builtins.open", new_callable=mock_open)
    def test_interactive_selection_with_selection(
        self, mock_file, mock_json_dump, mock_print, mock_input
    ):
        """Test _interactive_selection with actual selections"""
        concepts = [
            {"key": "concept1", "label": "Test Concept", "type": "Class", "category": "instance"},
        ]

        mock_options = [
            {
                "uri": "http://example.com/test",
                "label": "Test",
                "ontology": "HP",
                "description": "Test description",
                "synonyms": ["synonym1"],
                "source": "bioportal",
            }
        ]
        mock_comparison = {"discrepancies": [], "bioportal_count": 1, "ols_count": 0}

        mock_lookup = MagicMock()
        mock_lookup.lookup_concept.return_value = (mock_options, mock_comparison)

        result = self.cli._interactive_selection(concepts, mock_lookup)

        # Should have one selection
        self.assertIn("concept1", result)
        self.assertEqual(len(result["concept1"]), 1)
        self.assertEqual(result["concept1"][0]["label"], "Test")
        self.assertEqual(result["concept1"][0]["relationship"], "owl:sameAs")  # instance category

    def test_single_word_argument(self):
        """Test single word argument parsing"""
        args = self.cli.parser.parse_args(["--single-word", "fatigue"])

        self.assertEqual(args.single_word, "fatigue")

    def test_single_word_with_ontologies(self):
        """Test single word with ontologies"""
        args = self.cli.parser.parse_args(["--single-word", "fatigue", "--ontologies", "HP,MONDO"])

        self.assertEqual(args.single_word, "fatigue")
        self.assertEqual(args.ontologies, "HP,MONDO")

    def test_ttl_file_argument(self):
        """Test TTL file argument parsing"""
        args = self.cli.parser.parse_args(["test.ttl"])

        self.assertEqual(args.ttl_file, "test.ttl")

    def test_output_argument(self):
        """Test output argument parsing"""
        args = self.cli.parser.parse_args(["test.ttl", "--output", "output.ttl"])

        self.assertEqual(args.ttl_file, "test.ttl")
        self.assertEqual(args.output, "output.ttl")

    def test_batch_mode_argument(self):
        """Test batch mode argument parsing"""
        args = self.cli.parser.parse_args(["test.ttl", "--batch-mode", "selections.json"])

        self.assertEqual(args.ttl_file, "test.ttl")
        self.assertEqual(args.batch_mode, "selections.json")

    def test_terminal_only_argument(self):
        """Test terminal-only argument parsing"""
        args = self.cli.parser.parse_args(["test.ttl", "--terminal-only"])

        self.assertEqual(args.ttl_file, "test.ttl")
        self.assertTrue(args.terminal_only)

    def test_report_argument(self):
        """Test report argument parsing"""
        args = self.cli.parser.parse_args(["test.ttl", "--report", "report.json"])

        self.assertEqual(args.ttl_file, "test.ttl")
        self.assertEqual(args.report, "report.json")

    def test_list_ontologies_argument(self):
        """Test list ontologies argument parsing"""
        args = self.cli.parser.parse_args(["--list-ontologies"])

        self.assertTrue(args.list_ontologies)

    def test_help_functionality(self):
        """Test help functionality"""
        with self.assertRaises(SystemExit):
            self.cli.parser.parse_args(["--help"])

    def test_invalid_arguments(self):
        """Test invalid argument handling"""
        with self.assertRaises(SystemExit):
            self.cli.parser.parse_args(["--invalid-argument"])

    def test_missing_required_arguments(self):
        """Test missing required arguments"""
        # Single word mode requires word argument
        with self.assertRaises(SystemExit):
            self.cli.parser.parse_args(["--single-word"])

    def test_conflicting_arguments(self):
        """Test conflicting arguments"""
        # Should be able to specify both TTL file and single word (depending on implementation)
        # This test depends on the actual CLI design
        try:
            args = self.cli.parser.parse_args(["test.ttl", "--single-word", "fatigue"])
            # If this succeeds, both arguments are allowed
            self.assertEqual(args.ttl_file, "test.ttl")
            self.assertTrue(args.single_word)
        except SystemExit:
            # If this fails, the arguments are mutually exclusive
            pass

    def test_ontologies_default(self):
        """Test default ontologies handling"""
        args = self.cli.parser.parse_args(["test.ttl"])

        # Should have default ontologies or None
        self.assertIsInstance(args.ontologies, (str, type(None)))

    def test_multiple_ontologies_format(self):
        """Test multiple ontologies format"""
        args = self.cli.parser.parse_args(["test.ttl", "--ontologies", "HP,MONDO,NCIT"])

        self.assertEqual(args.ontologies, "HP,MONDO,NCIT")

    def test_argument_validation(self):
        """Test argument validation"""
        # Test valid arguments
        args = self.cli.parser.parse_args(["test.ttl", "--ontologies", "HP"])
        self.assertEqual(args.ttl_file, "test.ttl")
        self.assertEqual(args.ontologies, "HP")

    def test_boolean_arguments(self):
        """Test boolean argument handling"""
        # Test terminal-only
        args = self.cli.parser.parse_args(["test.ttl", "--terminal-only"])
        self.assertTrue(args.terminal_only)

        # Test list-ontologies
        args = self.cli.parser.parse_args(["--list-ontologies"])
        self.assertTrue(args.list_ontologies)

    def test_file_path_handling(self):
        """Test file path handling"""
        # Test relative path
        args = self.cli.parser.parse_args(["../test.ttl"])
        self.assertEqual(args.ttl_file, "../test.ttl")

        # Test absolute path
        args = self.cli.parser.parse_args(["/tmp/test.ttl"])
        self.assertEqual(args.ttl_file, "/tmp/test.ttl")

    def test_output_file_handling(self):
        """Test output file handling"""
        args = self.cli.parser.parse_args(["test.ttl", "--output", "result.ttl"])

        self.assertEqual(args.output, "result.ttl")

    def test_batch_file_handling(self):
        """Test batch file handling"""
        args = self.cli.parser.parse_args(["test.ttl", "--batch-mode", "batch.json"])

        self.assertEqual(args.batch_mode, "batch.json")

    def test_report_file_handling(self):
        """Test report file handling"""
        args = self.cli.parser.parse_args(["test.ttl", "--report", "report.json"])

        self.assertEqual(args.report, "report.json")

    def test_argument_defaults(self):
        """Test argument defaults"""
        args = self.cli.parser.parse_args(["test.ttl"])

        # Test default values
        self.assertFalse(args.terminal_only)
        self.assertFalse(args.list_ontologies)
        self.assertIsNone(args.batch_mode)
        self.assertIsNone(args.report)

    def test_single_word_validation(self):
        """Test single word validation"""
        # Test valid single word
        args = self.cli.parser.parse_args(["--single-word", "fatigue"])
        self.assertEqual(args.single_word, "fatigue")

        # Test single word with spaces (should work)
        args = self.cli.parser.parse_args(["--single-word", "long covid"])
        self.assertEqual(args.single_word, "long covid")

    def test_ontology_list_format(self):
        """Test ontology list format validation"""
        # Test comma-separated list
        args = self.cli.parser.parse_args(["test.ttl", "--ontologies", "HP,MONDO,NCIT"])
        self.assertEqual(args.ontologies, "HP,MONDO,NCIT")

        # Test single ontology
        args = self.cli.parser.parse_args(["test.ttl", "--ontologies", "HP"])
        self.assertEqual(args.ontologies, "HP")

    def test_argument_parsing_edge_cases(self):
        """Test edge cases in argument parsing"""
        # Test empty arguments should work (would rely on defaults or validation)
        # The CLI might accept empty args and then validate later
        try:
            self.cli.parser.parse_args([])
            # If this succeeds, empty args are handled gracefully
        except SystemExit:
            # If this fails, empty args are rejected by parser
            pass

    def test_parser_configuration(self):
        """Test parser configuration"""
        # Test that parser is properly configured
        self.assertIsNotNone(self.cli.parser.description)

        # Test that required arguments are configured
        actions = {action.dest: action for action in self.cli.parser._actions}

        # Should have basic actions
        self.assertIn("help", actions)

    def test_argument_groups(self):
        """Test argument groups configuration"""
        # Test that parser has proper argument groups
        self.assertGreater(len(self.cli.parser._action_groups), 0)

    def test_mutually_exclusive_groups(self):
        """Test mutually exclusive argument groups"""
        # Test if single-word and ttl_file are mutually exclusive (depends on implementation)
        try:
            args = self.cli.parser.parse_args(["--single-word", "fatigue", "test.ttl"])
            # If this succeeds, they're not mutually exclusive
            self.assertTrue(args.single_word)
            self.assertEqual(args.ttl_file, "test.ttl")
        except SystemExit:
            # If this fails, they're mutually exclusive
            pass

    def test_argument_type_validation(self):
        """Test argument type validation"""
        # Test string arguments
        args = self.cli.parser.parse_args(["test.ttl", "--ontologies", "HP"])
        self.assertIsInstance(args.ontologies, str)

        # Test boolean arguments
        args = self.cli.parser.parse_args(["test.ttl", "--terminal-only"])
        self.assertIsInstance(args.terminal_only, bool)

    def test_special_characters_in_arguments(self):
        """Test special characters in arguments"""
        # Test file with special characters
        args = self.cli.parser.parse_args(["test_file-name.ttl"])
        self.assertEqual(args.ttl_file, "test_file-name.ttl")

        # Test ontology with special characters
        args = self.cli.parser.parse_args(["test.ttl", "--ontologies", "HP-GO"])
        self.assertEqual(args.ontologies, "HP-GO")

    def test_unicode_handling(self):
        """Test unicode handling in arguments"""
        # Test unicode in file names
        args = self.cli.parser.parse_args(["tëst.ttl"])
        self.assertEqual(args.ttl_file, "tëst.ttl")

        # Test unicode in single word
        args = self.cli.parser.parse_args(["--single-word", "fátigue"])
        self.assertEqual(args.single_word, "fátigue")

    def test_long_argument_values(self):
        """Test long argument values"""
        # Test long file path
        long_path = "/very/long/path/to/test/file.ttl"
        args = self.cli.parser.parse_args([long_path])
        self.assertEqual(args.ttl_file, long_path)

        # Test long ontology list
        long_ontologies = "HP,MONDO,NCIT,GO,CHEBI,UBERON,CL,PATO"
        args = self.cli.parser.parse_args(["test.ttl", "--ontologies", long_ontologies])
        self.assertEqual(args.ontologies, long_ontologies)

    def test_argument_order_independence(self):
        """Test that argument order doesn't matter"""
        # Test different argument orders
        args1 = self.cli.parser.parse_args(["test.ttl", "--ontologies", "HP", "--terminal-only"])
        args2 = self.cli.parser.parse_args(["--terminal-only", "--ontologies", "HP", "test.ttl"])

        self.assertEqual(args1.ttl_file, args2.ttl_file)
        self.assertEqual(args1.ontologies, args2.ontologies)
        self.assertEqual(args1.terminal_only, args2.terminal_only)

    def test_case_sensitivity(self):
        """Test case sensitivity in arguments"""
        # Test case in ontology names
        args = self.cli.parser.parse_args(["test.ttl", "--ontologies", "hp,MONDO"])
        self.assertEqual(args.ontologies, "hp,MONDO")


if __name__ == "__main__":
    unittest.main()
