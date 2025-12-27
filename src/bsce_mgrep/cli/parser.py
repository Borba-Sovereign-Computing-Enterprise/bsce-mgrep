"""CLI argument parsing using argparse.

This module handles command-line argument parsing and validation.
Returns immutable CLIArgs dataclass using Railway-Oriented Programming.
"""

import argparse
import sys
from dataclasses import dataclass
from result import Result, Ok, Err


@dataclass(frozen=True, slots=True)
class CLIArgs:
    """Parsed CLI arguments.
    
    Attributes:
        source: File path or None (for stdin)
        pattern: Pattern to match (literal or /regex/)
        case_sensitive: Whether matching is case-sensitive
        where_clauses: List of where clause expressions
        
    Examples:
        >>> args = CLIArgs(
        ...     source="app.log",
        ...     pattern="ERROR",
        ...     case_sensitive=False,
        ...     where_clauses=["line.length > 80"]
        ... )
        >>> args.pattern
        'ERROR'
    """
    source: str | None
    pattern: str
    case_sensitive: bool
    where_clauses: list[str]


def parse_args(argv: list[str] | None = None) -> Result[CLIArgs, str]:
    """Parse CLI arguments using argparse.
    
    Args:
        argv: Arguments to parse (defaults to sys.argv)
        
    Returns:
        Result containing CLIArgs or error message
        
    Examples:
        >>> result = parse_args(["test.log", "--match", "ERROR"])
        >>> isinstance(result, Ok)
        True
        >>> result.ok_value.pattern
        'ERROR'
    """
    parser = argparse.ArgumentParser(
        prog='mgrep',
        description='Functional grep with semantic filtering',
        epilog='''
Examples:
  mgrep app.log --match 'ERROR'
  mgrep app.log --match '/status=(?<code>\\d+)/' --where 'group("code") >= 500'
  cat app.log | mgrep --match 'ERROR'
  mgrep app.log --match 'error' --case insensitive
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'source',
        nargs='?',  # Optional positional argument
        help='Input file (omit to read from stdin if piped)'
    )
    
    parser.add_argument(
        '--match',
        required=True,
        metavar='PATTERN',
        help='Pattern to match: literal string or /regex/ with optional named groups'
    )
    
    parser.add_argument(
        '--case',
        choices=['sensitive', 'insensitive'],
        metavar='MODE',
        help='Case sensitivity: sensitive or insensitive (default: insensitive for literals, sensitive for regex)'
    )
    
    parser.add_argument(
        '--where',
        action='append',
        default=[],
        dest='where_clauses',
        metavar='EXPR',
        help='Semantic filter expression (can be specified multiple times for AND logic)'
    )
    
    try:
        args = parser.parse_args(argv)
        
        # Validate source input
        if args.source is None and not _is_stdin_piped():
            return Err("No input source: provide a file path or pipe input via stdin")
        
        # Determine case sensitivity
        case_sensitive = _determine_case_sensitivity(
            args.match,
            args.case
        )
        
        return Ok(CLIArgs(
            source=args.source,
            pattern=args.match,
            case_sensitive=case_sensitive,
            where_clauses=args.where_clauses
        ))
    
    except SystemExit as e:
        # argparse calls sys.exit on error or --help
        if e.code == 0:
            # --help was requested
            return Err("Help requested")
        else:
            return Err("Invalid arguments")


def _determine_case_sensitivity(pattern: str, case_flag: str | None) -> bool:
    """Determine case sensitivity based on pattern type and explicit flag.
    
    Logic:
    - If explicit flag provided → use it
    - Else if regex pattern → sensitive (default)
    - Else if literal pattern → insensitive (default)
    
    Args:
        pattern: The match pattern
        case_flag: Explicit case flag ('sensitive' or 'insensitive' or None)
        
    Returns:
        True for case-sensitive, False for case-insensitive
        
    Examples:
        >>> _determine_case_sensitivity("ERROR", None)
        False
        >>> _determine_case_sensitivity("/ERROR/", None)
        True
        >>> _determine_case_sensitivity("ERROR", "sensitive")
        True
    """
    # Explicit flag takes precedence
    if case_flag == 'sensitive':
        return True
    if case_flag == 'insensitive':
        return False
    
    # Auto-detect based on pattern type
    if _is_regex_pattern(pattern):
        # Regex default: case-sensitive
        return True
    else:
        # Literal default: case-insensitive
        return False


def _is_regex_pattern(pattern: str) -> bool:
    """Check if pattern is wrapped in /.../ delimiters.
    
    Args:
        pattern: Pattern string to check
        
    Returns:
        True if pattern has regex delimiters
        
    Examples:
        >>> _is_regex_pattern("/test/")
        True
        >>> _is_regex_pattern("test")
        False
    """
    return (
        len(pattern) >= 3
        and pattern.startswith('/')
        and pattern.endswith('/')
    )


def _is_stdin_piped() -> bool:
    """Check if stdin is piped (not a TTY).
    
    Returns:
        True if stdin is piped, False if interactive terminal
        
    Examples:
        >>> # In terminal: _is_stdin_piped() → False
        >>> # In pipe (cat file | prog): _is_stdin_piped() → True
    """
    return not sys.stdin.isatty()
