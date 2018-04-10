from .expression import *
from .parser import *
from .util import *

class Region:
    def __init__(self, start, direction, is_used):
        self.start = start
        self.direction = direction
        self.symbols = (~direction).val
        self.negations = (~start).val
        self.is_used = is_used

class KarnaughMap:
    @classmethod
    def _fill(cls, ids_to_symbols, expr):
        dim = len(ids_to_symbols)
        return evaluate_all(expr, ids_to_symbols)

    @classmethod
    def from_expression(cls, expr):
        ids_to_symbols = gather_symbols_from_expr(expr)

        dim = len(ids_to_symbols)
        table = KarnaughMap._fill(ids_to_symbols, expr)

        return KarnaughMap(dim, table, ids_to_symbols)

    def __init__(self, dim, table, its):
        self.dim = dim
        self.table = table
        self.ids_to_symbols = its

    def __eq__(self, other):
        return self.table == other.table and self.ids_to_symbols == other.ids_to_symbols

    def __invert__(self):
        return KarnaughMap(self.dim, [(not x) for x in self.table], self.ids_to_symbols)

    def __neq__(self, other):
        return not self.__eq__(other)

    def is_true(self):
        return all(self.table)

    def is_false(self):
        return self.table.count(False) == len(self.table)

    def _gather_regions(self):
        regions = []

        visit_counts = [0] * len(self.table)
        visits_left = self.table.count(1)
        num_directions = pow2(self.dim)

        all_directions = []
        d = BoolVector(self.dim, 0)
        for i in range(num_directions):
            all_directions += [d.copy()]
            d.increment()
        all_directions.sort(key = lambda d : -d.ones())

        for direction in all_directions:
            num_starting_positions = pow2(direction.zeroes())
            start = BoolVector(self.dim, 0)
            for i in range(num_starting_positions):
                all_ones = True
                num_added_visits = 0
                for index in volume2(start.val, direction):
                    if self.table[index] == 0:
                        all_ones = False
                        break
                    elif visit_counts[index] == 0:
                        num_added_visits += 1

                if all_ones:
                    # apply the product
                    for index in volume2(start.val, direction):
                        visit_counts[index] += 1

                    regions += [Region(start.copy(), direction.copy(), True)]
                    visits_left -= num_added_visits
                    if visits_left <= 0:
                        break

                start.increment_masked((~direction.val) & direction.mask)

            if visits_left <= 0:
                break

        # remove unneeded regions
        for region in reversed(regions):
            can_be_removed = True
            for j in volume2(region.start.val, region.direction):
                if visit_counts[j] <= 1:
                    can_be_removed = False
                    break

            if can_be_removed:
                for j in volume2(region.start.val, region.direction):
                    visit_counts[j] -= 1

                region.is_used = False

        return regions, visit_counts


    def to_cnf(self):
        regions, visit_counts = (~self)._gather_regions()
        return self._gather_regions_as_product_of_sums(regions, visit_counts)

    def _gather_regions_as_product_of_sums(self, regions, visit_counts):
        # gather used regions
        sums = []
        for r in regions:
            if r.is_used:
                if r.symbols == 0: # the expression doesn't depend on any variables, so it is always true
                    return Constant(False)

                sums += [self._translate_region_into_sum(r)]

        if not sums:
            return Constant(True)

        return Conjunction.of(sums)

    def _translate_region_into_sum(self, region):
        symbols = []
        symbol_id = 0
        symbols_raw = region.symbols
        negations_raw = region.negations
        while symbols_raw != 0:
            if (symbols_raw & 1) == 1:
                if (negations_raw & 1) == 0: # negations are opposite compared to the products
                    symbols += [Negation(Symbol(self.ids_to_symbols[symbol_id]))]
                else:
                    symbols += [Symbol(self.ids_to_symbols[symbol_id])]

            symbols_raw >>= 1
            negations_raw >>= 1
            symbol_id += 1

        return Disjunction.of(symbols)

    def to_dnf(self):
        regions, visit_counts = self._gather_regions()
        return self._gather_regions_as_sum_of_products(regions, visit_counts)

    def _gather_regions_as_sum_of_products(self, regions, visit_counts):
        # gather used regions
        products = []
        for r in regions:
            if r.is_used:
                if r.symbols == 0: # the expression doesn't depend on any variables, so it is always true
                    return Constant(True)

                products += [self._translate_region_into_product(r)]

        if not products:
            return Constant(False)

        return Disjunction.of(products)


    def _translate_region_into_product(self, region):
        symbols = []
        symbol_id = 0
        symbols_raw = region.symbols
        negations_raw = region.negations
        while symbols_raw != 0:
            if (symbols_raw & 1) == 1:
                if (negations_raw & 1) == 1:
                    symbols += [Negation(Symbol(self.ids_to_symbols[symbol_id]))]
                else:
                    symbols += [Symbol(self.ids_to_symbols[symbol_id])]

            symbols_raw >>= 1
            negations_raw >>= 1
            symbol_id += 1

        return Conjunction.of(symbols)