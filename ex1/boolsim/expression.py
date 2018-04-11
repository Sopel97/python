"""Expression components and operations on them.

This module provides definitions for all expression components such as
constants, symbols (variables) and operators (as an expression with
one or more children).
Every class that is an expression in itself provides
basic methods for recursive inspection, substitution and pattern
application (for example for reduction of expressions).

There exist some module-level functions to help with more general
operations that can be perfomed on expressions, such as extraction
of used symbols (variables), evaluation, and short-circuiting
equality/truthness checks between expressions.
"""

from .util import *

import textwrap

def gather_symbols_from_expr(expr):
    """Gather names of unique symbols in the expression.

    Searches the expression recusively and remembers names of all
    unique symbols encountered.

    Args:
        expr (Expression): The expression to gather symbols from.

    Returns:
        list of str: A list of names.
    """
    return list({e.name for e in expr if type(e) == Symbol})

def count_distinct_symbols(expr):
    """Count how many distinct symbols are in the expression.

    Effectively returns the length of a list returned by
    gather_symbols_from_expr.

    Args:
        expr (Expression): The expression to count symbols in.

    Returns:
        int: Number of distinctly named symbols.
    """
    return len(gather_symbols_from_expr(expr))

def evaluates_to(expr, boolean):
    """Check if the given expression evaluates to a given boolean.

    Checks whether the given expression is equal to a given boolean for
    all possible inputs (all possible combinations of symbols used by the
    expression). It short-circuits, so it reports failure as soon as
    possible.

    Args:
        expr (Expression): The expression to evaluate.
        boolean (bool): The value to check against.

    Returns:
        bool: True on success, False on failure
    """
    ids_to_symbols = gather_symbols_from_expr(expr)
    dim = len(ids_to_symbols)
    for i in range(pow2(dim)):
        if expr.evaluate(symbol_dict_from_index(ids_to_symbols, BoolVector(dim, i))) != boolean:
            return False

    return True

def symbol_dict_from_index(ids_to_symbols, index):
    """Convert a list of unnamed values to named values.

    Given a bitfield it interprets the subsequent bits (starting from LSB)
    as values to use for variables with names repectively from ids_to_symbols
    list and forms a dictionary for them.
    At most len(ids_to_symbols) variables is assigned.

    Args:
        ids_to_symbols (list of str): Subsequent variable names.
        index (BoolVector): Bitfield storing values for every variable.

    Returns:
        dict of (str, bool): Variable names with values assigned to them.
    """
    return {ids_to_symbols[i] : bool(index[i]) for i in range(len(ids_to_symbols))}

def evaluate_all(expr, ids_to_symbols):
    """Evaluate given expression for all possible inputs.

    Evaluates the given expression for each possible input, with the order
    of variables as in ids_to_symbols.

    Args:
        expr (Expression): Expression to evaluate.
        ids_to_symbols (list of str): Order of input variables by name.

    Returns:
        list of bool: All 2^n (where n = len(ids_to_symbols)) evaluations of the
            expression in increasing order of input (000, 001, 010, ...)
    """
    dim = len(ids_to_symbols)
    return [expr.evaluate(symbol_dict_from_index(ids_to_symbols, BoolVector(dim, i))) for i in range(pow2(dim))]

def is_true_by_evaluation(expr):
    """Check if the expression is always True.

    Checks if the given expression evaluates to True for all possible
    inputs. Uses evaluation.

    Args:
        expr (Expression): Expression to evaluate.

    Returns:
        bool: True if the expression is always True, false otherwise.
    """
    return evaluates_to(expr, True)

def is_false_by_evaluation(expr):
    """Check if the expression is always False.

    Checks if the given expression evaluates to False for all possible
    inputs. Uses evaluation.

    Args:
        expr (Expression): Expression to evaluate.

    Returns:
        bool: True if the expression is always False, false otherwise.
    """
    return evaluates_to(expr, False)

def are_equal_by_evaluation(lhs, rhs):
    """Check if given expressions are always equal.

    Checks if the given expressions are equal for all possible
    inputs. Ie. lhs <=> rhs is a tautology.
    Uses evaluation.

    Args:
        lhs (Expression): The left hand side expression.
        rhs (Expression): The right hand side expression.

    Returns:
        bool: True if the expressions are always equal, false otherwise.
    """
    expr = Equivalency(lhs, rhs)
    return is_true_by_evaluation(expr)

