"""Railway-Oriented Programming utilities.

This module provides utilities for working with Result types in a Railway-Oriented
Programming style, where operations are composed along success/failure tracks.
"""

from typing import Callable, TypeVar, Iterator
from result import Result, Ok, Err

# Type variables for generic Result operations
A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
E = TypeVar('E')
F = TypeVar('F')

def bind(f: Callable[[A], Result[B, E]]) -> Callable[[Result[A, E]], Result[B, E]]:
    """Monadic bind for Result (flatMap / chain).
    
    Transforms a function that works on values into a function that works on Results.
    If the input is Ok, applies f. If the input is Err, propagates the error.
    
    Args:
        f: A function that takes a value and returns a Result
        
    Returns:
        A function that takes a Result and returns a Result
        
    Examples:
        >>> def safe_divide(x: int) -> Result[int, str]:
        ...     return Ok(10 // x) if x != 0 else Err("division by zero")
        >>> bound_fn = bind(safe_divide)
        >>> bound_fn(Ok(2))
        Ok(5)
        >>> bound_fn(Ok(0))
        Err('division by zero')
        >>> bound_fn(Err("previous error"))
        Err('previous error')
    """
    def bound(result: Result[A, E]) -> Result[B, E]:
        match result:
            case Ok(value):
                return f(value)
            case Err(error):
                return Err(error)
    return bound


def map_result(f: Callable[[A], B]) -> Callable[[Result[A, E]], Result[B, E]]:
    """Map over the success value of a Result.
    
    Transforms a function that works on values into a function that works on Results.
    If the input is Ok, applies f and wraps in Ok. If Err, propagates the error.
    
    Args:
        f: A pure function to apply to success values
        
    Returns:
        A function that maps over Results
        
    Examples:
        >>> double = lambda x: x * 2
        >>> mapped = map_result(double)
        >>> mapped(Ok(5))
        Ok(10)
        >>> mapped(Err("error"))
        Err('error')
    """
    def mapped(result: Result[A, E]) -> Result[B, E]:
        match result:
            case Ok(value):
                return Ok(f(value))
            case Err(error):
                return Err(error)
    return mapped


def map_error(f: Callable[[E], F]) -> Callable[[Result[A, E]], Result[A, F]]:
    """Map over the error value of a Result.
    
    Transforms error messages while preserving success values unchanged.
    
    Args:
        f: A function to transform error values
        
    Returns:
        A function that maps over Result errors
        
    Examples:
        >>> add_prefix = lambda e: f"ERROR: {e}"
        >>> mapped = map_error(add_prefix)
        >>> mapped(Err("timeout"))
        Err('ERROR: timeout')
        >>> mapped(Ok(42))
        Ok(42)
    """
    def mapped(result: Result[A, E]) -> Result[A, F]:
        match result:
            case Ok(value):
                return Ok(value)
            case Err(error):
                return Err(f(error))
    return mapped


def filter_results(
    predicate: Callable[[A], bool],
    error_message: str = "Filtered out"
) -> Callable[[Iterator[Result[A, E]]], Iterator[Result[A, E]]]:
    """Filter an iterator of Results by applying predicate to Ok values.
    
    Ok values that pass the predicate are yielded unchanged.
    Ok values that fail the predicate are converted to Err.
    Err values are always yielded unchanged.
    
    Args:
        predicate: Function to test Ok values
        error_message: Error message for filtered-out values
        
    Returns:
        A function that filters iterators of Results
        
    Examples:
        >>> is_even = lambda x: x % 2 == 0
        >>> filtered = filter_results(is_even, "not even")
        >>> list(filtered([Ok(2), Ok(3), Err("error"), Ok(4)]))
        [Ok(2), Err('not even'), Err('error'), Ok(4)]
    """
    def filtered(results: Iterator[Result[A, E]]) -> Iterator[Result[A, E]]:
        for result in results:
            match result:
                case Ok(value):
                    if predicate(value):
                        yield result
                    else:
                        yield Err(error_message)
                case Err(_):
                    yield result
    return filtered

def collect_ok(results: Iterator[Result[A, E]]) -> list[A]:
    """Collect only the Ok values from an iterator of Results.
    
    Silently discards all Err values. Useful for extracting successful results
    when errors have already been logged or handled.
    
    Args:
        results: Iterator of Result values
        
    Returns:
        List of unwrapped Ok values
        
    Examples:
        >>> results = [Ok(1), Err("error"), Ok(2), Ok(3), Err("another error")]
        >>> collect_ok(iter(results))
        [1, 2, 3]
    """
    return [value for result in results if isinstance(result, Ok) for value in [result.ok_value]]

def collect_errors(results: Iterator[Result[A, E]]) -> list[E]:
    """Collect only the error values from an iterator of Results.
    
    Silently discards all Ok values. Useful for error aggregation and reporting.
    
    Args:
        results: Iterator of Result values
        
    Returns:
        List of unwrapped Err values
        
    Examples:
        >>> results = [Ok(1), Err("error1"), Ok(2), Err("error2")]
        >>> collect_errors(iter(results))
        ['error1', 'error2']
    """
    return [error for result in results if isinstance(result, Err) for error in [result.err_value]]

def unwrap_or(default: A) -> Callable[[Result[A, E]], A]:
    """Unwrap a Result, providing a default value for Err cases.
    
    Args:
        default: Value to return if Result is Err
        
    Returns:
        A function that unwraps Results with a fallback
        
    Examples:
        >>> unwrap = unwrap_or(0)
        >>> unwrap(Ok(42))
        42
        >>> unwrap(Err("error"))
        0
    """
    def unwrapper(result: Result[A, E]) -> A:
        match result:
            case Ok(value):
                return value
            case Err(_):
                return default
    return unwrapper

def unwrap_or_else(f: Callable[[E], A]) -> Callable[[Result[A, E]], A]:
    """Unwrap a Result, computing a default from the error.
    
    Args:
        f: Function to compute default from error value
        
    Returns:
        A function that unwraps Results with computed fallback
        
    Examples:
        >>> handle_error = lambda e: f"Error occurred: {e}"
        >>> unwrap = unwrap_or_else(handle_error)
        >>> unwrap(Ok("success"))
        'success'
        >>> unwrap(Err("timeout"))
        'Error occurred: timeout'
    """
    def unwrapper(result: Result[A, E]) -> A:
        match result:
            case Ok(value):
                return value
            case Err(error):
                return f(error)
    return unwrapper
