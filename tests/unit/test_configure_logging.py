"""Unit tests for configure_logging.py module."""

import unittest
import unittest.mock
from unittest.mock import Mock, patch

from configure_logging import main


class TestConfigureLogging(unittest.TestCase):
    """Unit tests for configure_logging.py module"""

    @patch("configure_logging.setup_logging")
    @patch("configure_logging.show_logging_configuration")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_default_arguments(self, mock_parse_args, mock_show_config, mock_setup_logging):
        """Test main with default arguments"""
        mock_args = Mock()
        mock_args.level = "INFO"
        mock_args.log_file = None
        mock_args.no_console = False
        mock_args.json_format = False
        mock_args.quiet = False
        mock_args.verbose = False
        mock_args.test = False
        mock_parse_args.return_value = mock_args

        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger

        main()

        # Should call setup_logging with correct arguments
        mock_setup_logging.assert_called_once_with(
            level="INFO",
            log_file=None,
            console=True,
            json_format=False,
            quiet=False,
            verbose=False,
        )
        # Should show configuration
        mock_show_config.assert_called_once_with(mock_args, mock_logger)

    @patch("configure_logging.setup_logging")
    @patch("configure_logging.test_logging_configuration")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_test_mode(self, mock_parse_args, mock_test_config, mock_setup_logging):
        """Test main with test mode enabled"""
        mock_args = Mock()
        mock_args.level = "DEBUG"
        mock_args.log_file = None
        mock_args.no_console = False
        mock_args.json_format = False
        mock_args.quiet = False
        mock_args.verbose = False
        mock_args.test = True
        mock_parse_args.return_value = mock_args

        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger

        main()

        # Should call test_logging_configuration
        mock_test_config.assert_called_once_with(mock_logger)

    @patch("configure_logging.setup_logging")
    @patch("configure_logging.show_logging_configuration")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_verbose_mode(self, mock_parse_args, mock_show_config, mock_setup_logging):
        """Test main with verbose mode"""
        mock_args = Mock()
        mock_args.level = "INFO"
        mock_args.log_file = None
        mock_args.no_console = False
        mock_args.json_format = False
        mock_args.quiet = False
        mock_args.verbose = True
        mock_args.test = False
        mock_parse_args.return_value = mock_args

        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger

        main()

        mock_setup_logging.assert_called_once_with(
            level="INFO",
            log_file=None,
            console=True,
            json_format=False,
            quiet=False,
            verbose=True,
        )

    @patch("configure_logging.setup_logging")
    @patch("configure_logging.show_logging_configuration")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_quiet_mode(self, mock_parse_args, mock_show_config, mock_setup_logging):
        """Test main with quiet mode"""
        mock_args = Mock()
        mock_args.level = "INFO"
        mock_args.log_file = None
        mock_args.no_console = False
        mock_args.json_format = False
        mock_args.quiet = True
        mock_args.verbose = False
        mock_args.test = False
        mock_parse_args.return_value = mock_args

        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger

        main()

        mock_setup_logging.assert_called_once_with(
            level="INFO",
            log_file=None,
            console=True,
            json_format=False,
            quiet=True,
            verbose=False,
        )

    @patch("configure_logging.setup_logging")
    @patch("configure_logging.show_logging_configuration")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_log_file(self, mock_parse_args, mock_show_config, mock_setup_logging):
        """Test main with log file specified"""
        mock_args = Mock()
        mock_args.level = "INFO"
        mock_args.log_file = "test.log"
        mock_args.no_console = False
        mock_args.json_format = False
        mock_args.quiet = False
        mock_args.verbose = False
        mock_args.test = False
        mock_parse_args.return_value = mock_args

        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger

        main()

        mock_setup_logging.assert_called_once_with(
            level="INFO",
            log_file="test.log",
            console=True,
            json_format=False,
            quiet=False,
            verbose=False,
        )

    @patch("configure_logging.setup_logging")
    @patch("configure_logging.show_logging_configuration")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_json_format(self, mock_parse_args, mock_show_config, mock_setup_logging):
        """Test main with JSON format"""
        mock_args = Mock()
        mock_args.level = "INFO"
        mock_args.log_file = None
        mock_args.no_console = False
        mock_args.json_format = True
        mock_args.quiet = False
        mock_args.verbose = False
        mock_args.test = False
        mock_parse_args.return_value = mock_args

        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger

        main()

        mock_setup_logging.assert_called_once_with(
            level="INFO",
            log_file=None,
            console=True,
            json_format=True,
            quiet=False,
            verbose=False,
        )

    @patch("configure_logging.setup_logging")
    @patch("configure_logging.show_logging_configuration")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_no_console(self, mock_parse_args, mock_show_config, mock_setup_logging):
        """Test main with no console output"""
        mock_args = Mock()
        mock_args.level = "INFO"
        mock_args.log_file = None
        mock_args.no_console = True
        mock_args.json_format = False
        mock_args.quiet = False
        mock_args.verbose = False
        mock_args.test = False
        mock_parse_args.return_value = mock_args

        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger

        main()

        mock_setup_logging.assert_called_once_with(
            level="INFO",
            log_file=None,
            console=False,
            json_format=False,
            quiet=False,
            verbose=False,
        )

    def test_configure_logging_module_docstring(self):
        """Test configure_logging module has docstring"""
        import configure_logging as config_module

        docstring = config_module.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("Configure logging", docstring)

    @patch("builtins.print")
    @patch("time.sleep")
    @patch("time.time")
    def test_test_logging_configuration(self, mock_time, mock_sleep, mock_print):
        """Test test_logging_configuration function"""
        from configure_logging import test_logging_configuration

        # Mock time.time() to return predictable values for duration calculation
        mock_time.side_effect = [100.0, 100.1]  # start_time, end_time

        # Create a mock logger
        mock_logger = Mock()

        # Call the function
        test_logging_configuration(mock_logger)

        # Verify all log levels were called
        mock_logger.debug.assert_called_once_with(
            "This is a DEBUG message - detailed information for debugging"
        )
        mock_logger.info.assert_called()  # Called multiple times
        mock_logger.warning.assert_called_once_with(
            "This is a WARNING message - something unexpected happened"
        )
        mock_logger.error.assert_called_once_with("This is an ERROR message - something went wrong")
        mock_logger.critical.assert_called_once_with(
            "This is a CRITICAL message - serious error occurred"
        )

        # Verify structured logging calls
        expected_calls = [
            unittest.mock.call("This is an INFO message - general information about progress"),
            unittest.mock.call(
                "Processing concept: melanoma",
                extra={
                    "extra_fields": {
                        "concept_id": "NCIT_C3224",
                        "ontology": "NCIT",
                        "operation": "lookup",
                    }
                },
            ),
        ]

        # Check the first two info calls
        for expected_call in expected_calls:
            self.assertIn(expected_call, mock_logger.info.call_args_list)

        # Check the performance call separately - duration may vary due to floating point precision
        performance_calls = [
            call
            for call in mock_logger.info.call_args_list
            if call[1]
            and "extra_fields" in call[1].get("extra", {})
            and call[1]["extra"]["extra_fields"].get("performance_metric")
        ]

        self.assertEqual(len(performance_calls), 1)
        performance_call = performance_calls[0]
        self.assertIn("Operation completed in", performance_call[0][0])
        self.assertEqual(
            performance_call[1]["extra"]["extra_fields"]["operation"], "concept_lookup"
        )
        self.assertTrue(performance_call[1]["extra"]["extra_fields"]["performance_metric"])
        # Duration should be close to 0.1
        duration = performance_call[1]["extra"]["extra_fields"]["duration_seconds"]
        self.assertAlmostEqual(duration, 0.1, places=1)

        # Verify print statements
        self.assertTrue(mock_print.called)
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        self.assertIn("Testing logging configuration...", print_calls)
        self.assertIn("=" * 50, print_calls)

    @patch("builtins.print")
    def test_show_logging_configuration(self, mock_print):
        """Test show_logging_configuration function"""
        from configure_logging import show_logging_configuration

        # Create mock args and logger
        mock_args = Mock()
        mock_args.level = "DEBUG"
        mock_args.no_console = False
        mock_args.log_file = "test.log"
        mock_args.json_format = True
        mock_args.quiet = False
        mock_args.verbose = True

        mock_logger = Mock()

        # Call the function
        show_logging_configuration(mock_args, mock_logger)

        # Verify logger.info was called
        mock_logger.info.assert_called_once_with("Logging configuration applied successfully")

        # Verify print statements
        self.assertTrue(mock_print.called)
        # Get the actual printed text - handle empty calls
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # If there are positional arguments
                print_calls.append(call[0][0])

        # Convert to string to check for content
        print_output = " ".join(str(call) for call in print_calls)
        self.assertIn("Logging Configuration", print_output)
        self.assertIn("Level: DEBUG", print_output)
        self.assertIn("Console: Yes", print_output)
        self.assertIn("Log file: test.log", print_output)
        self.assertIn("JSON format: Yes", print_output)
        self.assertIn("Quiet mode: No", print_output)
        self.assertIn("Verbose mode: Yes", print_output)
        self.assertIn(
            "Sample log message sent. Use --test to run comprehensive logging tests.", print_calls
        )

    @patch("builtins.print")
    def test_show_logging_configuration_no_console_no_log_file(self, mock_print):
        """Test show_logging_configuration with no console and no log file"""
        from configure_logging import show_logging_configuration

        # Create mock args and logger
        mock_args = Mock()
        mock_args.level = "WARNING"
        mock_args.no_console = True
        mock_args.log_file = None
        mock_args.json_format = False
        mock_args.quiet = True
        mock_args.verbose = False

        mock_logger = Mock()

        # Call the function
        show_logging_configuration(mock_args, mock_logger)

        # Verify print statements include specific values
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # If there are positional arguments
                print_calls.append(call[0][0])

        # Convert to string to check for content
        print_output = " ".join(str(call) for call in print_calls)
        self.assertIn("Level: WARNING", print_output)
        self.assertIn("Console: No", print_output)
        self.assertIn("Log file: None", print_output)
        self.assertIn("JSON format: No", print_output)
        self.assertIn("Quiet mode: Yes", print_output)
        self.assertIn("Verbose mode: No", print_output)

    @patch("time.sleep")
    @patch("time.time")
    def test_test_logging_configuration_timing(self, mock_time, mock_sleep):
        """Test test_logging_configuration timing calculation"""
        from configure_logging import test_logging_configuration

        # Mock time.time() to return specific values
        mock_time.side_effect = [200.0, 200.5]  # Different duration

        mock_logger = Mock()

        # Call the function
        test_logging_configuration(mock_logger)

        # Verify the performance logging call with correct duration
        performance_call = None
        for call in mock_logger.info.call_args_list:
            if len(call[0]) > 0 and "Operation completed in" in call[0][0]:
                performance_call = call
                break

        self.assertIsNotNone(performance_call)
        if performance_call is not None:
            self.assertIn("Operation completed in 0.50s", performance_call[0][0])

            # Check the extra fields
            extra = performance_call[1]["extra"]
            self.assertEqual(extra["extra_fields"]["duration_seconds"], 0.5)
            self.assertEqual(extra["extra_fields"]["operation"], "concept_lookup")
            self.assertTrue(extra["extra_fields"]["performance_metric"])


if __name__ == "__main__":
    unittest.main()