def are_opposite_by_evaluation(lhs, rhs):
    """Check if given expressions are never equal.

    Checks if the given expressions are different for all possible
    inputs. Ie. lhs <=> rhs is never True.
    Uses evaluation.

    Args:
        lhs (Expression): The left hand side expression.
        rhs (Expression): The right hand side expression.

    Returns:
        bool: True if the expressions are never equal, false otherwise.
    """
    expr = Equivalency(lhs, rhs)
    return is_false_by_evaluation(expr)

def add_if_no_conflict(d, key, value):
    """Try add value to a dictionary disallowing collisions.

    Tries to add a given (key, value) pair into a dictionary while
    ensuring that the already existing value won't change.
    Requires the value to be an expression, and equality is checked
    by evaluation of both sides.
    If the value would change the already existing value under given key
    to a different one then the dictionary remains unchanged.

    Args:
        d (dict): Dictionary to alter.
        key: The key to insert under.
        value (Expression): The expression to try insert.

    Returns:
        bool: True if the value was inserted or equal to the previous one,
            False otherwise
    """
    if key in d:
        # The check by truth tables is necessary, because we don't
        # permute expressions on leaves of simplifying rules.
        # The expression tree equality check is an optimistic heuristic.
        return d[key] == value or are_equal_by_evaluation(d[key], value)

    d[key] = value
    return True



class Expression:
    """Base class for all expression types.

    Each class that represents an Expression HAS TO be immutable.
    Allows for use as a persistent data structure.

    Represents a base for all types that should have expression semantics.
    For example values, operators.
    Defines manipulation methods common for each expression.
    """

    def get_paths_to_some_matches(self, pattern):
        """Gather some paths to nodes that match against pattern.

        For each node of the expression recursively gathers paths
        (path is a (list, dict) pair consisting of a list of nodes
        in the expression tree forming the path to the node that matched
        against pattern and a dictionary with captures made during the match).
        Only one succesful match is allowed per expression node.

        Args:
            pattern (Expression): Expression that serves as a pattern for matching.
                Symbols in the pattern can capture subtrees of the expression.

        Returns:
            list of (list, dict): Paths to nodes with succesful matching as well
                as respective captures made during matching.
        """
        all_paths = []
        self.gather_paths_to_some_matches(pattern, all_paths, [])
        return all_paths

    def get_paths_to_all_matches(self, pattern):
        """Gather all paths to nodes that match against pattern.

        This method works the same way as get_paths_to_some_matches, but
        it allows more successful matches from a single node to be
        reported.
        """
        all_paths = []
        self.gather_paths_to_all_matches(pattern, all_paths, [])
        return all_paths

    def apply_pattern_recursively_to_some(self, to_match, to_apply):
        """Form new expressions with given substitutes.

        Finds nodes that match to_match pattern and changes them
        to expression of form to_apply with respective captures made
        during matching.
        Only one match is allowed per node.
        Every substitution results in a separate expression.
        Ie. Any resulting expression is exactly one substitution away from
        the starting one.

        Args:
            to_match (Expression): Expression working as a pattern for matching nodes.
            to_apply (Expression): Expression to substitute previously made captures into.

        Returns:
            list of Expression: New expressions with appropriate substitutions made.
        """
        resulting_expressions = set()

        paths = self.get_paths_to_some_matches(to_match)
        for path in paths:
            resulting_expressions.add(self.apply_pattern_after_path(to_match, to_apply, path))

        return resulting_expressions

    def apply_pattern_recursively_to_all(self, to_match, to_apply):
        """Form new expressions with given substitutes.

        This method works the same as apply_pattern_recursively_to_some,
        but it allows multiple matches per node.
        """
        resulting_expressions = set()

        paths = self.get_paths_to_all_matches(to_match)
        for path in paths:
            resulting_expressions.add(self.apply_pattern_after_path(to_match, to_apply, path))

        return resulting_expressions

    def try_simplify_by_evaluation(self, lut):
        """Try simplify the expression by evaluating subtrees.

        Recursively tries to simplify the expression by evaluating children
        and applying rules specific to the type of the subtree (operator).
        Tries to use a lookup table of already simplified expressions with
        few variables first.

        Args:
            lut: A callable that receives the expression and returns the same
                expression or the equivalent simplest possible.

        Returns:
            Expression: Either a newly formed, simplified expression, an
                expression from lookup table, or self if nothing can be done.
        """
        simplified = lut(self)
        if not simplified is self:
            return simplified

        return self.try_simplify_by_children_evaluation(lut)

    def __repr__(self):
        """Stringify into a tree form.

        Converts the expression into a flattened tree, where children of
        each expression node are indented. Also shows complexity of each node.

        Returns:
            str: Representaton
        """
        indentation = '    '
        return ''.join(
            [
                'Type: {0}; Complexity: {1}; Children:\n'.format(self.__class__.__name__, self.complexity),
                textwrap.indent('\n'.join(repr(e) for e in self.children()), indentation)
            ]
        )

    def children(self):
        """Retrieve all children of the node.

        Returns all children stored by the expression node.
        Base expression doesn't have any children.

        Returns:
            list: All children expressions
        """
        return []

