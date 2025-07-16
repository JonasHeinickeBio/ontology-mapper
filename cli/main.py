"""
Main CLI entry point.
"""

import sys

from .interface import CLIInterface


def main():
    """Main entry point"""
    try:
        cli = CLIInterface()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
