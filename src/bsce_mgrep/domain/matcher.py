"""Pattern matching logic.

This module implements literal and regex pattern matching with Railway-Oriented
error handling. Matchers are pure functions that transform Lines into MatchContexts.
"""

from dataclasses import dataclass
from typing import Callable
import re
from result import Ok, Err

from bsce_mgrep.domain.types import Line, MatchContext, MatchResult, PatternString

# Regex pattern delimiter
REGEX_DELIMITER = '/'
MIN_REGEX_LENGTH = 3  # Minimum: /x/

@dataclass(frozen=True, slots=True)
class MatchConfig:
    """Configuration for pattern matching.
    
    Attributes:
        pattern: The pattern to match (literal or /regex/)
        case_sensitive: Whether matching should be case-sensitive
        
    Examples:
        >>> config = MatchConfig(pattern="ERROR", case_sensitive=False)
        >>> config.pattern
        'ERROR'
    """
    pattern: PatternString
    case_sensitive: bool

def create_matcher(config: MatchConfig) -> Callable[[Line], MatchResult]:
    """Factory function that creates a pattern matcher.
    
    Detects pattern type and returns appropriate matcher:
    - Wrapped in /.../ → regex matcher
    - Plain string → literal matcher
    
    Args:
        config: Configuration specifying pattern and case sensitivity
        
    Returns:
        A pure matcher function: Line → Result[MatchContext, str]
        
    Examples:
        >>> config = MatchConfig(pattern="ERROR", case_sensitive=False)
        >>> matcher = create_matcher(config)
        >>> line = Line(1, "ERROR: Database timeout")
        >>> result = matcher(line)
        >>> isinstance(result, Ok)
        True
    """
    match config.pattern:
        case str() if _is_regex_pattern(config.pattern):
            return _create_regex_matcher(config)
        case str() if config.pattern:
            return _create_literal_matcher(config)
        case _:
            # Empty pattern or invalid type
            return lambda line: Err(f"Invalid pattern: {config.pattern!r}")

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
        >>> _is_regex_pattern("/")
        False
    """
    return (
        len(pattern) >= MIN_REGEX_LENGTH
        and pattern.startswith(REGEX_DELIMITER)
        and pattern.endswith(REGEX_DELIMITER)
    )

def _create_regex_matcher(config: MatchConfig) -> Callable[[Line], MatchResult]:
    """Create a regex matcher with named group support.
    
    Extracts pattern between delimiters, compiles regex, and returns a matcher
    that captures named groups for use in where clauses.
    
    Args:
        config: Match configuration with regex pattern
        
    Returns:
        A matcher function that extracts regex groups
        
    Examples:
        >>> config = MatchConfig(pattern="/status=(?P<code>\\d+)/", case_sensitive=True)
        >>> matcher = _create_regex_matcher(config)
        >>> line = Line(1, "status=500")
        >>> result = matcher(line)
        >>> result.ok_value.groups["code"]
        '500'
    """
    # Extract pattern between delimiters
    regex_pattern = config.pattern[1:-1]
    
    # Compile regex with appropriate flags
    try:
        flags = 0 if config.case_sensitive else re.IGNORECASE
        compiled_regex = re.compile(regex_pattern, flags)
    except re.error as e:
        # Return a matcher that always fails with the compilation error
        error_message = f"Invalid regex pattern: {e}"
        return lambda line: Err(error_message)
    
    def matcher(line: Line) -> MatchResult:
        """Match line content against compiled regex."""
        match = compiled_regex.search(line.content)
        
        if match:
            # Extract named groups (empty dict if no groups)
            groups = match.groupdict()
            return Ok(MatchContext(line=line, groups=groups))
        else:
            return Err(f"No match at line {line.number}")
    
    return matcher

def _create_literal_matcher(config: MatchConfig) -> Callable[[Line], MatchResult]:
    """Create a literal string matcher.
    
    Performs simple substring matching with optional case sensitivity.
    No regex groups are captured.
    
    Args:
        config: Match configuration with literal pattern
        
    Returns:
        A matcher function for literal string matching
        
    Examples:
        >>> config = MatchConfig(pattern="ERROR", case_sensitive=False)
        >>> matcher = _create_literal_matcher(config)
        >>> line = Line(1, "error: timeout")
        >>> result = matcher(line)
        >>> isinstance(result, Ok)
        True
    """
    # Prepare pattern and content transformation based on case sensitivity
    if config.case_sensitive:
        search_pattern = config.pattern
        transform = lambda s: s
    else:
        search_pattern = config.pattern.lower()
        transform = lambda s: s.lower()
    
    def matcher(line: Line) -> MatchResult:
        """Match line content against literal pattern."""
        transformed_content = transform(line.content)
        
        if search_pattern in transformed_content:
            # Literal matches have no captured groups
            return Ok(MatchContext(line=line, groups={}))
        else:
            return Err(f"No match at line {line.number}")
    
    return matcher