class Constant(Expression):
    """A constant boolean expression.

    Represents either True or False.
    """

    self_complexity = -1
    """Complexity the node adds to the expression."""

    _instances = dict()

    def __new__(cls, value):
        if value not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[value] = instance
        return cls._instances[value]

    def __init__(self, value):
        """Initialize to a given value.

        Sets the value and computes overall complexity and hash of
        the whole expression.

        Args:
            value (bool): Value to set the constant to.
        """
        if self._initialized:
            return
        self._initialized = True

        self._value = value
        self._complexity = self.__compute_complexity()
        self._hash = self.__compute_hash()

    def __iter__(self):
        yield self

    @property
    def value(self):
        """The value stored in the constant."""
        return self._value

    @property
    def complexity(self):
        """The complexity of the whole expression."""
        return self._complexity

    def evaluate(self, variables):
        """Return boolean value of this constant."""
        return self._value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return 'Constant: {0}'.format(self.value)

    def to_string(self, parent):
        """Stringifies with less parentheses.

        Similar to __str__, but allows for omitting unneeded parentheses.

        Args:
            parent (class): The class of the parent of this expression node.

        Returns:
            str: __str__
        """
        return str(self.value)

    def __eq__(self, other):
        return type(other) == Constant and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def try_match_once(self, pattern, captures):
        """Try match the node with the given pattern.

        Tries to match the node with expression given in pattern.
        Updates captures if pattern is a symbol.
        Can modify captures even on failure.
        Does at most one match.

        Args:
            pattern (Expression): Expression to try match against.
            captures (dict of (str, Expression)): captures from previous
                matches of the same pattern.

        Returns:
            bool: True if the match was successful, False otherwise.
        """
        if type(pattern) is Symbol:
            return add_if_no_conflict(captures, pattern.name, self)
        elif type(pattern) is Constant:
            return self.value == pattern.value
        else:
            return False

    def try_match_all(self, pattern, prev_captures):
        """Try match the node with the given pattern.

        Similar as try_match_ones, but is made in a form of a generator that
        can report multiple matches per node.

        prev_captures is never modified.

        Args:
            pattern (Expression): Expression to try match against.
            prev_captures (dict of (str, Expression)): captures from previous
                matches of the same pattern.

        Yields:
            (bool, (dict of (str, Expression)): A boolean indicating whether
                the match was successful and a copy of captures made during
                the matching.

        """
        if type(pattern) is Symbol:
            captures = prev_captures.copy()
            yield (add_if_no_conflict(captures, pattern.name, self), captures)
        elif type(pattern) is Constant:
            captures = prev_captures.copy()
            yield (self.value == pattern.value, captures)
        else:
            yield (False, prev_captures)

    def apply_pattern_after_path(self, to_match, to_apply, path_captures):
        """Apply pattern after path with captures.

        Traverses the expression according to the path and at the end
        makes a substitution forming a new expression (unchanged parts
        are reused due to immutability).

        Args:
            to_match (Expression): Expression to match. Currently unused.
            to_apply (Expression): Expression to substitute into at the end.
            path_captures ((list of Expression, dict of (str, Expression)) pair):
                path to the matching node and captures to substitute into it.

        Returns:
            A new expression after substitution.
        """
        captures = path_captures[1]
        return to_apply.substitute(captures)

    def gather_paths_to_some_matches(self, pattern, all_paths, current_path):
        """Gather paths and captures to matching nodes.

        See get_paths_to_some_matches.

        Additional paths that are formed are appended to all_paths.
        Maximum of one path per node.

        Args:
            pattern (Expression): Expression to match against.
            all_paths (list of list of Expression): Already saved paths.
            current_path (list of Expression): Path to the current node.
        """
        captures = dict()
        if self.try_match_once(pattern, captures):
            current_path += [self]
            all_paths += [(current_path.copy(), captures)]
            current_path.pop()

    def gather_paths_to_all_matches(self, pattern, all_paths, current_path):
        """Gather paths and captures to matching nodes.

        Same as gather_paths_to_some_matches, but can add multiple
        paths (captures) for one node.
        """
        current_path += [self]

        current_path_copy = current_path.copy()
        for v, c in self.try_match_all(pattern, dict()):
            if v:
                all_paths += [(current_path_copy, c)]

        current_path.pop()

    def substitute(self, variables):
        """Substitute variables into the expression.

        Args:
            variables (dict of (str, Expression)): Expressions to substitute
                under certain variables (symbols).

        Returns:
            The newly formed expression, or self if no substitution was made.
        """
        return self

    def __compute_complexity(self):
        return self.self_complexity

    def __compute_hash(self):
        return hash((self.value, type(self)))

    def __hash__(self):
        return self._hash

    def try_simplify_by_children_evaluation(self, lut):
        """Try to simplify the expression by evaluation of children

        Evaluates children and tries to simplify according to rules
        specific for the expression type (operator).
        """
        return self


