"""
Unit tests for config/logging_config.py module.
"""

import json
import logging
import os
import sys
import tempfile
import threading
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from config.logging_config import (
    ColoredFormatter,
    JSONFormatter,
    get_logger,
    setup_logging,
)


class TestLoggingConfig(unittest.TestCase):
    """Unit tests for logging configuration"""

    def setUp(self):
        """Set up test fixtures"""
        # Clear any existing handlers
        logging.getLogger().handlers.clear()

    def tearDown(self):
        """Clean up after tests"""
        # Clear handlers after each test
        logging.getLogger().handlers.clear()

    def test_colored_formatter_initialization(self):
        """Test ColoredFormatter initialization"""
        formatter = ColoredFormatter()
        self.assertIsInstance(formatter, logging.Formatter)
        self.assertIn("DEBUG", formatter.COLORS)
        self.assertIn("INFO", formatter.COLORS)
        self.assertIn("ERROR", formatter.COLORS)

    def test_colored_formatter_format(self):
        """Test ColoredFormatter format method"""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")

        # Create test log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Should contain color codes and message
        self.assertIn("Test message", formatted)
        # Original levelname should be preserved
        self.assertEqual(record.levelname, "INFO")

    def test_json_formatter_initialization(self):
        """Test JSONFormatter initialization"""
        formatter = JSONFormatter()
        self.assertIsInstance(formatter, logging.Formatter)

    def test_json_formatter_format(self):
        """Test JSONFormatter format method"""
        formatter = JSONFormatter()

        # Create test log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        parsed = json.loads(formatted)
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["message"], "Test message")
        self.assertEqual(parsed["logger"], "test")
        self.assertEqual(parsed["line"], 1)

    def test_json_formatter_with_exception(self):
        """Test JSONFormatter with exception info"""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )

            formatted = formatter.format(record)
            parsed = json.loads(formatted)

            self.assertIn("exception", parsed)
            self.assertIn("ValueError", parsed["exception"])

    def test_setup_logging_basic(self):
        """Test basic logging setup"""
        logger = setup_logging()

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.level, logging.INFO)
        self.assertGreater(len(logger.handlers), 0)

    def test_setup_logging_with_level(self):
        """Test logging setup with specific level"""
        logger = setup_logging(level="DEBUG")

        self.assertEqual(logger.level, logging.DEBUG)

    def test_setup_logging_quiet_mode(self):
        """Test logging setup with quiet mode"""
        logger = setup_logging(quiet=True)

        self.assertEqual(logger.level, logging.WARNING)

    def test_setup_logging_verbose_mode(self):
        """Test logging setup with verbose mode"""
        logger = setup_logging(verbose=True)

        self.assertEqual(logger.level, logging.DEBUG)

    def test_setup_logging_with_file(self):
        """Test logging setup with file output"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            logger = setup_logging(log_file=temp_path)

            # Should have file handler
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            self.assertGreater(len(file_handlers), 0)

        finally:
            import os

            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_setup_logging_json_format(self):
        """Test logging setup with JSON format"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            logger = setup_logging(log_file=temp_path, json_format=True)

            # Should have JSON formatter
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            self.assertGreater(len(file_handlers), 0)

            file_handler = file_handlers[0]
            self.assertIsInstance(file_handler.formatter, JSONFormatter)

        finally:
            import os

            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_setup_logging_no_console(self):
        """Test logging setup without console output"""
        logger = setup_logging(console=False)

        # Should not have console handler
        console_handlers = [
            h
            for h in logger.handlers
            if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
        ]
        self.assertEqual(len(console_handlers), 0)

    def test_get_logger_basic(self):
        """Test basic logger creation"""
        logger = get_logger("test_module")

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_module")

    def test_get_logger_with_name(self):
        """Test logger creation with specific name"""
        logger = get_logger("my.module.name")

        self.assertEqual(logger.name, "my.module.name")

    def test_logging_level_string_handling(self):
        """Test handling of string logging levels"""
        test_levels = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]

        for level_str, expected_level in test_levels:
            with self.subTest(level=level_str):
                logger = setup_logging(level=level_str)
                self.assertEqual(logger.level, expected_level)

    def test_logging_invalid_level(self):
        """Test handling of invalid logging level"""
        # Should default to INFO for invalid level
        logger = setup_logging(level="INVALID")
        self.assertEqual(logger.level, logging.INFO)

    def test_multiple_handlers_setup(self):
        """Test setup with multiple handlers"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            logger = setup_logging(log_file=temp_path, console=True)

            # Should have both console and file handlers
            self.assertGreater(len(logger.handlers), 1)

            # Check for different handler types
            handler_types = [type(h).__name__ for h in logger.handlers]
            self.assertIn("FileHandler", handler_types)
            self.assertIn("StreamHandler", handler_types)

        finally:
            import os

            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_error_handler_setup(self):
        """Test error handler setup"""
        logger = setup_logging()

        # Should have error handler for stderr
        error_handlers = [
            h
            for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
            and hasattr(h, "stream")
            and h.stream == sys.stderr
        ]
        self.assertGreater(len(error_handlers), 0)

        # Error handler should be set to WARNING level
        if error_handlers:
            error_handler = error_handlers[0]
            self.assertEqual(error_handler.level, logging.WARNING)

    def test_handler_formatting(self):
        """Test handler formatting setup"""
        logger = setup_logging()

        # All handlers should have formatters
        for handler in logger.handlers:
            self.assertIsNotNone(handler.formatter)

    def test_log_file_directory_creation(self):
        """Test log file directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "logs", "test.log")

            setup_logging(log_file=log_path)

            # Directory should be created
            self.assertTrue(os.path.exists(os.path.dirname(log_path)))

    def test_concurrent_logging_setup(self):
        """Test concurrent logging setup (thread safety)"""
        import threading

        results = []

        def setup_logger():
            logger = setup_logging()
            results.append(logger is not None)

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=setup_logger)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All setups should succeed
        self.assertTrue(all(results))

    def test_logging_with_extra_fields(self):
        """Test JSONFormatter with extra fields"""
        formatter = JSONFormatter()

        # Create record with extra fields
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add extra fields
        record.extra_fields = {"user_id": "123", "request_id": "abc"}

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        # Should include extra fields
        self.assertEqual(parsed["user_id"], "123")
        self.assertEqual(parsed["request_id"], "abc")


if __name__ == "__main__":
    unittest.main()
