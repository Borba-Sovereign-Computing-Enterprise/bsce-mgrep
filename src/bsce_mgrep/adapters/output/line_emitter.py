"""Plain text line emitter.

This module implements the output adapter for emitting matched lines to stdout.
Errors are written to stderr.
"""

import sys
from dataclasses import dataclass
from typing import Iterator
from result import Result, Ok, Err

from bsce_mgrep.domain.types import MatchContext


@dataclass(frozen=True, slots=True)
class LineEmitter:
    """Adapter for emitting matched lines to stdout.
    
    Writes matching line content to stdout and errors to stderr.
    This is a pure output adapter at the boundary of the system.
    
    Attributes:
        show_line_numbers: Whether to prefix output with line numbers
        
    Examples:
        >>> from bsce_mgrep.domain.types import Line, MatchContext
        >>> line = Line(1, "ERROR: timeout")
        >>> ctx = MatchContext(line=line, groups={})
        >>> emitter = LineEmitter()
        >>> emitter.emit(iter([Ok(ctx)]))
        ERROR: timeout
    """
    show_line_numbers: bool = False
    
    def emit(self, contexts: Iterator[Result[MatchContext, str]]) -> None:
        """Emit matched lines to stdout.
        
        Successful matches are written to stdout. Errors are written to stderr.
        Each line is written as-is (original content).
        
        Args:
            contexts: Iterator of MatchContext Results to emit
            
        Side Effects:
            Writes to sys.stdout (matches)
            Writes to sys.stderr (errors)
        """
        for result in contexts:
            match result:
                case Ok(context):
                    if self.show_line_numbers:
                        print(f"{context.line.number}:{context.line.content}", file=sys.stdout)
                    else:
                        print(context.line.content, file=sys.stdout)
                case Err(error):
                    print(f"Error: {error}", file=sys.stderr)
    
    def emit_with_groups(self, contexts: Iterator[Result[MatchContext, str]]) -> None:
        """Emit matched lines with captured groups.
        
        Shows both the line and any regex groups that were captured.
        Useful for debugging or when groups are important.
        
        Args:
            contexts: Iterator of MatchContext Results to emit
            
        Side Effects:
            Writes to sys.stdout (matches with groups)
            Writes to sys.stderr (errors)
        """
        for result in contexts:
            match result:
                case Ok(context):
                    line_prefix = f"{context.line.number}:" if self.show_line_numbers else ""
                    print(f"{line_prefix}{context.line.content}", file=sys.stdout)
                    
                    if context.groups:
                        for name, value in context.groups.items():
                            print(f"  {name}: {value}", file=sys.stdout)
                case Err(error):
                    print(f"Error: {error}", file=sys.stderr)


@dataclass(frozen=True, slots=True)
class CountingEmitter:
    """Emitter that counts matches instead of printing them.
    
    Useful for implementing a --count flag (future feature).
    
    Examples:
        >>> from bsce_mgrep.domain.types import Line, MatchContext
        >>> line = Line(1, "ERROR: timeout")
        >>> ctx = MatchContext(line=line, groups={})
        >>> emitter = CountingEmitter()
        >>> emitter.emit(iter([Ok(ctx)]))
        >>> emitter.match_count
        1
    """
    
    def __post_init__(self):
        """Initialize mutable counter.
        
        Note: This breaks immutability, but is isolated to I/O boundary.
        For pure functional alternative, use count_results from pipeline.
        """
        object.__setattr__(self, 'match_count', 0)
        object.__setattr__(self, 'error_count', 0)
    
    def emit(self, contexts: Iterator[Result[MatchContext, str]]) -> None:
        """Count matches and errors.
        
        Args:
            contexts: Iterator of MatchContext Results to count
            
        Side Effects:
            Updates internal counters
        """
        for result in contexts:
            match result:
                case Ok(_):
                    object.__setattr__(self, 'match_count', self.match_count + 1)
                case Err(_):
                    object.__setattr__(self, 'error_count', self.error_count + 1)
        
        # Print counts
        print(f"Matches: {self.match_count}", file=sys.stdout)
        if self.error_count > 0:
            print(f"Errors: {self.error_count}", file=sys.stderr)