class Symbol(Expression):
    self_complexity = 0

    _instances = dict()

    def __new__(cls, name):
        if name not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[name] = instance
        return cls._instances[name]

    def __init__(self, name):
        if self._initialized:
            return
        self._initialized = True

        self._name = name
        self._complexity = self.__compute_complexity();
        self._hash = self.__compute_hash()

    def __iter__(self):
        yield self

    @property
    def name(self):
        return self._name

    @property
    def complexity(self):
        return self._complexity

    def evaluate(self, variables):
        return variables[self.name]

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Symbol: {0}'.format(self.name)

    def to_string(self, parent):
        return self.name

    def __eq__(self, other):
        return type(other) == Symbol and self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def try_match_once(self, pattern, captures):
        if type(pattern) is Symbol:
            return add_if_no_conflict(captures, pattern.name, self)
        else:
            return False

    def try_match_all(self, pattern, prev_captures):
        if type(pattern) is Symbol:
            captures = prev_captures.copy()
            yield (add_if_no_conflict(captures, pattern.name, self), captures)
        else:
            yield (False, prev_captures)

    def apply_pattern_after_path(self, to_match, to_apply, path_captures):
        captures = path_captures[1]
        return to_apply.substitute(captures)

    def gather_paths_to_some_matches(self, pattern, all_paths, current_path):
        captures = dict()
        if self.try_match_once(pattern, captures):
            current_path += [self]
            all_paths += [(current_path.copy(), captures)]
            current_path.pop()

    def gather_paths_to_all_matches(self, pattern, all_paths, current_path):
        current_path += [self]

        current_path_copy = current_path.copy()
        for v, c in self.try_match_all(pattern, dict()):
            if v:
                all_paths += [(current_path_copy, c)]

        current_path.pop()

    def substitute(self, variables):
        return variables[self.name]

    def __compute_complexity(self):
        return self.self_complexity

    def __compute_hash(self):
        return hash((self.name, type(self)))

    def __hash__(self):
        return self._hash

    def try_simplify_by_children_evaluation(self, lut):
        return self


