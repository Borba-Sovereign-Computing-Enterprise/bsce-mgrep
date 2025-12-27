"""Source reader port (interface).

This module defines the protocol for reading lines from various sources.
Adapters implement this protocol for specific input sources (file, stdin, etc.).
"""

from typing import Protocol, Iterator

from bsce_mgrep.domain.types import LineResult

class SourceReader(Protocol):
    """Protocol for reading lines from a source.
    
    Implementations should yield LineResult objects, handling errors gracefully
    by yielding Err values instead of raising exceptions.
    
    Examples:
        >>> from dataclasses import dataclass
        >>> from result import Ok
        >>> from bsce_mgrep.domain.types import Line
        >>> 
        >>> @dataclass
        >>> class DummyReader:
        ...     def read_lines(self) -> Iterator[LineResult]:
        ...         yield Ok(Line(1, "test"))
        >>> 
        >>> reader: SourceReader = DummyReader()
        >>> lines = list(reader.read_lines())
        >>> len(lines)
        1
    """
    
    def read_lines(self) -> Iterator[LineResult]:
        """Read lines from source, yielding Results.
        
        Yields:
            Ok(Line) for successful reads
            Err(str) for errors (file not found, permission denied, etc.)
            
        Note:
            Should not raise exceptions - all errors should be yielded as Err.
        """
        ...
