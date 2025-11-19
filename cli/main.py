"""
Main CLI entry point.
"""

import sys
import logging
import traceback
from .interface import CLIInterface
from utils.logging_config import setup_logging
from utils.error_handling import (
    OntologyMapperError,
    format_error_message
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point with enhanced error handling"""
    # Initialize logging (reads from environment variables)
    try:
        setup_logging()
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize logging: {e}")
    
    try:
        cli = CLIInterface()
        cli.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print(f"\n\n⏹️  Interrupted by user. Exiting...")
        sys.exit(0)
    except OntologyMapperError as e:
        # Application-specific errors with user-friendly messages
        error_msg = format_error_message(e, user_friendly=True)
        print(f"\n{error_msg}")
        logger.error(f"Application error: {e}")
        sys.exit(1)
    except Exception as e:
        # Unexpected errors
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Provide helpful information in verbose mode
        if logger.isEnabledFor(logging.DEBUG):
            print("\nDebug information:")
            traceback.print_exc()
        
        sys.exit(1)


if __name__ == '__main__':
    main()
