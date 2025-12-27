"""Manual expression parser for --where clauses.

This module implements a secure expression parser that does NOT use eval().
It tokenizes, parses into AST, and evaluates filter expressions safely.

Grammar:
    expr     := or_expr
    or_expr  := and_expr ('or' and_expr)*
    and_expr := cmp_expr ('and' cmp_expr)*
    cmp_expr := term (('>' | '<' | '>=' | '<=' | '==' | '!=') term)?
    term     := 'not' term | atom
    atom     := NUMBER | STRING | attribute | method_call | group_call | '(' expr ')'
    
    attribute    := 'line' '.' IDENT
    method_call  := 'line' '.' IDENT '(' STRING ')'
    group_call   := 'group' '(' STRING ')'
"""

from dataclasses import dataclass
from typing import Callable
from result import Result, Ok, Err
import re

from bsce_mgrep.domain.types import MatchContext, FilterResult, FilterExpression


# AST Node types
@dataclass(frozen=True, slots=True)
class Literal:
    """Literal value (int, str, bool)."""
    value: int | str | bool


@dataclass(frozen=True, slots=True)
class Attribute:
    """Object attribute access (e.g., line.length)."""
    object: str  # e.g., "line"
    attr: str    # e.g., "length"


@dataclass(frozen=True, slots=True)
class MethodCall:
    """Method call (e.g., line.contains("text"))."""
    object: str      # e.g., "line"
    method: str      # e.g., "contains"
    args: list[str]  # e.g., ["text"]


@dataclass(frozen=True, slots=True)
class GroupAccess:
    """Regex group access (e.g., group("code"))."""
    name: str


@dataclass(frozen=True, slots=True)
class BinaryOp:
    """Binary operation (comparison or logical)."""
    left: 'ASTNode'
    op: str  # '>', '<', '>=', '<=', '==', '!=', 'and', 'or'
    right: 'ASTNode'


@dataclass(frozen=True, slots=True)
class UnaryOp:
    """Unary operation (not)."""
    op: str  # 'not'
    operand: 'ASTNode'


type ASTNode = Literal | Attribute | MethodCall | GroupAccess | BinaryOp | UnaryOp


# Token types
TOKEN_PATTERNS = [
    ('NUMBER', r'-?\d+'),
    ('STRING', r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\''),
    ('GTE', r'>='),
    ('LTE', r'<='),
    ('EQ', r'=='),
    ('NEQ', r'!='),
    ('GT', r'>'),
    ('LT', r'<'),
    ('AND', r'\band\b'),
    ('OR', r'\bor\b'),
    ('NOT', r'\bnot\b'),
    ('IDENT', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('DOT', r'\.'),
    ('COMMA', r','),
    ('WHITESPACE', r'\s+'),
]

TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_PATTERNS)
TOKEN_RE = re.compile(TOKEN_REGEX)


@dataclass(frozen=True, slots=True)
class Token:
    """A lexical token."""
    type: str
    value: str
    position: int


def tokenize(expression: str) -> Result[list[Token], str]:
    """Tokenize an expression into a list of tokens.
    
    Args:
        expression: Filter expression string
        
    Returns:
        Result containing list of tokens or error message
        
    Examples:
        >>> result = tokenize("line.length > 120")
        >>> len(result.ok_value)
        5
    """
    tokens: list[Token] = []
    position = 0
    
    for match in TOKEN_RE.finditer(expression):
        token_type = match.lastgroup
        token_value = match.group()
        
        if token_type == 'WHITESPACE':
            # Skip whitespace
            continue
        
        if token_type is None:
            return Err(f"Invalid character at position {match.start()}: {token_value}")
        
        tokens.append(Token(type=token_type, value=token_value, position=match.start()))
        position = match.end()
    
    if position < len(expression):
        return Err(f"Unexpected character at position {position}: {expression[position]}")
    
    return Ok(tokens)


