"""
CLI handling tools.
"""

import argparse
import sys
import discord_taskbot

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

        parser =  argparse.ArgumentParser(prog='discord-taskbot', description="Task management utility for small programming teams using Discord.")
        parser.add_argument('--version', action='store_true', help="print version info and exit", dest="version")

        # activate subparsers (== subcommands)
        subparsers = parser.add_subparsers(help='sub-command help')

        # 'run' subcommand
        parser_run = subparsers.add_parser(
            name='run',
            description="Run the bot with an .env file.",
            help='run the bot')
        parser_run.add_argument('envfile', help="attach an .env file")
        parser_run.set_defaults(func=self._subcommand_run)

        self._parser = parser

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
        result = self._parser.parse_args(self.argv)
        self._pre_subcmd_executing(result)
        
        result.func(result)

    def _pre_subcmd_executing(self, args: argparse.Namespace) -> None:
        """Stuff that always should be executed before executing subcommand dependent code."""
        
        arg_vars = vars(args)

        # print version info
        if arg_vars.get('version'):
            print (discord_taskbot.__version__)
            sys.exit()

        func = arg_vars.get('func', None)
        if not func:
            self._parser.print_help()
            sys.exit()
        
    
    def _subcommand_run(self, args: argparse.Namespace) -> None:
        import dotenv, os
        from pathlib import Path
        from discord_taskbot.bot import BOT

        envfile = Path(args.envfile)
        if not envfile.is_file():
            print ("Passed .env-file does not exist.")
            sys.exit()

        dotenv.load_dotenv(envfile)
        TOKEN = os.getenv("TOKEN")

        BOT.run(TOKEN)


def command_line_entry_point(argv: list[str] = None):
    """Execute a command line handler."""
    handler = CLIHandler(argv)
    handler.execute()
