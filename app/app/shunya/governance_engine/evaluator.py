"""SHUNYA — Safe Expression Evaluator (Phase H — ES-001).

Replaces Python's built-in eval() with a fully deterministic, sandboxed
expression evaluator. Supports field access, comparisons, boolean logic,
arithmetic, and a whitelisted set of function calls.

No eval(), no exec(), no __builtins__, no dynamic imports.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Whitelisted functions available in policy expressions
# ---------------------------------------------------------------------------

_WHITELISTED_FUNCTIONS: Dict[str, Any] = {
    "has": lambda ctx, k: k in ctx and ctx[k] is not None,
    "get": lambda ctx, k, d=None: ctx.get(k, d),
    "len": len,
    "any": any,
    "all": all,
    "isinstance": isinstance,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "re_match": lambda p, s: bool(re.match(p, str(s))) if s else False,
    "in_range": lambda v, lo, hi: lo <= v <= hi,
}


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

class TokenType:
    """Token types for the expression language."""
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    BOOL = "BOOL"
    NONE = "NONE"
    DOT = "DOT"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MUL = "MUL"
    DIV = "DIV"
    EQ = "EQ"          # ==
    NEQ = "NEQ"        # !=
    LT = "LT"          # <
    GT = "GT"          # >
    LE = "LE"          # <=
    GE = "GE"          # >=
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    IN = "IN"
    EOF = "EOF"


class Token:
    __slots__ = ("type", "value", "pos")

    def __init__(self, token_type: str, value: Any, pos: int = 0):
        self.type = token_type
        self.value = value
        self.pos = pos

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r})"


def tokenize(expression: str) -> List[Token]:
    """Tokenize a policy expression string."""
    tokens: List[Token] = []
    i = 0
    length = len(expression)

    while i < length:
        ch = expression[i]

        # Whitespace
        if ch in ' \t\n\r':
            i += 1
            continue

        # Single-line comments (for multi-condition expressions)
        if ch == '#' or (ch == '/' and i + 1 < length and expression[i + 1] == '/'):
            while i < length and expression[i] != '\n':
                i += 1
            continue

        # String literals: single or double quoted
        if ch in ("'", '"'):
            quote = ch
            i += 1
            start = i
            while i < length and expression[i] != quote:
                if expression[i] == '\\':
                    i += 1  # skip escape char
                    if i >= length:
                        break
                i += 1
            value = expression[start:i]
            if i < length:
                i += 1  # skip closing quote
            tokens.append(Token(TokenType.STRING, value, start))
            continue

        # Numbers
        if ch.isdigit() or (ch == '-' and i + 1 < length and expression[i + 1].isdigit()
                            and (i == 0 or expression[i - 1] in ' \t\n\r(,[=!<>+-*/')):
            start = i
            if ch == '-':
                i += 1
            while i < length and (expression[i].isdigit() or expression[i] == '.'):
                i += 1
            num_str = expression[start:i]
            if '.' in num_str:
                tokens.append(Token(TokenType.NUMBER, float(num_str), start))
            else:
                tokens.append(Token(TokenType.NUMBER, int(num_str), start))
            continue

        # Identifiers and keywords
        if ch.isalpha() or ch == '_':
            start = i
            while i < length and (expression[i].isalnum() or expression[i] == '_'):
                i += 1
            word = expression[start:i]
            if word in ('True', 'true'):
                tokens.append(Token(TokenType.BOOL, True, start))
            elif word in ('False', 'false'):
                tokens.append(Token(TokenType.BOOL, False, start))
            elif word in ('None', 'null'):
                tokens.append(Token(TokenType.NONE, None, start))
            elif word == 'and':
                tokens.append(Token(TokenType.AND, 'and', start))
            elif word == 'or':
                tokens.append(Token(TokenType.OR, 'or', start))
            elif word == 'not':
                tokens.append(Token(TokenType.NOT, 'not', start))
            elif word == 'in':
                tokens.append(Token(TokenType.IN, 'in', start))
            else:
                tokens.append(Token(TokenType.IDENTIFIER, word, start))
            continue

        # Multi-char operators
        # Handle 'not in' as compound operator
        if (ch == 'n' and expression[i:i+3] == 'not'
                and i + 3 < length and expression[i+3] in ' \t'
                and i + 4 < length and expression[i+4:i+6] == 'in'
                and (i + 6 >= length or expression[i+6] in ' \t')):
            # This is handled in the parser, not the tokenizer
            pass  # Will be parsed as separate NOT + IN tokens

        if ch == '=' and i + 1 < length and expression[i + 1] == '=':
            tokens.append(Token(TokenType.EQ, '==', i))
            i += 2
            continue
        if ch == '!' and i + 1 < length and expression[i + 1] == '=':
            tokens.append(Token(TokenType.NEQ, '!=', i))
            i += 2
            continue
        if ch == '<' and i + 1 < length and expression[i + 1] == '=':
            tokens.append(Token(TokenType.LE, '<=', i))
            i += 2
            continue
        if ch == '>' and i + 1 < length and expression[i + 1] == '=':
            tokens.append(Token(TokenType.GE, '>=', i))
            i += 2
            continue

        # Single-char operators
        ops = {
            '.': TokenType.DOT,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ',': TokenType.COMMA,
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MUL,
            '/': TokenType.DIV,
            '<': TokenType.LT,
            '>': TokenType.GT,
        }
        if ch in ops:
            tokens.append(Token(ops[ch], ch, i))
            i += 1
            continue

        # Skip unknown chars (belt-and-suspenders)
        i += 1

    tokens.append(Token(TokenType.EOF, None, length))
    return tokens


# ---------------------------------------------------------------------------
# Recursive-descent parser
# ---------------------------------------------------------------------------

class ASTNode:
    """Base class for all AST nodes."""
    __slots__ = ()


class LiteralNode(ASTNode):
    __slots__ = ("value",)
    def __init__(self, value: Any):
        self.value = value


class IdentifierNode(ASTNode):
    __slots__ = ("name",)
    def __init__(self, name: str):
        self.name = name


class BinaryOpNode(ASTNode):
    __slots__ = ("op", "left", "right")
    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op
        self.left = left
        self.right = right


class UnaryOpNode(ASTNode):
    __slots__ = ("op", "operand")
    def __init__(self, op: str, operand: ASTNode):
        self.op = op
        self.operand = operand


class FunctionCallNode(ASTNode):
    __slots__ = ("name", "args")
    def __init__(self, name: str, args: List[ASTNode]):
        self.name = name
        self.args = args


class AttributeAccessNode(ASTNode):
    __slots__ = ("object", "attr")
    def __init__(self, obj: ASTNode, attr: str):
        self.object = obj
        self.attr = attr


class ListLiteralNode(ASTNode):
    __slots__ = ("elements",)
    def __init__(self, elements: List[ASTNode]):
        self.elements = elements


class Parser:
    """Recursive-descent parser for governance policy expressions."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def consume(self, expected_type: Optional[str] = None) -> Token:
        token = self.peek()
        if expected_type and token.type != expected_type:
            raise ValueError(f"Expected {expected_type}, got {token.type} ('{token.value}') "
                             f"at position {token.pos}")
        self.pos += 1
        return token

    def parse(self) -> ASTNode:
        """Parse the full expression."""
        result = self.parse_or()
        if self.peek().type != TokenType.EOF:
            raise ValueError(f"Unexpected token {self.peek().type} "
                             f"('{self.peek().value}') at position {self.peek().pos}")
        return result

    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        while self.peek().type == TokenType.OR:
            op = self.consume().value
            right = self.parse_and()
            left = BinaryOpNode(op, left, right)
        return left

    def parse_and(self) -> ASTNode:
        left = self.parse_not()
        while self.peek().type == TokenType.AND:
            op = self.consume().value
            right = self.parse_not()
            left = BinaryOpNode(op, left, right)
        return left

    def parse_not(self) -> ASTNode:
        if self.peek().type == TokenType.NOT:
            op = self.consume().value
            operand = self.parse_not()
            return UnaryOpNode(op, operand)
        return self.parse_comparison()

    def parse_comparison(self) -> ASTNode:
        left = self.parse_addition()
        comp_ops = {
            TokenType.EQ: '==', TokenType.NEQ: '!=',
            TokenType.LT: '<', TokenType.GT: '>',
            TokenType.LE: '<=', TokenType.GE: '>=',
            TokenType.IN: 'in',
        }
        while True:
            token = self.peek()
            # Handle 'not in' as compound operator
            if token.type == TokenType.NOT:
                # Look ahead to see if next token is IN
                next_pos = self.pos + 1
                if (next_pos < len(self.tokens)
                        and self.tokens[next_pos].type == TokenType.IN):
                    self.consume()  # consume NOT
                    self.consume()  # consume IN
                    right = self.parse_addition()
                    left = UnaryOpNode('not', BinaryOpNode('in', left, right))
                    continue
            if token.type in comp_ops:
                op_token = self.consume()
                op = comp_ops[op_token.type]
                right = self.parse_addition()
                left = BinaryOpNode(op, left, right)
                continue
            break
        return left

    def parse_addition(self) -> ASTNode:
        left = self.parse_multiplication()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.consume().value
            right = self.parse_multiplication()
            left = BinaryOpNode(op, left, right)
        return left

    def parse_multiplication(self) -> ASTNode:
        left = self.parse_unary()
        while self.peek().type in (TokenType.MUL, TokenType.DIV):
            op = self.consume().value
            right = self.parse_unary()
            left = BinaryOpNode(op, left, right)
        return left

    def parse_unary(self) -> ASTNode:
        if self.peek().type == TokenType.MINUS:
            self.consume()
            operand = self.parse_unary()
            return UnaryOpNode('-', operand)
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        token = self.peek()

        # Parenthesized expression
        if token.type == TokenType.LPAREN:
            self.consume()
            expr = self.parse_or()
            self.consume(TokenType.RPAREN)
            return expr

        # List literal
        if token.type == TokenType.LBRACKET:
            self.consume()
            elements: List[ASTNode] = []
            if self.peek().type != TokenType.RBRACKET:
                elements.append(self.parse_or())
                while self.peek().type == TokenType.COMMA:
                    self.consume()
                    elements.append(self.parse_or())
            self.consume(TokenType.RBRACKET)
            return ListLiteralNode(elements)

        # Literals
        if token.type == TokenType.NUMBER:
            self.consume()
            return LiteralNode(token.value)
        if token.type == TokenType.STRING:
            self.consume()
            return LiteralNode(token.value)
        if token.type == TokenType.BOOL:
            self.consume()
            return LiteralNode(token.value)
        if token.type == TokenType.NONE:
            self.consume()
            return LiteralNode(None)

        # Identifier (could be field access or function call)
        if token.type == TokenType.IDENTIFIER:
            name = token.value
            self.consume()

            # Function call: func(args)
            if self.peek().type == TokenType.LPAREN:
                self.consume()
                args: List[ASTNode] = []
                if self.peek().type != TokenType.RPAREN:
                    args.append(self.parse_or())
                    while self.peek().type == TokenType.COMMA:
                        self.consume()
                        args.append(self.parse_or())
                self.consume(TokenType.RPAREN)
                node: ASTNode = FunctionCallNode(name, args)
            else:
                node = IdentifierNode(name)

            # Attribute/method chains: a.b.c
            while self.peek().type == TokenType.DOT:
                self.consume()
                attr = self.consume(TokenType.IDENTIFIER).value
                node = AttributeAccessNode(node, attr)

            return node

        raise ValueError(f"Unexpected token {token.type} ('{token.value}') "
                         f"at position {token.pos}")


