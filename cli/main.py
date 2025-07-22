"""
Main CLI entry point.
"""

import sys

from config.logging_config import get_logger

from .interface import CLIInterface

logger = get_logger(__name__)


def main():
    """Main entry point"""
    try:
        cli = CLIInterface()
        cli.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
