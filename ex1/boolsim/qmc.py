from .expression import *
from .parser import *
from .util import *

from collections import defaultdict

class Implicant:
    __slots__ = ['minterm', 'wildcards', 'hash']

    def __init__(self, minterm, wildcards):
        # it is assumed that where wildcards has a 1 bit then minterm has 0 bit
        self.minterm = minterm
        self.wildcards = wildcards
        self.hash = hash((minterm, wildcards))

    def __repr__(self):
        return '({0}, {1})'.format(self.minterm, self.wildcards)

    def __eq__(self, other):
        return self.minterm == other.minterm and self.wildcards == other.wildcards

    def __neq__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.hash

    def all_minterms(self, dim):
        i = BoolVector(dim, self.minterm)
        num_minterms = pow2(popcnt(self.wildcards))
        for _ in range(num_minterms):
            yield i.val
            i.increment_masked_preserve_other(self.wildcards)

class Qmc:
    @classmethod
    def from_expression(cls, expr):
        return Qmc(expr)

    def __init__(self, expr):
        self._expr = expr
        # for testing it's good to sort ids_to_symbols
        self._ids_to_symbols = gather_symbols_from_expr(expr)

    def _empty_table(self):
        dim = len(self._ids_to_symbols)
        # binned by wildcards
        return [defaultdict(lambda: set()) for _ in range(dim+1)]

    def _gen_next_table(self, prev_table):
        dim = len(self._ids_to_symbols)
        next_table = self._empty_table()

        prime_implicants = set()
        combinable_implicants = set()

        #print("MAIN LOOP START")
        # iterate all possible hamming weigths
        for hw in range(dim):
            # pairs of implicants i1, i2
            # they are further binned by wildcards
            # so only compare those with the same wildcard
            for w, i1s in prev_table[hw].items():
                for i1 in i1s:
                    w = i1.wildcards
                    i1m = i1.minterm
                    for i2 in prev_table[hw+1][w]:
                        # check if popcnt(x) == 1
                        # with out storage choice it is guaranteed that at i1 and i2 are different
                        # so x will never be 0
                        # So amounts to just checking if x is a power of 2
                        x = i2.minterm ^ i1m
                        if (x & (x-1)) == 0:
                            # update wildcards with bit where they differ
                            wildcards = x | w
                            # we can take either i1m or i2m, doesnt matterr
                            # since the difference is under a wildcard
                            # but we have to zero out the differing bit
                            # (see requirement in Implicant constructor)
                            next_table[hw][wildcards].add(Implicant(i1m & ~wildcards, wildcards))

                            # add them as combinable so we can check later which are prime
                            combinable_implicants.add(i1)
                            combinable_implicants.add(i2)

        #print("MAIN LOOP END")
        for hw in range(dim+1):
            prime_implicants.update({i for _, iss in prev_table[hw].items() for i in iss if i not in combinable_implicants})

        return next_table, prime_implicants

    def _filter_prime_implicants(self, prime_implicants):
        dim = len(self._ids_to_symbols)
        prime_implicant_chart = [[] for _ in range(pow2(dim))]

        filtered_implicants = []

        for pi in prime_implicants:
            for m in pi.all_minterms(dim):
                prime_implicant_chart[m].append(pi)

        unsatisfied_minterms = {i for i, e in enumerate(prime_implicant_chart) if e}

        while unsatisfied_minterms:
            minterm_with_min_implicants_id = min(unsatisfied_minterms, key=lambda x: len(prime_implicant_chart[x]))
            minterm_with_min_implicants = prime_implicant_chart[minterm_with_min_implicants_id]

            best_implicant = minterm_with_min_implicants[0]
            if len(minterm_with_min_implicants) > 1:
                best_implicant = max(minterm_with_min_implicants, key=lambda x: popcnt(x.wildcards))

            filtered_implicants.append(best_implicant)
            for m in best_implicant.all_minterms(dim):
                unsatisfied_minterms.discard(m)

        return filtered_implicants

    def _convert_implicant_to_conjunction(self, implicant):
        m = implicant.minterm
        w = implicant.wildcards

        exprs = []
        for s in self._ids_to_symbols:
            if w & 1 == 0:
                # include the symbol in the conjunction
                if m & 1 == 1:
                    exprs.append(Symbol(s))
                else: # negated
                    exprs.append(Negation(Symbol(s)))

            m >>= 1
            w >>= 1

        return Conjunction.of(exprs)

    def _convert_implicant_to_disjunction(self, implicant):
        m = implicant.minterm
        w = implicant.wildcards

        exprs = []
        for s in self._ids_to_symbols:
            if w & 1 == 0:
                # include the symbol in the conjunction
                if m & 1 == 0:
                    exprs.append(Symbol(s))
                else: # negated
                    exprs.append(Negation(Symbol(s)))

            m >>= 1
            w >>= 1

        return Disjunction.of(exprs)

    def _convert_implicants_to_dnf(self, implicants):
        conjunctions = [self._convert_implicant_to_conjunction(i) for i in implicants]

        return Disjunction.of(conjunctions)

    def _convert_implicants_to_cnf(self, implicants):
        disjunctions = [self._convert_implicant_to_disjunction(i) for i in implicants]

        return Conjunction.of(disjunctions)

    def _gather_prime_implicants(self, evals):
        #print(self._ids_to_symbols)

        dim = len(self._ids_to_symbols)
        current_table = self._empty_table()
        for i, e in enumerate(evals):
            if e:
                current_table[popcnt(i)][0].add(Implicant(i, 0))

        prime_implicants = set()
        while True:
            #print("Step")
            #print(current_table)
            next_table, current_prime_implicants = self._gen_next_table(current_table)
            prime_implicants.update(current_prime_implicants)
            current_table = next_table
            # if all sets are empty == no further combinations made
            if not any(next_table):
                break

        #print(prime_implicants)

        #print("Filtering")
        return self._filter_prime_implicants(prime_implicants)

    def to_dnf(self):
        dim = len(self._ids_to_symbols)
        evals = evaluate_all(self._expr, self._ids_to_symbols)

        num_truths = evals.count(True)
        if num_truths == 0:
            return Constant(False)
        elif num_truths == pow2(dim):
            return Constant(True)

        filtered_prime_implicants = self._gather_prime_implicants(evals)

        #print("Converting")
        return self._convert_implicants_to_dnf(filtered_prime_implicants)

    def to_cnf(self):
        dim = len(self._ids_to_symbols)
        evals = evaluate_all(self._expr, self._ids_to_symbols)

        num_truths = evals.count(True)
        if num_truths == 0:
            return Constant(False)
        elif num_truths == pow2(dim):
            return Constant(True)

        filtered_prime_implicants = self._gather_prime_implicants([not e for e in evals])

        return self._convert_implicants_to_cnf(filtered_prime_implicants)
