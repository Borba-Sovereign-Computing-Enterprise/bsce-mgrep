"""Entry point for mgrep CLI.

This module provides the main() function that serves as the entry point
for the mgrep command-line tool.
"""

import sys
from result import Ok, Err

from bsce_mgrep.cli.parser import parse_args
from bsce_mgrep.cli.runner import run


def main() -> int:
    """Main entry point for the CLI.
    
    Parses arguments, executes pipeline, and returns exit code.
    
    Returns:
        0 on success, 1 on error
        
    Side Effects:
        - Reads from stdin or file
        - Writes to stdout (matches)
        - Writes to stderr (errors)
        - Exits with appropriate code
    """
    # Parse CLI arguments
    args_result = parse_args()
    
    match args_result:
        case Err(error):
            if error != "Help requested":
                print(f"Error: {error}", file=sys.stderr)
            return 1
        case Ok(args):
            pass
    
    # Execute pipeline
    run_result = run(args)
    
    match run_result:
        case Ok(_):
            return 0
        case Err(error):
            print(f"Error: {error}", file=sys.stderr)
            return 1


if __name__ == '__main__':
    sys.exit(main())