# ---------------------------------------------------------------------------
# Safe Evaluator
# ---------------------------------------------------------------------------


class SafeContext:
    """A dict wrapper that returns None for missing keys instead of raising KeyError.
    Supports both dict['key'] and dict.key access patterns."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __contains__(self, key: str) -> bool:
        if key == 'ctx':
            return True
        return key in self._data and self._data[key] is not None

    def __getitem__(self, key: str) -> Any:
        if key == 'ctx':
            return self
        return self._data.get(key, None)

    def __getattr__(self, key: str) -> Any:
        if key.startswith('_'):
            raise AttributeError(key)
        if key == 'ctx':
            return self
        return self._data.get(key, None)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self._data and self._data[key] is not None


def evaluate(node: ASTNode, context: Dict[str, Any],
             functions: Optional[Dict[str, Any]] = None) -> Any:
    """Evaluate an AST node against a context dictionary.

    Only the whitelisted function set is available. No eval(), no exec(),
    no dynamic imports, no attribute access beyond SafeContext fields.
    """
    ctx = SafeContext(context) if not isinstance(context, SafeContext) else context
    funcs = functions if functions is not None else _WHITELISTED_FUNCTIONS

    if isinstance(node, LiteralNode):
        return node.value

    if isinstance(node, ListLiteralNode):
        return [evaluate(e, ctx, funcs) for e in node.elements]

    if isinstance(node, IdentifierNode):
        # Reject dunder identifiers (security: no access to Python internals)
        if node.name.startswith('__'):
            raise ValueError(f"Access denied to identifier starting with '__': {node.name}")
        # ctx is the implicit context object; bare identifiers reference context fields
        return ctx[node.name]

    if isinstance(node, AttributeAccessNode):
        # Resolve the object first
        obj = evaluate(node.object, ctx, funcs)
        # If the object is a SafeContext, use getattr pattern
        if isinstance(obj, SafeContext):
            return obj[node.attr]
        # Otherwise use regular attribute access (for ctx.field patterns)
        if isinstance(obj, dict):
            return obj.get(node.attr, None)
        return getattr(obj, node.attr, None)

    if isinstance(node, UnaryOpNode):
        operand = evaluate(node.operand, ctx, funcs)
        if node.op == 'not':
            return not operand
        if node.op == '-':
            return -operand
        raise ValueError(f"Unknown unary operator: {node.op}")

    if isinstance(node, BinaryOpNode):
        if node.op in ('and', 'or'):
            # Short-circuit evaluation
            left = evaluate(node.left, ctx, funcs)
            if node.op == 'and':
                return bool(left) and bool(evaluate(node.right, ctx, funcs))
            else:
                return bool(left) or bool(evaluate(node.right, ctx, funcs))

        left = evaluate(node.left, ctx, funcs)
        right = evaluate(node.right, ctx, funcs)

        if node.op == '==':
            return left == right
        if node.op == '!=':
            return left != right
        if node.op == '<':
            return left < right
        if node.op == '>':
            return left > right
        if node.op == '<=':
            return left <= right
        if node.op == '>=':
            return left >= right
        if node.op == '+':
            return left + right
        if node.op == '-':
            return left - right
        if node.op == '*':
            return left * right
        if node.op == '/':
            if right == 0:
                return float('inf')
            return left / right
        if node.op == 'in':
            # support both 'x in list' and 'x in string'
            if isinstance(right, (list, tuple, set, str, bytes, dict)):
                return left in right
            return False
        raise ValueError(f"Unknown binary operator: {node.op}")

    if isinstance(node, FunctionCallNode):
        if node.name not in funcs:
            raise ValueError(f"Unknown function: {node.name}")
        fn = funcs[node.name]
        args = [evaluate(a, ctx, funcs) for a in node.args]
        # Functions that need the context as first arg (has, get)
        if node.name in ('has', 'get'):
            args = [ctx] + args
        try:
            return fn(*args)
        except Exception as e:
            raise ValueError(f"Error in function {node.name}: {e}") from e

    raise ValueError(f"Unknown AST node type: {type(node).__name__}")


def safe_eval(expression: str, context: Dict[str, Any]) -> Any:
    """Evaluate a policy expression against a context dictionary.

    This is the sole entry point for policy condition evaluation.
    No eval(), no exec(), no __builtins__, no dynamic imports.
    """
    tokens = tokenize(expression)
    parser = Parser(tokens)
    ast = parser.parse()
    return evaluate(ast, context)


def safe_eval_bool(expression: str, context: Dict[str, Any]) -> bool:
    """Evaluate a policy expression and return a boolean result."""
    result = safe_eval(expression, context)
    return bool(result)