class UnaryOperator(Expression):
    def __iter__(self):
        for e in self.arg:
            yield e
        yield self

    def __init__(self, arg):
        self._arg = arg
        self._complexity = self.__compute_complexity();
        self._hash = self.__compute_hash()

    @property
    def arg(self):
        return self._arg

    @property
    def complexity(self):
        return self._complexity

    def try_match_once(self, pattern, captures):
        if type(pattern) is Symbol:
            return add_if_no_conflict(captures, pattern.name, self)
        elif type(pattern) is type(self):
            return self._arg.try_match_once(pattern.arg, captures)
        else:
            return False

    def try_match_all(self, pattern, prev_captures):
        if type(pattern) is Symbol:
            captures = prev_captures.copy()
            yield (add_if_no_conflict(captures, pattern.name, self), captures)
        elif type(pattern) is type(self):
            captures = prev_captures.copy()
            for v, c in self._arg.try_match_all(pattern.arg, captures):
                if v:
                    yield (v, c)
        else:
            return False

    def gather_paths_to_some_matches(self, pattern, all_paths, current_path):
        current_path += [self]

        captures = dict()
        if self.try_match_once(pattern, captures):
            all_paths += [(current_path.copy(), captures)]

        self._arg.gather_paths_to_some_matches(pattern, all_paths, current_path)

        current_path.pop()

    def gather_paths_to_all_matches(self, pattern, all_paths, current_path):
        current_path += [self]

        current_path_copy = current_path.copy()
        for v, c in self.try_match_all(pattern, dict()):
            if v:
                all_paths += [(current_path_copy, c)]

        self._arg.gather_paths_to_all_matches(pattern, all_paths, current_path)

        current_path.pop()

    def substitute(self, variables):
        return type(self)(self._arg.substitute(variables))

    def apply_pattern_after_path(self, to_match, to_apply, path_captures):
        path = path_captures[0]
        captures = path_captures[1]
        if len(path) == 1:
            return to_apply.substitute(captures)
        else:
            return type(self)(self._arg.apply_pattern_after_path(to_match, to_apply, [path[1:], captures]))

    def __compute_complexity(self):
        return self.self_complexity + self._arg.complexity

    def __compute_hash(self):
        return hash((self._arg, type(self)))

    def children(self):
        return [self._arg]


class BinaryOperator(Expression):
    def __iter__(self):
        for e in self.lhs:
            yield e
        for e in self.rhs:
            yield e
        yield self

    def __init__(self, lhs, rhs):
        self._lhs = lhs
        self._rhs = rhs
        self._complexity = self.__compute_complexity();
        self._hash = self.__compute_hash()

    @property
    def lhs(self):
        return self._lhs

    @property
    def rhs(self):
        return self._rhs

    @property
    def complexity(self):
        return self._complexity

    def try_match_once(self, pattern, captures):
        t = type(pattern)
        if t is Symbol:
            return add_if_no_conflict(captures, pattern.name, self)
        elif t is type(self):
            return self._lhs.try_match_once(pattern.lhs, captures) and self._rhs.try_match_once(pattern.rhs, captures)
        else:
            return False

    def try_match_all(self, pattern, prev_captures):
        t = type(pattern)
        if t is Symbol:
            captures = prev_captures.copy()
            yield (add_if_no_conflict(captures, pattern.name, self), captures)
        elif t is type(self):
            captures = prev_captures.copy()
            for v, c in self._lhs.try_match_all(pattern.lhs, captures):
                if v:
                    c_copy = c.copy()
                    for v2, c2 in self._rhs.try_match_all(pattern.rhs, c_copy):
                        if v2:
                            yield (v2, c2)
        else:
            yield (False, prev_captures)

    def gather_paths_to_some_matches(self, pattern, all_paths, current_path):
        current_path += [self]

        captures = dict()
        if self.try_match_once(pattern, captures):
            all_paths += [(current_path.copy(), captures)]

        self._lhs.gather_paths_to_some_matches(pattern, all_paths, current_path)
        self._rhs.gather_paths_to_some_matches(pattern, all_paths, current_path)

        current_path.pop()

    def gather_paths_to_all_matches(self, pattern, all_paths, current_path):
        current_path += [self]

        current_path_copy = current_path.copy()
        for v, c in self.try_match_all(pattern, dict()):
            if v:
                all_paths += [(current_path_copy, c)]

        self._lhs.gather_paths_to_all_matches(pattern, all_paths, current_path)
        self._rhs.gather_paths_to_all_matches(pattern, all_paths, current_path)

        current_path.pop()

    def substitute(self, variables):
        return type(self)(self._lhs.substitute(variables), self._rhs.substitute(variables))

    def apply_pattern_after_path(self, to_match, to_apply, path_captures):
        path = path_captures[0]
        captures = path_captures[1]
        if len(path) == 1:
            return to_apply.substitute(captures)
        elif path[1] is self._lhs:
            return type(self)(self._lhs.apply_pattern_after_path(to_match, to_apply, [path[1:], captures]), self._rhs)
        else:
            return type(self)(self._lhs, self._rhs.apply_pattern_after_path(to_match, to_apply, [path[1:], captures]))

    def __compute_complexity(self):
        return self.self_complexity + self._lhs.complexity + self._rhs.complexity

    def __compute_hash(self):
        return hash((self._lhs, self._rhs, type(self)))

    def get_lowest_complexity_child(self):
            if self._lhs.complexity < self._rhs.complexity:
                return self._lhs
            else:
                return self._rhs

    def children(self):
        return [self._lhs, self._rhs]

