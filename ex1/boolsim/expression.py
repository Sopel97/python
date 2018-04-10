from .util import *

import textwrap

def gather_symbols_from_expr(expr):
    return list({e.name for e in expr if type(e) == Symbol})

def count_distinct_symbols(expr):
    return len(gather_symbols_from_expr(expr))

def evaluates_to(expr, boolean):
    ids_to_symbols = gather_symbols_from_expr(expr)
    dim = len(ids_to_symbols)
    for i in range(pow2(dim)):
        if expr.evaluate(symbol_dict_from_index(ids_to_symbols, BoolVector(dim, i))) != boolean:
            return False

    return True

def symbol_dict_from_index(ids_to_symbols, index):
        return {ids_to_symbols[i] : bool(index[i]) for i in range(len(ids_to_symbols))}

def evaluate_all(expr, ids_to_symbols):
    dim = len(ids_to_symbols)
    return [expr.evaluate(symbol_dict_from_index(ids_to_symbols, BoolVector(dim, i))) for i in range(pow2(dim))]

def is_true_by_evaluation(expr):
    return evaluates_to(expr, True)

def is_false_by_evaluation(expr):
    return evaluates_to(expr, False)

def are_equal_by_evaluation(lhs, rhs):
    expr = Equivalency(lhs, rhs)
    return is_true_by_evaluation(expr)

def are_opposite_by_evaluation(lhs, rhs):
    expr = Equivalency(lhs, rhs)
    return is_false_by_evaluation(expr)

def add_if_no_conflict(d, key, value):
    if key in d:
        # The check by truth tables is necessary, because we don't
        # permute expressions on leaves of simplifying rules.
        # The expression tree equality check is an optimistic heuristic.
        return d[key] == value or are_equal_by_evaluation(d[key], value)

    d[key] = value
    return True


class Expression:
    __slots__ = []

    def get_paths_to_some_matches(self, pattern):
        all_paths = []
        self.gather_paths_to_some_matches(pattern, all_paths, [])
        return all_paths

    def get_paths_to_all_matches(self, pattern):
        all_paths = []
        self.gather_paths_to_all_matches(pattern, all_paths, [])
        return all_paths

    def apply_pattern_recursively_to_all(self, to_match, to_apply):
        resulting_expressions = set()

        paths = self.get_paths_to_all_matches(to_match)
        for path in paths:
            resulting_expressions.add(self.apply_pattern_after_path(to_match, to_apply, path))

        return resulting_expressions

    def apply_pattern_recursively_to_some(self, to_match, to_apply):
        resulting_expressions = set()

        paths = self.get_paths_to_some_matches(to_match)
        for path in paths:
            resulting_expressions.add(self.apply_pattern_after_path(to_match, to_apply, path))

        return resulting_expressions

    def try_simplify_by_evaluation(self, lut):
        simplified = lut(self)
        if not simplified is self:
            return simplified

        return self.try_simplify_by_children_evaluation(lut)

    def __repr__(self):
        indentation = '    '
        return ''.join(
            [
                'Type: {0}; Complexity: {1}; Children:\n'.format(self.__class__.__name__, self.complexity),
                textwrap.indent('\n'.join(repr(e) for e in self.children()), indentation)
            ]
        )

    def children(self):
        return []

class Constant(Expression):
    self_complexity = -1

    __slots__ = '_value', '_complexity', '_hash'

    def __init__(self, value):
        self._value = value
        self._complexity = self.__compute_complexity()
        self._hash = self.__compute_hash()

    def __iter__(self):
        yield self

    @property
    def value(self):
        return self._value

    @property
    def complexity(self):
        return self._complexity

    def evaluate(self, variables):
        return self._value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return 'Constant: {0}'.format(self.value)

    def to_string(self, parent):
        return str(self.value)

    def __eq__(self, other):
        return type(other) == Constant and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def try_match_once(self, pattern, captures):
        if type(pattern) is Symbol:
            return add_if_no_conflict(captures, pattern.name, self)
        elif type(pattern) is Constant:
            return self.value == pattern.value
        else:
            return False

    def try_match_all(self, pattern, prev_captures):
        if type(pattern) is Symbol:
            captures = prev_captures.copy()
            yield (add_if_no_conflict(captures, pattern.name, self), captures)
        elif type(pattern) is Constant:
            captures = prev_captures.copy()
            yield (self.value == pattern.value, captures)
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
        return self

    def __compute_complexity(self):
        return self.self_complexity

    def __compute_hash(self):
        return hash((self.value, type(self)))

    def __hash__(self):
        return self._hash

    def try_simplify_by_children_evaluation(self, lut):
        return self


class Symbol(Expression):
    self_complexity = 0

    __slots__ = '_name', '_complexity', '_hash'

    def __init__(self, name):
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

    __slots__ = '_arg', '_complexity', '_hash'

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

    __slots__ = '_lhs', '_rhs', '_complexity', '_hash'

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

