"""
CLI handling tools.
"""

import argparse
import sys

__all__ = ['command_line_entry_point']

class CLIHandler:
    
    def __init__(self, argv: list[str] = None) -> None:
        """
        Utility class for handling command line arguments.

        Attributes:
            argv        Custom arguments that should get parsed. If none given, use sys.argv[1:].
        
        """
        
        self._argv = argv or sys.argv[1:]
        self._parser: argparse.ArgumentParser

        self._create_parser()

    @property
    def argv(self) -> list[str]:
        return self._argv

    def _create_parser(self):
        """Create the parser for discord-taskbot."""

        self._parser =  argparse.ArgumentParser(prog='discord-taskbot', description="Task management utility for small programming teams using Discord.")

    def execute(self) -> None:
        """
        Given the command-line arguments, figure out which subcommand is being
        run, create an appropriate parser and run depending on the parsing result.
        """

        try:
            self._execute()
        except SystemExit:
            pass
        except KeyboardInterrupt:
            pass
    
    def _execute(self) -> None:
        result = self._parser.parse_args(self._argv)


def command_line_entry_point(argv: list[str] = None):
    """Execute a command line handler."""
    handler = CLIHandler(argv)
    handler.execute()
