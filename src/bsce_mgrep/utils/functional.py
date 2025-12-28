"""Functional programming utilities.

This module provides core FP primitives for function composition and transformation.
All functions are pure and support currying where appropriate.
"""

from typing import Callable, TypeVar

# Type variables for generic function composition
A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
D = TypeVar('D')

def pipe(*functions: Callable) -> Callable:
    """Compose functions left-to-right (Unix pipe style).
    
    Applies functions in sequence, passing output of each as input to the next.
    This is the natural reading order for data transformations.
    
    Args:
        *functions: Variable number of unary functions to compose
        
    Returns:
        A function that applies all functions in sequence
        
    Examples:
        >>> add_one = lambda x: x + 1
        >>> double = lambda x: x * 2
        >>> f = pipe(add_one, double)
        >>> f(5)
        12
        
    Note:
        pipe(f, g, h)(x) ≡ h(g(f(x)))
    """
    def piped(arg):
        result = arg
        for func in functions:
            result = func(result)
        return result
    return piped

def compose(*functions: Callable) -> Callable:
    """Compose functions right-to-left (mathematical style).
    
    Applies functions in reverse order of arguments. This follows mathematical
    function composition notation: (f ∘ g)(x) = f(g(x))
    
    Args:
        *functions: Variable number of unary functions to compose
        
    Returns:
        A function that applies all functions right-to-left
        
    Examples:
        >>> add_one = lambda x: x + 1
        >>> double = lambda x: x * 2
        >>> f = compose(double, add_one)
        >>> f(5)
        12
        
    Note:
        compose(f, g, h)(x) ≡ f(g(h(x)))
    """
    def composed(arg):
        result = arg
        for func in reversed(functions):
            result = func(result)
        return result
    return composed

def identity(x: A) -> A:
    """Identity function - returns its argument unchanged.
    
    Useful as a default function or for testing function composition.
    
    Args:
        x: Any value
        
    Returns:
        The same value unchanged
        
    Examples:
        >>> identity(42)
        42
        >>> identity("hello")
        'hello'
    """
    return x

def const(value: A) -> Callable[[B], A]:
    """Create a constant function that always returns the same value.
    
    Args:
        value: The value to return
        
    Returns:
        A function that ignores its argument and returns value
        
    Examples:
        >>> always_five = const(5)
        >>> always_five(100)
        5
        >>> always_five("anything")
        5
    """
    def constant_fn(_: B) -> A:
        return value
    return constant_fn

def curry2(func: Callable[[A, B], C]) -> Callable[[A], Callable[[B], C]]:
    """Curry a two-argument function.
    
    Transforms a function that takes two arguments into a function that takes
    one argument and returns a function that takes the second argument.
    
    Args:
        func: A binary function to curry
        
    Returns:
        A curried version of the function
        
    Examples:
        >>> def add(x: int, y: int) -> int:
        ...     return x + y
        >>> curried_add = curry2(add)
        >>> add_five = curried_add(5)
        >>> add_five(3)
        8
    """
    def curried_first(a: A) -> Callable[[B], C]:
        def curried_second(b: B) -> C:
            return func(a, b)
        return curried_second
    return curried_first

def flip(func: Callable[[A, B], C]) -> Callable[[B, A], C]:
    """Flip the order of arguments for a binary function.
    
    Args:
        func: A binary function
        
    Returns:
        A function with arguments in reverse order
        
    Examples:
        >>> def divide(x: int, y: int) -> float:
        ...     return x / y
        >>> flipped_divide = flip(divide)
        >>> divide(10, 2)
        5.0
        >>> flipped_divide(2, 10)
        5.0
    """
    def flipped(b: B, a: A) -> C:
        return func(a, b)
    return flipped
