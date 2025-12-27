"""Pipeline composition using Railway-Oriented Programming.

This module composes the core processing pipeline: reading → matching → filtering.
All stages use Result types for error handling along success/failure tracks.
"""

from typing import Iterator, Callable
from result import Result, Ok, Err

from bsce_mgrep.domain.types import Line, MatchContext, LineResult, MatchResult, FilterResult


def build_pipeline(
    matcher: Callable[[Line], MatchResult],
    filter_fn: Callable[[MatchContext], FilterResult],
) -> Callable[[Iterator[LineResult]], Iterator[Result[MatchContext, str]]]:
    """Compose the processing pipeline with Railway-Oriented Programming.
    
    Pipeline stages:
        1. Lines (from reader)
        2. Match against pattern
        3. Filter with where clauses
        4. Yield successful matches
    
    Errors at any stage are propagated but don't stop processing of other lines.
    
    Args:
        matcher: Function to match lines against pattern
        filter_fn: Function to apply where clause filters
        
    Returns:
        A function that transforms an iterator of LineResults into MatchContexts
        
    Examples:
        >>> from bsce_mgrep.domain.types import Line
        >>> from bsce_mgrep.domain.matcher import MatchConfig, create_matcher
        >>> from bsce_mgrep.domain.filter import create_filter
        >>> 
        >>> config = MatchConfig(pattern="ERROR", case_sensitive=False)
        >>> matcher = create_matcher(config)
        >>> filter_fn = create_filter([])
        >>> pipeline = build_pipeline(matcher, filter_fn)
        >>> 
        >>> lines = [Ok(Line(1, "ERROR: timeout")), Ok(Line(2, "INFO: ok"))]
        >>> results = list(pipeline(iter(lines)))
        >>> len([r for r in results if isinstance(r, Ok)])
        1
    """
    def pipeline(lines: Iterator[LineResult]) -> Iterator[Result[MatchContext, str]]:
        """Process lines through match → filter stages."""
        for line_result in lines:
            # Stage 1: Check if line was read successfully
            match line_result:
                case Err(error):
                    # Propagate read errors
                    yield Err(error)
                    continue
                case Ok(line):
                    pass
            
            # Stage 2: Match line against pattern
            match_result = matcher(line)
            
            match match_result:
                case Err(_):
                    # Line doesn't match - silently skip
                    # (this is normal, not an error to report)
                    continue
                case Ok(context):
                    pass
            
            # Stage 3: Apply where clause filters
            filter_result = filter_fn(context)
            
            match filter_result:
                case Err(error):
                    # Filter evaluation error - report and skip
                    yield Err(error)
                    continue
                case Ok(passes):
                    if passes:
                        # All filters passed - yield the match
                        yield Ok(context)
                    # else: filter rejected - silently skip
    
    return pipeline


def build_simple_pipeline(
    matcher: Callable[[Line], MatchResult],
) -> Callable[[Iterator[LineResult]], Iterator[MatchContext]]:
    """Build a pipeline with only matching (no filtering).
    
    Convenience function for pipelines that don't need where clauses.
    
    Args:
        matcher: Function to match lines against pattern
        
    Returns:
        A pipeline function without filtering stage
        
    Examples:
        >>> from bsce_mgrep.domain.types import Line
        >>> from bsce_mgrep.domain.matcher import MatchConfig, create_matcher
        >>> 
        >>> config = MatchConfig(pattern="ERROR", case_sensitive=False)
        >>> matcher = create_matcher(config)
        >>> pipeline = build_simple_pipeline(matcher)
        >>> 
        >>> lines = [Ok(Line(1, "ERROR: timeout"))]
        >>> results = list(pipeline(iter(lines)))
        >>> len(results)
        1
    """
    no_filter: Callable[[MatchContext], FilterResult] = lambda ctx: Ok(True)
    return build_pipeline(matcher, no_filter)


def compose_matchers(
    matchers: list[Callable[[Line], MatchResult]]
) -> Callable[[Line], MatchResult]:
    """Compose multiple matchers with OR logic.
    
    Returns the first successful match, or Err if none match.
    
    Args:
        matchers: List of matcher functions
        
    Returns:
        A composite matcher that tries all matchers
        
    Examples:
        >>> from bsce_mgrep.domain.types import Line
        >>> from bsce_mgrep.domain.matcher import MatchConfig, create_matcher
        >>> 
        >>> config1 = MatchConfig(pattern="ERROR", case_sensitive=False)
        >>> config2 = MatchConfig(pattern="WARN", case_sensitive=False)
        >>> matcher1 = create_matcher(config1)
        >>> matcher2 = create_matcher(config2)
        >>> combined = compose_matchers([matcher1, matcher2])
        >>> 
        >>> line = Line(1, "WARN: low memory")
        >>> result = combined(line)
        >>> isinstance(result, Ok)
        True
    """
    if not matchers:
        return lambda line: Err("No matchers provided")
    
    def composite(line: Line) -> MatchResult:
        """Try all matchers until one succeeds."""
        errors = []
        
        for matcher in matchers:
            result = matcher(line)
            
            match result:
                case Ok(_):
                    return result
                case Err(error):
                    errors.append(error)
        
        # None matched
        return Err(f"No match (tried {len(matchers)} patterns)")
    
    return composite


def count_results(results: Iterator[Result[MatchContext, str]]) -> tuple[int, int]:
    """Count successes and errors in a result stream.
    
    Consumes the iterator and returns counts. Useful for statistics.
    
    Args:
        results: Iterator of Results to count
        
    Returns:
        Tuple of (success_count, error_count)
        
    Examples:
        >>> from bsce_mgrep.domain.types import Line, MatchContext
        >>> line = Line(1, "test")
        >>> ctx = MatchContext(line=line, groups={})
        >>> results = [Ok(ctx), Err("error"), Ok(ctx)]
        >>> count_results(iter(results))
        (2, 1)
    """
    success_count = 0
    error_count = 0
    
    for result in results:
        match result:
            case Ok(_):
                success_count += 1
            case Err(_):
                error_count += 1
    
    return success_count, error_count