class SymmetricBinaryOperator(BinaryOperator):
    # sorted by hash, to because order doesn't matter
    def __init__(self, lhs, rhs):
        if hash(lhs) < hash(rhs):
            BinaryOperator.__init__(self, lhs, rhs)
        else:
            BinaryOperator.__init__(self, rhs, lhs)

    # This approach comes with one disadvantage compared to permuting.
    # Namely, it can only apply once per node, so if the expression
    # could be matched after changing the order of operands in the pattern
    # we lose some possible transformations. Again, this change was made
    # as an additional heuristic to make the code run faster,
    # possibly at a cost of inability to simplify some rare expressions.
    #'''
    def try_match_once(self, pattern, captures):
        t = type(pattern)
        if t is Symbol:
            return add_if_no_conflict(captures, pattern.name, self)
        elif t is type(self):
            captures_copy = captures.copy()
            if self.lhs.try_match_once(pattern.lhs, captures_copy) and self.rhs.try_match_once(pattern.rhs, captures_copy):
                captures.update(captures_copy)
                return True
            else:
                return self.lhs.try_match_once(pattern.rhs, captures) and self.rhs.try_match_once(pattern.lhs, captures)

        else:
            return False
    #'''

    def try_match_all(self, pattern, prev_captures):
        t = type(pattern)
        if t is Symbol:
            captures = prev_captures.copy()
            yield (add_if_no_conflict(captures, pattern.name, self), captures)
        elif t is type(self):
            captures = prev_captures.copy()
            for v, c in self._lhs.try_match_all(pattern.lhs, captures):
                if v:
                    c_copy = c.copy()
                    for v2, c2 in self._rhs.try_match_all(pattern.rhs, c_copy):
                        if v2:
                            yield (v2, c2)

            captures = prev_captures.copy()
            for v, c in self._lhs.try_match_all(pattern.rhs, captures):
                if v:
                    c_copy = c.copy()
                    for v2, c2 in self._rhs.try_match_all(pattern.lhs, c_copy):
                        if v2:
                            yield (v2, c2)
        else:
            yield (False, prev_captures)

class Negation(UnaryOperator):
    precedence = 10
    self_complexity = 1

    def __init__(self, arg):
        UnaryOperator.__init__(self, arg)

    def evaluate(self, variables):
        return not self.arg.evaluate(variables)

    def __str__(self):
        return self.to_string(None)

    def to_string(self, parent):
        return ('(!{0})' if self.__uses_parens_inside(parent) else '!{0}').format(self.arg.to_string(Negation))

    @classmethod
    def __uses_parens_inside(cls, parent):
        if not parent:
            return False
        if parent == Negation:
            return False
        else:
            return Negation.precedence <= parent.precedence

    def __eq__(self, other):
        return type(other) == Negation and self.arg == other.arg

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self._hash

    def try_simplify_by_children_evaluation(self, lut):
        a = self._arg.try_simplify_by_evaluation(lut)
        if a == Constant(False):
            return Constant(True)
        elif a == Constant(True):
            return Constant(False)
        else:
            if not a is self.arg:
                return Negation(a)
            else:
                return self



