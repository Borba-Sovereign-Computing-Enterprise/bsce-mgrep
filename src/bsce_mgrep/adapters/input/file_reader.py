"""File reading adapter.

This module implements the SourceReader protocol for reading from files.
Handles common file errors gracefully using Railway-Oriented Programming.
"""

from dataclasses import dataclass
from typing import Iterator
from result import Ok, Err

from bsce_mgrep.domain.types import Line, LineResult


@dataclass(frozen=True, slots=True)
class FileReader:
    """Adapter for reading lines from a file.
    
    Implements the SourceReader protocol. Handles common file errors:
    - File not found
    - Permission denied
    - I/O errors during reading
    
    Attributes:
        filepath: Path to the file to read
        
    Examples:
        >>> reader = FileReader(filepath="test.log")
        >>> lines = reader.read_lines()
        >>> # Yields LineResult objects
    """
    filepath: str
    
    def read_lines(self) -> Iterator[LineResult]:
        """Read lines from file.
        
        Opens file, reads line by line, and yields LineResult objects.
        Errors are yielded as Err values, not raised as exceptions.
        
        Yields:
            Ok(Line) for each successfully read line
            Err(str) if file cannot be opened or read
            
        Note:
            Line numbers start at 1 (not 0).
            Trailing newlines are stripped from content.
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                for line_number, content in enumerate(file, start=1):
                    yield Ok(Line(
                        number=line_number,
                        content=content.rstrip('\n\r')
                    ))
        except FileNotFoundError:
            yield Err(f"File not found: {self.filepath}")
        except PermissionError:
            yield Err(f"Permission denied: {self.filepath}")
        except IsADirectoryError:
            yield Err(f"Is a directory: {self.filepath}")
        except IOError as e:
            yield Err(f"Read error: {e}")
        except UnicodeDecodeError as e:
            yield Err(f"Encoding error: {e}")
