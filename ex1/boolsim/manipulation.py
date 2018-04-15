from .expression import *
from .parser import *
from .util import *
from .karnaugh import *
from .lut import *
from .rulesets import *
import random

# apply_pattern_recursively_to_some is used, but it can be replaced
# with apply_pattern_recursively_to_all for better simplification
# opportunities, but at the cost of speed
class FullSimplifier:
    def __init__(
        self,
        ruleset,
        expr,
        confidence_factor=2.5,
        confidence_factor_min_complexity=10,
        max_preserved_exprs=8,
        num_permuting_iterations=3):
        # confidence_factor is used to prune the expressions with much worse
        # complexity than others.
        # confidence_factor_min_complexity tells after what complexity
        # the confidence_factor can prune other expressions.
        # Ie. no expressions with complexity less than confidence_factor_min_complexity
        # will be pruned.

        self._ruleset = ruleset
        self._is_completed = False
        self._max_preserved_expressions = max_preserved_exprs
        self._num_permuting_iterations = num_permuting_iterations

        # If an expression can be found in the lookup table then it is
        # guaranteed to be retrieved minimal.
        looked_up_expr = try_lookup_expression(expr)
        if not looked_up_expr is expr:
            self._is_completed = True
            self._current_exprs = {looked_up_expr}
            self._min_complexity = looked_up_expr.complexity
        else:
            km = KarnaughMap.from_expression(expr)
            candidate_root_exprs = [expr, expr.try_simplify_by_evaluation(try_lookup_expression), km.to_dnf(), km.to_cnf()]
            self._min_complexity = min(candidate_root_exprs, key = lambda x: x.complexity).complexity
            self._current_exprs = {e for e in candidate_root_exprs if e.complexity <= max(confidence_factor_min_complexity, self._min_complexity * confidence_factor)}

            # Since reduction follows symmetry rules without permuting the
            # expression it is profitable to do it first.
            self._reduction_step()
            self._pruning_step()

    @property
    def current_exprs(self):
        return self._current_exprs

    @property
    def is_completed(self):
        return self._is_completed

    def _reduction_step(self):
        # Try reduce as much as possible before continuing
        # It's guaranteed to exit the loop because all reducing_rules
        # decrease the complexity
        prev_reduced_exprs = self._current_exprs
        while True:
            new_reduced_exprs = set()
            for e in prev_reduced_exprs:
                for to_match, to_apply in self._ruleset.reducing_rules:
                    new_reduced_exprs.update(e.apply_pattern_recursively_to_some(to_match, to_apply))

            if not new_reduced_exprs:
                break

            prev_reduced_exprs = new_reduced_exprs - self._current_exprs
            self._current_exprs.update(prev_reduced_exprs)

    def _pruning_step(self):
        # Reduces the number of expressions preserved between iterations. Should be kept low,
        # but making it too low may prune good expressions.
        if len(self._current_exprs) > self._max_preserved_expressions:
            self._current_exprs = {e.try_simplify_by_evaluation(try_lookup_expression) for e in sorted(self._current_exprs, key=lambda x: x.complexity)[:self._max_preserved_expressions]}

    def _permutation_step(self):
        # The bigger the value, the more permutations (increasing in depth) are tried.
        # Execution time increases exponentially with this number.
        prev_permuted_exprs = self._current_exprs
        for i in range(self._num_permuting_iterations):
            new_permuted_exprs = set()
            for e in prev_permuted_exprs:
                for to_match, to_apply in self._ruleset.permuting_rules:
                    # apply_pattern_recursively_to_some -> apply_pattern_recursively_to_all to improve
                    # coverage with an impact on speed
                    new_permuted_exprs.update(e.apply_pattern_recursively_to_some(to_match, to_apply))

            prev_permuted_exprs = new_permuted_exprs - self._current_exprs
            # Simplifying by evaluation should not be needed as much, as long as add_if_no_conflict
            # checks equality with truth table. It only accounts for subexpressions that
            # are on leaves of simplification rules, but the simpler ones should be
            # already simplified by conversion to CNF or DNF.
            self._current_exprs.update(prev_permuted_exprs)
            #self._current_exprs.update(e.try_simplify_by_evalutation() for e in prev_permuted_exprs)

    def step(self):
        if self._is_completed:
            return self

        self._permutation_step()

        self._reduction_step()

        self._pruning_step()

        old = self._min_complexity
        self._min_complexity = min(self._current_exprs, key = lambda x: x.complexity).complexity
        if self._min_complexity == old:
            self._is_completed = True

        return self

    def step_until_done(self):
        while not self._is_completed:
            self.step()

        return self

    def best_expr(self):
        return min(self._current_exprs, key = lambda x: x.complexity)


class DnfSimplifier:
    def __init__(self, algo, expr):
        self._best = algo.from_expression(expr).to_dnf()
        self._is_completed = True

    @property
    def is_completed(self):
        return self._is_completed

    def best_expr(self):
        if not self._is_completed:
            self.step_until_done()

        return self._best

    def step(self):
        return self

    def step_until_done(self):
        return self


class CnfSimplifier:
    def __init__(self, algo, expr):
        self._best = algo.from_expression(expr).to_cnf()
        self._is_completed = True

    @property
    def is_completed(self):
        return self._is_completed

    def best_expr(self):
        if not self._is_completed:
            self.step_until_done()

        return self._best

    def step(self):
        return self

    def step_until_done(self):
        return self


class Scrambler:
    def __init__(self, ruleset, expr, max_preserved_exprs=16):
        self._ruleset = ruleset
        self._all_exprs = {expr}
        self._max_preserved_expressions = max_preserved_exprs

    def step(self, n = 1):
        for i in range(n):
            new_exprs = set()
            for e in self._all_exprs:
                for to_match, to_apply in self._ruleset.permuting_rules:
                    new_exprs.update(e.apply_pattern_recursively_to_some(to_match, to_apply))

            self._all_exprs.update(new_exprs)

            if len(self._all_exprs) > self._max_preserved_expressions:
                self._all_exprs = self.n_random_weighted(self._max_preserved_expressions)

        return self

    def n_random_weighted(self, n):
        return set(sorted(self._all_exprs, key = lambda x: -(random.randint(-1, x.complexity)))[:n])

    def random_expr(self):
        return random.choice(list(self._all_exprs))