class Disjunction(SymmetricBinaryOperator):
    precedence = 8
    self_complexity = 3

    @classmethod
    def of(cls, exprs):
        if len(exprs) == 1:
            return exprs[0]
        else:
            mid = len(exprs) // 2
            return Disjunction(Disjunction.of(exprs[:mid]), Disjunction.of(exprs[mid:]))

    def __init__(self, lhs, rhs):
        SymmetricBinaryOperator.__init__(self, lhs, rhs)

    def evaluate(self, variables):
        return self.lhs.evaluate(variables) or self.rhs.evaluate(variables)

    def __str__(self):
        return self.to_string(None)

    def to_string(self, parent):
        this_precedence = Disjunction.precedence
        return ('({0}|{1})' if self.__uses_parens_inside(parent) else '{0}|{1}').format(self.lhs.to_string(Disjunction), self.rhs.to_string(Disjunction))

    @classmethod
    def __uses_parens_inside(cls, parent):
        if not parent:
            return False
        elif parent == Disjunction:
            return False
        else:
            return Disjunction.precedence <= parent.precedence

    def __eq__(self, other):
        return type(other) == Disjunction and (self.lhs == other.lhs and self.rhs == other.rhs)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self._hash

    def try_simplify_by_children_evaluation(self, lut):
        l = self.lhs.try_simplify_by_evaluation(lut)
        r = self.rhs.try_simplify_by_evaluation(lut)
        if l == Constant(True):
            return Constant(True)
        elif l == Constant(False):
            return r
        elif r == Constant(True):
            return Constant(True)
        elif r == Constant(False):
            return l
        elif are_equal_by_evaluation(l, r):
            return min([l, r], key = lambda x: count_distinct_symbols(x))
        elif are_opposite_by_evaluation(l, r):
            return Constant(False)
        else:
            if l is not self.lhs or r is not self.rhs:
                return Disjunction(l, r)
            else:
                return self


class ExclusiveDisjunction(SymmetricBinaryOperator):
    precedence = 8
    self_complexity = 3

    def __init__(self, lhs, rhs):
        SymmetricBinaryOperator.__init__(self, lhs, rhs)

    def evaluate(self, variables):
        return self.lhs.evaluate(variables) != self.rhs.evaluate(variables)

    def __str__(self):
        return self.to_string(None)

    def to_string(self, parent):
        this_precedence = Disjunction.precedence
        return ('({0}^{1})' if self.__uses_parens_inside(parent) else '{0}^{1}').format(self.lhs.to_string(ExclusiveDisjunction), self.rhs.to_string(ExclusiveDisjunction))

    @classmethod
    def __uses_parens_inside(cls, parent):
        if not parent:
            return False
        elif parent == ExclusiveDisjunction:
            return False
        else:
            return ExclusiveDisjunction.precedence <= parent.precedence

    def __eq__(self, other):
        return type(other) == ExclusiveDisjunction and (self.lhs == other.lhs and self.rhs == other.rhs)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self._hash

    def try_simplify_by_children_evaluation(self, lut):
        l = self.lhs.try_simplify_by_evaluation(lut)
        r = self.rhs.try_simplify_by_evaluation(lut)
        if l == Constant(True):
            return Negation(r)
        elif l == Constant(False):
            return r
        elif r == Constant(True):
            return Negation(l)
        elif r == Constant(False):
            return l
        elif are_equal_by_evaluation(l, r):
            return Constant(False)
        elif are_opposite_by_evaluation(l, r):
            return Constant(True)
        else:
            if l is not self.lhs or r is not self.rhs:
                return ExclusiveDisjunction(l, r)
            else:
                return self


