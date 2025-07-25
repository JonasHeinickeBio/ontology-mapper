#!/usr/bin/env python3
"""
Configure logging for the ontology-mapper project.
This script allows users to set up logging configuration for different use cases.
"""

import argparse

from config.logging_config import setup_logging


def main():
    """Configure logging based on command line arguments."""
    parser = argparse.ArgumentParser(
        description="Configure logging for the ontology-mapper project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic logging to console
  python configure_logging.py

  # Verbose logging to console and file
  python configure_logging.py --verbose --log-file logs/debug.log

  # Quiet mode (errors only) with JSON format
  python configure_logging.py --quiet --log-file logs/errors.json --json-format

  # Custom log level to file
  python configure_logging.py --level DEBUG --log-file logs/detailed.log
        """,
    )

    parser.add_argument(
        "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )

    parser.add_argument("--log-file", type=str, help="Write logs to this file")

    parser.add_argument(
        "--json-format", action="store_true", help="Use JSON format for file logging"
    )

    parser.add_argument("--no-console", action="store_true", help="Disable console logging")

    parser.add_argument("--quiet", action="store_true", help="Suppress INFO and DEBUG messages")

    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG level logging")

    parser.add_argument(
        "--test", action="store_true", help="Run logging tests to verify configuration"
    )

    args = parser.parse_args()

    # Configure logging
    logger = setup_logging(
        level=args.level,
        log_file=args.log_file,
        console=not args.no_console,
        json_format=args.json_format,
        quiet=args.quiet,
        verbose=args.verbose,
    )

    # Test logging configuration
    if args.test:
        test_logging_configuration(logger)
    else:
        # Show configuration
        show_logging_configuration(args, logger)


def test_logging_configuration(logger):
    """Test the logging configuration with sample messages."""
    print("Testing logging configuration...")
    print("=" * 50)

    # Test different log levels
    logger.debug("This is a DEBUG message - detailed information for debugging")
    logger.info("This is an INFO message - general information about progress")
    logger.warning("This is a WARNING message - something unexpected happened")
    logger.error("This is an ERROR message - something went wrong")
    logger.critical("This is a CRITICAL message - serious error occurred")

    # Test structured logging
    logger.info(
        "Processing concept: melanoma",
        extra={
            "extra_fields": {"concept_id": "NCIT_C3224", "ontology": "NCIT", "operation": "lookup"}
        },
    )

    # Test performance logging
    import time

    start_time = time.time()
    time.sleep(0.1)  # Simulate some work
    duration = time.time() - start_time
    logger.info(
        f"Operation completed in {duration:.2f}s",
        extra={
            "extra_fields": {
                "operation": "concept_lookup",
                "duration_seconds": duration,
                "performance_metric": True,
            }
        },
    )

    print("\nLogging test completed. Check your console and log files.")


def show_logging_configuration(args, logger):
    """Show the current logging configuration."""
    print("Logging Configuration")
    print("=" * 30)
    print(f"Level: {args.level}")
    print(f"Console: {'No' if args.no_console else 'Yes'}")
    print(f"Log file: {args.log_file or 'None'}")
    print(f"JSON format: {'Yes' if args.json_format else 'No'}")
    print(f"Quiet mode: {'Yes' if args.quiet else 'No'}")
    print(f"Verbose mode: {'Yes' if args.verbose else 'No'}")
    print()

    # Show sample log message
    logger.info("Logging configuration applied successfully")
    print("Sample log message sent. Use --test to run comprehensive logging tests.")


if __name__ == "__main__":
    main()
