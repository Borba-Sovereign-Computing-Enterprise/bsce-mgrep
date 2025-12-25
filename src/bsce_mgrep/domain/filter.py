"""Filtering logic using where clauses.

This module composes multiple filter expressions into a single predicate function
using Railway-Oriented Programming.
"""

from typing import Callable
from result import Ok, Err

from bsce_mgrep.domain.types import MatchContext, FilterResult, FilterExpression
from bsce_mgrep.domain.where_parser import parse_where_expression, evaluate_where, ASTNode


def create_filter(expressions: list[FilterExpression]) -> Callable[[MatchContext], FilterResult]:
    """Create a composite filter from multiple where expressions.
    
    Multiple expressions are combined with AND logic. If no expressions are
    provided, returns a filter that always passes.
    
    Args:
        expressions: List of where clause strings
        
    Returns:
        A pure function that evaluates all filters
        
    Examples:
        >>> from bsce_mgrep.domain.types import Line, MatchContext
        >>> line = Line(1, "ERROR: Database timeout")
        >>> ctx = MatchContext(line=line, groups={})
        >>> filter_fn = create_filter(["line.length > 10"])
        >>> result = filter_fn(ctx)
        >>> result.ok_value
        True
    """
    # If no expressions, create a pass-through filter
    if not expressions:
        return lambda context: Ok(True)
    
    # Parse all expressions into ASTs
    parsed_asts: list[ASTNode] = []
    
    for expr in expressions:
        parse_result = parse_where_expression(expr)
        
        match parse_result:
            case Ok(ast):
                parsed_asts.append(ast)
            case Err(error):
                # Return a filter that always fails with the parse error
                return lambda context, err=error: Err(f"Parse error: {err}")
    
    # Create composite filter function
    def composite_filter(context: MatchContext) -> FilterResult:
        """Evaluate all ASTs with AND logic."""
        for ast in parsed_asts:
            eval_result = evaluate_where(ast, context)
            
            match eval_result:
                case Ok(value):
                    # If any filter returns False, short-circuit
                    if not value:
                        return Ok(False)
                case Err(error):
                    # Propagate evaluation errors
                    return Err(error)
        
        # All filters passed
        return Ok(True)
    
    return composite_filter


def combine_filters_and(
    filters: list[Callable[[MatchContext], FilterResult]]
) -> Callable[[MatchContext], FilterResult]:
    """Combine multiple filter functions with AND logic.
    
    This is a more general combinator for pre-built filter functions.
    
    Args:
        filters: List of filter functions
        
    Returns:
        A composite filter that applies all filters with AND logic
        
    Examples:
        >>> from bsce_mgrep.domain.types import Line, MatchContext
        >>> line = Line(1, "test")
        >>> ctx = MatchContext(line=line, groups={})
        >>> filter1 = lambda c: Ok(True)
        >>> filter2 = lambda c: Ok(True)
        >>> combined = combine_filters_and([filter1, filter2])
        >>> result = combined(ctx)
        >>> result.ok_value
        True
    """
    if not filters:
        return lambda context: Ok(True)
    
    def combined(context: MatchContext) -> FilterResult:
        """Apply all filters with short-circuit AND logic."""
        for filter_fn in filters:
            result = filter_fn(context)
            
            match result:
                case Ok(value):
                    if not value:
                        return Ok(False)
                case Err(_):
                    return result
        
        return Ok(True)
    
    return combined


def combine_filters_or(
    filters: list[Callable[[MatchContext], FilterResult]]
) -> Callable[[MatchContext], FilterResult]:
    """Combine multiple filter functions with OR logic.
    
    Args:
        filters: List of filter functions
        
    Returns:
        A composite filter that applies all filters with OR logic
        
    Examples:
        >>> from bsce_mgrep.domain.types import Line, MatchContext
        >>> line = Line(1, "test")
        >>> ctx = MatchContext(line=line, groups={})
        >>> filter1 = lambda c: Ok(False)
        >>> filter2 = lambda c: Ok(True)
        >>> combined = combine_filters_or([filter1, filter2])
        >>> result = combined(ctx)
        >>> result.ok_value
        True
    """
    if not filters:
        return lambda context: Ok(False)
    
    def combined(context: MatchContext) -> FilterResult:
        """Apply all filters with short-circuit OR logic."""
        for filter_fn in filters:
            result = filter_fn(context)
            
            match result:
                case Ok(value):
                    if value:
                        return Ok(True)
                case Err(_):
                    return result
        
        return Ok(False)
    
    return combined


def negate_filter(
    filter_fn: Callable[[MatchContext], FilterResult]
) -> Callable[[MatchContext], FilterResult]:
    """Negate a filter function (NOT logic).
    
    Args:
        filter_fn: Filter function to negate
        
    Returns:
        A filter that returns the opposite boolean result
        
    Examples:
        >>> from bsce_mgrep.domain.types import Line, MatchContext
        >>> line = Line(1, "test")
        >>> ctx = MatchContext(line=line, groups={})
        >>> always_true = lambda c: Ok(True)
        >>> negated = negate_filter(always_true)
        >>> result = negated(ctx)
        >>> result.ok_value
        False
    """
    def negated(context: MatchContext) -> FilterResult:
        """Negate the filter result."""
        result = filter_fn(context)
        
        match result:
            case Ok(value):
                return Ok(not value)
            case Err(_):
                return result
    
    return negated
