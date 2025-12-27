"""Domain types for bsce-mgrep.

This module defines the core domain types used throughout the application.
All types are immutable and represent pure domain concepts.
"""

from dataclasses import dataclass
from result import Result

# Type aliases using Python 3.12 syntax
type LineNumber = int
type LineContent = str
type PatternString = str
type FilterExpression = str
type ErrorMessage = str

@dataclass(frozen=True, slots=True)
class Line:
    """Represents a single line from input source.
    
    Attributes:
        number: 1-indexed line number in the source
        content: Raw line content (without trailing newline)
    
    Examples:
        >>> line = Line(number=1, content="ERROR: Database timeout")
        >>> line.length
        23
        >>> line.contains("Database")
        True
    """
    number: LineNumber
    content: LineContent
    
    @property
    def length(self) -> int:
        """Character count of line content.
        
        Returns:
            Number of characters in the content string
        """
        return len(self.content)
    
    def contains(self, text: str) -> bool:
        """Check if line contains substring.
        
        Args:
            text: Substring to search for
            
        Returns:
            True if text is found in content
            
        Examples:
            >>> Line(1, "ERROR: timeout").contains("ERROR")
            True
        """
        return text in self.content
    
    def startswith(self, text: str) -> bool:
        """Check if line starts with substring.
        
        Args:
            text: Prefix to search for
            
        Returns:
            True if content starts with text
            
        Examples:
            >>> Line(1, "ERROR: timeout").startswith("ERROR")
            True
        """
        return self.content.startswith(text)
    
    def endswith(self, text: str) -> bool:
        """Check if line ends with substring.
        
        Args:
            text: Suffix to search for
            
        Returns:
            True if content ends with text
            
        Examples:
            >>> Line(1, "status=500").endswith("500")
            True
        """
        return self.content.endswith(text)

@dataclass(frozen=True, slots=True)
class MatchContext:
    """Context available during filtering.
    
    Combines matched line with any captured regex groups for use in
    where clause evaluation.
    
    Attributes:
        line: The matched Line object
        groups: Dictionary of named regex capture groups
        
    Examples:
        >>> line = Line(1, "status=500")
        >>> ctx = MatchContext(line=line, groups={"code": "500"})
        >>> ctx.groups["code"]
        '500'
    """
    line: Line
    groups: dict[str, str]

# Result types for Railway-Oriented Programming
type LineResult = Result[Line, ErrorMessage]
type MatchResult = Result[MatchContext, ErrorMessage]
type FilterResult = Result[bool, ErrorMessage]