class Conjunction(SymmetricBinaryOperator):
    precedence = 8
    self_complexity = 3

    @classmethod
    def of(cls, exprs):
        if len(exprs) == 1:
            return exprs[0]
        else:
            mid = len(exprs) // 2
            return Conjunction(Conjunction.of(exprs[:mid]), Conjunction.of(exprs[mid:]))

    def __init__(self, lhs, rhs):
        SymmetricBinaryOperator.__init__(self, lhs, rhs)

    def evaluate(self, variables):
        return self.lhs.evaluate(variables) and self.rhs.evaluate(variables)

    def __str__(self):
        return self.to_string(None)

    def to_string(self, parent):
        this_precedence = Disjunction.precedence
        return ('({0}&{1})' if self.__uses_parens_inside(parent) else '{0}&{1}').format(self.lhs.to_string(Conjunction), self.rhs.to_string(Conjunction))

    @classmethod
    def __uses_parens_inside(cls, parent):
        if not parent:
            return False
        elif parent == Conjunction:
            return False
        else:
            return Conjunction.precedence <= parent.precedence

    def __eq__(self, other):
        return type(other) == Conjunction and (self.lhs == other.lhs and self.rhs == other.rhs)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self._hash

    def try_simplify_by_children_evaluation(self, lut):
        l = self.lhs.try_simplify_by_evaluation(lut)
        r = self.rhs.try_simplify_by_evaluation(lut)
        if l == Constant(False):
            return Constant(False)
        elif l == Constant(True):
            return r
        elif r == Constant(False):
            return Constant(False)
        elif r == Constant(True):
            return l
        elif are_equal_by_evaluation(l, r):
            return min([l, r], key = lambda x: count_distinct_symbols(x))
        elif are_opposite_by_evaluation(l, r):
            return Constant(False)
        else:
            if l is not self.lhs or r is not self.rhs:
                return Conjunction(l, r)
            else:
                return self


class Implication(BinaryOperator):
    precedence = 4
    self_complexity = 3

    def __init__(self, lhs, rhs):
        BinaryOperator.__init__(self, lhs, rhs)

    def evaluate(self, variables):
        return (not self.lhs.evaluate(variables)) or self.rhs.evaluate(variables)

    def __str__(self):
        return self.to_string(None)

    def to_string(self, parent):
        this_precedence = Disjunction.precedence
        return ('({0}=>{1})' if self.__uses_parens_inside(parent) else '{0}=>{1}').format(self.lhs.to_string(Implication), self.rhs.to_string(Implication))

    @classmethod
    def __uses_parens_inside(cls, parent):
        if not parent:
            return False
        else:
            return Implication.precedence <= parent.precedence

    def __eq__(self, other):
        return type(other) == Implication and (self.lhs == other.lhs and self.rhs == other.rhs)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self._hash

    def try_simplify_by_children_evaluation(self, lut):
        l = self.lhs.try_simplify_by_evaluation(lut)
        r = self.rhs.try_simplify_by_evaluation(lut)
        if l == Constant(True):
            return r
        elif l == Constant(False):
            return Constant(True)
        elif r == Constant(True):
            return Constant(True)
        elif r == Constant(False):
            return Negation(l)
        elif are_equal_by_evaluation(l, r):
            return Constant(True)
        elif are_opposite_by_evaluation(l, r):
            return Negation(l)
        else:
            if l is not self.lhs or r is not self.rhs:
                return Implication(l, r)
            else:
                return self


class Equivalency(SymmetricBinaryOperator):
    precedence = 4
    self_complexity = 3

    def __init__(self, lhs, rhs):
        SymmetricBinaryOperator.__init__(self, lhs, rhs)

    def evaluate(self, variables):
        return self.lhs.evaluate(variables) == self.rhs.evaluate(variables)

    def __str__(self):
        return self.to_string(None)

    def to_string(self, parent):
        this_precedence = Disjunction.precedence
        return ('({0}<=>{1})' if self.__uses_parens_inside(parent) else '{0}<=>{1}').format(self.lhs.to_string(Equivalency), self.rhs.to_string(Equivalency))

    @classmethod
    def __uses_parens_inside(cls, parent):
        if not parent:
            return False
        elif parent == Equivalency:
            return False
        else:
            return Equivalency.precedence <= parent.precedence

    def __eq__(self, other):
        return type(other) == Equivalency and (self.lhs == other.lhs and self.rhs == other.rhs)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self._hash

    def try_simplify_by_children_evaluation(self, lut):
        l = self.lhs.try_simplify_by_evaluation(lut)
        r = self.rhs.try_simplify_by_evaluation(lut)
        if l == Constant(True):
            return r
        elif l == Constant(False):
            return Negation(r)
        elif r == Constant(True):
            return l
        elif r == Constant(False):
            return Negation(l)
        elif are_equal_by_evaluation(l, r):
            return Constant(True)
        elif are_opposite_by_evaluation(l, r):
            return Constant(False)
        else:
            if l is not self.lhs or r is not self.rhs:
                return Equivalency(l, r)
            else:
                return self

