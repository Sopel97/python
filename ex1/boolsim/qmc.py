from .expression import *
from .parser import *
from .util import *

class Implicant:
    def __init__(self, minterm, wildcards):
        self.minterm = minterm
        self.wildcards = wildcards

    def __repr__(self):
        return '({0}, {1})'.format(self.minterm, self.wildcards)

    def __eq__(self, other):
        return self.minterm == other.minterm and self.wildcards == other.wildcards

    def __neq__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.minterm, self.wildcards))

    def all_minterms(self, dim):
        i = BoolVector(dim, self.minterm)
        num_minterms = pow2(popcnt(self.wildcards))
        for _ in range(num_minterms):
            yield i.val
            i.increment_masked_preserve_other(self.wildcards)

def hamming_distance(lhs, rhs):
    return popcnt(lhs ^ rhs)

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
        return [set() for _ in range(dim+1)]

    def _gen_next_table(self, prev_table):
        dim = len(self._ids_to_symbols)
        next_table = self._empty_table()

        prime_implicants = set()
        combinable_implicants = set()
        # iterate all possible hamming weigths
        for hw in range(dim):
            # pairs of implicants i1, i2

            for i1 in prev_table[hw]:
                for i2 in prev_table[hw+1]:
                    if i1.wildcards != i2.wildcards:
                        continue

                    w = i1.wildcards
                    # zero out bits under wildcard so they won't
                    # be significant in calculating hamming distance
                    i1s = i1.minterm & ~w
                    i2s = i2.minterm & ~w
                    if hamming_distance(i1s, i2s) == 1:
                        # update wildcards with bit where they differ
                        wildcards = (i1s ^ i2s) | w
                        # we can take either i1s or i2s, doesnt matterr
                        # since the difference is under a wildcard
                        # but we have to zero out the differing bit so
                        # it's easier to find repetitions
                        next_table[hw].add(Implicant(i1s & ~wildcards, wildcards))

                        # add them as combinable so we can check later which are prime
                        combinable_implicants.add(i1)
                        combinable_implicants.add(i2)

        for hw in range(dim+1):
            prime_implicants.update({i for i in prev_table[hw] if i not in combinable_implicants})

        return next_table, prime_implicants

    def _filter_prime_implicants(self, prime_implicants):
        dim = len(self._ids_to_symbols)
        prime_implicant_chart = [[] for _ in range(pow2(dim))]

        filtered_implicants = set()

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

            filtered_implicants.add(best_implicant)
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
                current_table[popcnt(i)].add(Implicant(i, 0))

        prime_implicants = set()
        while True:
            print("Step")
            #print(current_table)
            next_table, current_prime_implicants = self._gen_next_table(current_table)
            prime_implicants.update(current_prime_implicants)
            current_table = next_table
            # if all sets are empty == no further combinations made
            if not any(next_table):
                break

        #print(prime_implicants)

        print("Filtering")
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

        print("Converting")
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
