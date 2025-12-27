"""Stdin reading adapter.

This module implements the SourceReader protocol for reading from stdin.
Handles stdin errors gracefully using Railway-Oriented Programming.
"""

import sys
from dataclasses import dataclass
from typing import Iterator
from result import Ok, Err

from bsce_mgrep.domain.types import Line, LineResult


@dataclass(frozen=True, slots=True)
class StdinReader:
    """Adapter for reading lines from stdin.
    
    Implements the SourceReader protocol. Handles stdin I/O errors gracefully.
    
    Examples:
        >>> reader = StdinReader()
        >>> lines = reader.read_lines()
        >>> # Yields LineResult objects from stdin
    """
    
    def read_lines(self) -> Iterator[LineResult]:
        """Read lines from stdin.
        
        Reads from sys.stdin line by line and yields LineResult objects.
        Errors are yielded as Err values, not raised as exceptions.
        
        Yields:
            Ok(Line) for each successfully read line
            Err(str) if stdin cannot be read
            
        Note:
            Line numbers start at 1 (not 0).
            Trailing newlines are stripped from content.
            Handles BrokenPipeError gracefully (e.g., when piped to head).
        """
        try:
            for line_number, content in enumerate(sys.stdin, start=1):
                yield Ok(Line(
                    number=line_number,
                    content=content.rstrip('\n\r')
                ))
        except BrokenPipeError:
            # This is normal when piping to commands like head
            # that close the pipe early - not an error
            pass
        except IOError as e:
            yield Err(f"Stdin read error: {e}")
        except UnicodeDecodeError as e:
            yield Err(f"Stdin encoding error: {e}")
        except KeyboardInterrupt:
            # User interrupted with Ctrl+C - not an error
            pass