class Parser:
    """Recursive descent parser for filter expressions."""
    
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.position = 0
    
    def current_token(self) -> Token | None:
        """Get current token without consuming."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None
    
    def consume(self, expected_type: str | None = None) -> Token:
        """Consume and return current token."""
        token = self.current_token()
        if token is None:
            raise ValueError("Unexpected end of expression")
        
        if expected_type and token.type != expected_type:
            raise ValueError(f"Expected {expected_type}, got {token.type} at position {token.position}")
        
        self.position += 1
        return token
    
    def parse(self) -> Result[ASTNode, str]:
        """Parse tokens into AST."""
        try:
            ast = self.parse_or_expr()
            if self.current_token() is not None:
                return Err(f"Unexpected token after expression: {self.current_token().value}")
            return Ok(ast)
        except ValueError as e:
            return Err(str(e))
        except Exception as e:
            return Err(f"Parse error: {e}")
    
    def parse_or_expr(self) -> ASTNode:
        """Parse: or_expr := and_expr ('or' and_expr)*"""
        left = self.parse_and_expr()
        
        while self.current_token() and self.current_token().type == 'OR':
            self.consume('OR')
            right = self.parse_and_expr()
            left = BinaryOp(left=left, op='or', right=right)
        
        return left
    
    def parse_and_expr(self) -> ASTNode:
        """Parse: and_expr := cmp_expr ('and' cmp_expr)*"""
        left = self.parse_cmp_expr()
        
        while self.current_token() and self.current_token().type == 'AND':
            self.consume('AND')
            right = self.parse_cmp_expr()
            left = BinaryOp(left=left, op='and', right=right)
        
        return left
    
    def parse_cmp_expr(self) -> ASTNode:
        """Parse: cmp_expr := term (('>' | '<' | '>=' | '<=' | '==' | '!=') term)?"""
        left = self.parse_term()
        
        token = self.current_token()
        if token and token.type in ('GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ'):
            op_token = self.consume()
            right = self.parse_term()
            
            # Map token type to operator string
            op_map = {
                'GT': '>', 'LT': '<', 'GTE': '>=',
                'LTE': '<=', 'EQ': '==', 'NEQ': '!='
            }
            return BinaryOp(left=left, op=op_map[op_token.type], right=right)
        
        return left
    
    def parse_term(self) -> ASTNode:
        """Parse: term := 'not' term | atom"""
        token = self.current_token()
        
        if token and token.type == 'NOT':
            self.consume('NOT')
            operand = self.parse_term()
            return UnaryOp(op='not', operand=operand)
        
        return self.parse_atom()
    
    def parse_atom(self) -> ASTNode:
        """Parse: atom := NUMBER | STRING | attribute | method_call | group_call | '(' expr ')'"""
        token = self.current_token()
        
        if not token:
            raise ValueError("Unexpected end of expression")
        
        # Parenthesized expression
        if token.type == 'LPAREN':
            self.consume('LPAREN')
            expr = self.parse_or_expr()
            self.consume('RPAREN')
            return expr
        
        # Number literal
        if token.type == 'NUMBER':
            self.consume('NUMBER')
            return Literal(value=int(token.value))
        
        # String literal
        if token.type == 'STRING':
            self.consume('STRING')
            # Remove quotes and handle escapes
            string_value = token.value[1:-1]  # Remove surrounding quotes
            string_value = string_value.replace(r'\"', '"').replace(r"\'", "'")
            return Literal(value=string_value)
        
        # Identifier (could be attribute access, method call, or group call)
        if token.type == 'IDENT':
            ident = self.consume('IDENT').value
            
            # Check for dot notation (line.attr or line.method(...))
            if self.current_token() and self.current_token().type == 'DOT':
                self.consume('DOT')
                member = self.consume('IDENT').value
                
                # Check if it's a method call
                if self.current_token() and self.current_token().type == 'LPAREN':
                    self.consume('LPAREN')
                    args = []
                    
                    # Parse method arguments
                    if self.current_token() and self.current_token().type == 'STRING':
                        arg_token = self.consume('STRING')
                        arg_value = arg_token.value[1:-1]
                        arg_value = arg_value.replace(r'\"', '"').replace(r"\'", "'")
                        args.append(arg_value)
                    
                    self.consume('RPAREN')
                    return MethodCall(object=ident, method=member, args=args)
                else:
                    # Attribute access
                    return Attribute(object=ident, attr=member)
            
            # Check for function call (group(...))
            if self.current_token() and self.current_token().type == 'LPAREN':
                self.consume('LPAREN')
                
                if ident == 'group':
                    # Parse group name
                    if self.current_token() and self.current_token().type == 'STRING':
                        name_token = self.consume('STRING')
                        name_value = name_token.value[1:-1]
                        name_value = name_value.replace(r'\"', '"').replace(r"\'", "'")
                        self.consume('RPAREN')
                        return GroupAccess(name=name_value)
                    else:
                        raise ValueError(f"group() requires string argument")
                else:
                    raise ValueError(f"Unknown function: {ident}")
            
            raise ValueError(f"Unexpected identifier: {ident}")
        
        raise ValueError(f"Unexpected token: {token.type}")


def parse_where_expression(expr: FilterExpression) -> Result[ASTNode, str]:
    """Parse a where expression into an AST.
    
    Args:
        expr: Filter expression string
        
    Returns:
        Result containing AST or error message
        
    Examples:
        >>> result = parse_where_expression("line.length > 120")
        >>> isinstance(result, Ok)
        True
    """
    # Tokenize
    tokens_result = tokenize(expr)
    if isinstance(tokens_result, Err):
        return tokens_result
    
    tokens = tokens_result.ok_value
    
    # Parse
    parser = Parser(tokens)
    return parser.parse()


def evaluate_where(ast: ASTNode, context: MatchContext) -> FilterResult:
    """Evaluate AST with match context.
    
    Args:
        ast: Abstract syntax tree to evaluate
        context: Match context with line and groups
        
    Returns:
        Result containing boolean or error message
        
    Examples:
        >>> from bsce_mgrep.domain.types import Line
        >>> line = Line(1, "test")
        >>> ctx = MatchContext(line=line, groups={})
        >>> ast = Literal(value=True)
        >>> result = evaluate_where(ast, ctx)
        >>> result.ok_value
        True
    """
    try:
        result = _evaluate_node(ast, context)
        return Ok(result)
    except Exception as e:
        return Err(f"Evaluation error: {e}")


def _evaluate_node(node: ASTNode, context: MatchContext) -> bool | int | str:
    """Recursively evaluate AST node."""
    match node:
        case Literal(value):
            return value
        
        case Attribute(obj, attr):
            if obj == 'line':
                line = context.line
                match attr:
                    case 'length':
                        return line.length
                    case 'number':
                        return line.number
                    case 'content':
                        return line.content
                    case _:
                        raise ValueError(f"Unknown line attribute: {attr}")
            else:
                raise ValueError(f"Unknown object: {obj}")
        
        case MethodCall(obj, method, args):
            if obj == 'line':
                line = context.line
                match method:
                    case 'contains':
                        if len(args) != 1:
                            raise ValueError("contains() requires exactly 1 argument")
                        return line.contains(args[0])
                    case 'startswith':
                        if len(args) != 1:
                            raise ValueError("startswith() requires exactly 1 argument")
                        return line.startswith(args[0])
                    case 'endswith':
                        if len(args) != 1:
                            raise ValueError("endswith() requires exactly 1 argument")
                        return line.endswith(args[0])
                    case _:
                        raise ValueError(f"Unknown line method: {method}")
            else:
                raise ValueError(f"Unknown object: {obj}")
        
        case GroupAccess(name):
            if name in context.groups:
                return context.groups[name]
            else:
                raise ValueError(f"Regex group not found: {name}")
        
        case BinaryOp(left, op, right):
            left_val = _evaluate_node(left, context)
            right_val = _evaluate_node(right, context)
            
            match op:
                case '>':
                    return left_val > right_val
                case '<':
                    return left_val < right_val
                case '>=':
                    return left_val >= right_val
                case '<=':
                    return left_val <= right_val
                case '==':
                    return left_val == right_val
                case '!=':
                    return left_val != right_val
                case 'and':
                    return bool(left_val) and bool(right_val)
                case 'or':
                    return bool(left_val) or bool(right_val)
                case _:
                    raise ValueError(f"Unknown binary operator: {op}")
        
        case UnaryOp(op, operand):
            operand_val = _evaluate_node(operand, context)
            match op:
                case 'not':
                    return not bool(operand_val)
                case _:
                    raise ValueError(f"Unknown unary operator: {op}")
        
        case _:
            raise ValueError(f"Unknown AST node type: {type(node)}")
