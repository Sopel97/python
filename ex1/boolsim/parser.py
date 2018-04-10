from enum import Enum
from .expression import *

class OpenParen:
    precedence = -1

    def __init__(self, c):
        self.c = c

    def __str__(self):
        return self.c

    def __repr__(self):
        return repr(self.c)


class CloseParen:
    precedence = -1

    def __init__(self, c):
        self.c = c

    def __str__(self):
        return self.c

    def __repr__(self):
        return repr(self.c)


class InvalidExpression(Exception):
    pass

unary_operators = [
    ('!', Negation),
    ('~', Negation)
]


binary_operators = [
    ('||', Disjunction),
    ('|', Disjunction),
    ('^', ExclusiveDisjunction),
    ('&&', Conjunction),
    ('&', Conjunction),
    ('=>', Implication),
    ('>', Implication),
    ('<=>', Equivalency),
    ('=', Equivalency)
]


class TokenType(Enum):
    CONSTANT = 0
    SYMBOL = 1
    PAREN_OPEN = 2
    PAREN_CLOSE = 3
    UNARY_OP = 4
    BINARY_OP = 5


class Token:
    def __init__(self, type, token):
        self.type = type
        self.token = token

    def __str__(self):
        return '(' + str(self.type) + ', ' + str(self.token) + ')'

    def __repr__(self):
        return '(' + repr(self.type) + ', ' + repr(self.token) + ')'


def try_read_constant(expr_str, pos):
    if expr_str.startswith('0', pos):
        return Constant(False), 1
    elif expr_str.startswith('1', pos):
        return Constant(True), 1
    elif expr_str.startswith('False', pos):
        return Constant(False), 5
    elif expr_str.startswith('True', pos):
        return Constant(True), 4
    else:
        return None, 0


def try_read_unary_operator(expr_str, pos):
    for s, o in unary_operators:
        if expr_str.startswith(s, pos):
            return o, len(s)

    return None, 0


def try_read_binary_operator(expr_str, pos):
    for s, o in binary_operators:
        if expr_str.startswith(s, pos):
            return o, len(s)

    return None, 0


def try_read(expr_str, pos, to_read):
    if expr_str.startswith(to_read, pos):
        return to_read, len(to_read)

    return None, 0


def try_read_symbol(expr_str, pos):
    start = pos
    if pos < len(expr_str) and expr_str[pos].isalpha():
        pos += 1
    while pos < len(expr_str) and (expr_str[pos].isalpha() or expr_str[pos].isdigit()):
        pos += 1

    if pos > start:
        return Symbol(expr_str[start:pos]), (pos - start)
    else:
        return None, 0


def tokenize(expr_str):
    tokens = []

    current_pos = 0
    while current_pos < len(expr_str):
        token, length = try_read_constant(expr_str, current_pos)
        if token:
            current_pos += length
            tokens += [Token(TokenType.CONSTANT, token)]
            continue

        token, length = try_read_unary_operator(expr_str, current_pos)
        if token:
            current_pos += length
            tokens += [Token(TokenType.UNARY_OP, token)]
            continue

        token, length = try_read_binary_operator(expr_str, current_pos)
        if token:
            current_pos += length
            tokens += [Token(TokenType.BINARY_OP, token)]
            continue

        token, length = try_read_symbol(expr_str, current_pos)
        if token:
            current_pos += length
            tokens += [Token(TokenType.SYMBOL, token)]
            continue

        token, length = try_read(expr_str, current_pos, '(')
        if token:
            current_pos += length
            tokens += [Token(TokenType.PAREN_OPEN, OpenParen(token))]
            continue

        token, length = try_read(expr_str, current_pos, ')')
        if token:
            current_pos += length
            tokens += [Token(TokenType.PAREN_CLOSE, CloseParen(token))]
            continue

        raise InvalidExpression()

    return tokens

def infix_to_postfix(tokens):
    postfix = []
    operator_stack = []

    virtual_operand_count = 0

    def pop_operator():
        nonlocal virtual_operand_count
        nonlocal operator_stack

        if not operator_stack:
            raise InvalidExpression()

        op = operator_stack.pop()

        if op.type == TokenType.BINARY_OP:
            if virtual_operand_count < 1:
                raise InvalidExpression()
            virtual_operand_count -= 1 # take 2, make 1

        return op


    for token in tokens:
        if token.type == TokenType.PAREN_OPEN or token.type == TokenType.UNARY_OP:
            operator_stack += [token]
            continue

        if token.type == TokenType.BINARY_OP:
            while operator_stack and operator_stack[-1].token.precedence >= token.token.precedence:
                postfix += [pop_operator()]
            operator_stack += [token]

            continue

        if token.type == TokenType.PAREN_CLOSE:
            finished_on_paren_open = False
            while operator_stack:
                if operator_stack[-1].type == TokenType.PAREN_OPEN:
                    operator_stack.pop()
                    finished_on_paren_open = True
                    break

                postfix += [pop_operator()]

            if not finished_on_paren_open:
                raise InvalidExpression()

            continue

        if token.type == TokenType.SYMBOL or token.type == TokenType.CONSTANT:
            virtual_operand_count += 1
            postfix += [token]

    while operator_stack:
        op = pop_operator()

        if op.type == TokenType.PAREN_OPEN:
            raise InvalidExpression()

        postfix += [op]

    if virtual_operand_count != 1:
        raise InvalidExpression()

    return postfix

def parse_expression(expr_str):
    tokens = infix_to_postfix(tokenize(expr_str))

    operand_stack = []

    for token in tokens:
        if token.type in [TokenType.SYMBOL, TokenType.CONSTANT]:
            operand_stack += [token.token]
            continue

        if token.type == TokenType.UNARY_OP:
            if len(operand_stack) < 1:
                raise InvalidExpression()

            arg = operand_stack.pop()
            operand_stack += [token.token(arg)]
            continue

        if token.type == TokenType.BINARY_OP:
            if len(operand_stack) < 2:
                raise InvalidExpression()

            rhs = operand_stack.pop()
            lhs = operand_stack.pop()
            operand_stack += [token.token(lhs, rhs)]

    if len(operand_stack) != 1:
        raise InvalidExpression()

    return operand_stack[0]