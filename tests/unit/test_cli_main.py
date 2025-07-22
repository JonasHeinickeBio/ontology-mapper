"""Unit tests for cli/main.py module."""

import sys
import unittest
from unittest.mock import Mock, patch

from cli.main import main


class TestCliMain(unittest.TestCase):
    """Unit tests for cli/main.py module"""

    @patch("cli.main.CLIInterface")
    def test_main_successful_execution(self, mock_cli_interface):
        """Test successful main execution"""
        mock_cli = Mock()
        mock_cli_interface.return_value = mock_cli

        main()

        # Should create CLI interface and run it
        mock_cli_interface.assert_called_once()
        mock_cli.run.assert_called_once()

    @patch("cli.main.logger")
    @patch("cli.main.CLIInterface")
    @patch("sys.exit")
    def test_main_keyboard_interrupt(self, mock_exit, mock_cli_interface, mock_logger):
        """Test main handles KeyboardInterrupt gracefully"""
        mock_cli = Mock()
        mock_cli.run.side_effect = KeyboardInterrupt("User interrupted")
        mock_cli_interface.return_value = mock_cli

        main()

        # Should log interruption and exit with code 0
        mock_logger.info.assert_called_with("Interrupted by user. Exiting...")
        mock_exit.assert_called_with(0)

    @patch("cli.main.logger")
    @patch("cli.main.CLIInterface")
    @patch("sys.exit")
    def test_main_unexpected_exception(self, mock_exit, mock_cli_interface, mock_logger):
        """Test main handles unexpected exceptions"""
        mock_cli = Mock()
        test_error = RuntimeError("Unexpected error")
        mock_cli.run.side_effect = test_error
        mock_cli_interface.return_value = mock_cli

        main()

        # Should log error and exit with code 1
        mock_logger.error.assert_called_with(f"Unexpected error: {test_error}")
        mock_exit.assert_called_with(1)

    @patch("cli.main.logger")
    @patch("cli.main.CLIInterface")
    @patch("sys.exit")
    def test_main_cli_creation_error(self, mock_exit, mock_cli_interface, mock_logger):
        """Test main handles CLI creation errors"""
        mock_cli_interface.side_effect = ImportError("CLI creation failed")

        main()

        # Should exit with error code
        mock_exit.assert_called_with(1)
        mock_logger.error.assert_called()

    def test_main_module_docstring(self):
        """Test cli.main module has correct docstring"""
        import cli.main as cli_main_module

        docstring = cli_main_module.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("Main", docstring)
            self.assertIn("entry point", docstring)

    @patch("cli.main.CLIInterface")
    def test_main_with_various_exception_types(self, mock_cli_interface):
        """Test main handles various exception types"""
        mock_cli = Mock()
        mock_cli_interface.return_value = mock_cli

        # Test with different exception types
        exceptions = [ValueError("Test error"), OSError("File error"), TypeError("Type error")]

        for exception in exceptions:
            with self.subTest(exception=type(exception).__name__):
                with patch("cli.main.logger") as mock_logger:
                    with patch("sys.exit") as mock_exit:
                        mock_cli.run.side_effect = exception

                        main()

                        mock_logger.error.assert_called()
                        mock_exit.assert_called_with(1)

    @patch("cli.main.logger")
    @patch("cli.main.CLIInterface")
    def test_main_exception_message_formatting(self, mock_cli_interface, mock_logger):
        """Test exception message formatting"""
        mock_cli = Mock()
        mock_cli_interface.return_value = mock_cli
        test_message = "Custom error message"
        mock_cli.run.side_effect = Exception(test_message)

        with patch("sys.exit"):
            main()

        # Should format error message correctly
        mock_logger.error.assert_called_with(f"Unexpected error: {test_message}")

    @patch("cli.main.CLIInterface")
    def test_main_execution_order(self, mock_cli_interface):
        """Test main execution order"""
        mock_cli = Mock()
        mock_cli_interface.return_value = mock_cli

        main()

        # Should create CLI first, then run it
        mock_cli_interface.assert_called_once()
        mock_cli.run.assert_called_once()

    def test_main_logger_creation(self):
        """Test main creates logger correctly"""
        # Test that logger is available
        from cli.main import logger

        self.assertIsNotNone(logger)


if __name__ == "__main__":
    unittest.main()
