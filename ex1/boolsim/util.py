def pow2(n):
    return 1 << n

def mask(n):
    return (1 << n) - 1

POPCOUNT_TABLE16 = [0] * 2**16
for i in range(len(POPCOUNT_TABLE16)):
    POPCOUNT_TABLE16[i] = (i & 1) + POPCOUNT_TABLE16[i >> 1]

def popcnt(n):
    return (POPCOUNT_TABLE16[ n        & 0xffff] +
            POPCOUNT_TABLE16[(n >> 16) & 0xffff])

def hamming_distance(lhs, rhs):
    n = lhs ^ rhs
    return (POPCOUNT_TABLE16[ n        & 0xffff] +
            POPCOUNT_TABLE16[(n >> 16) & 0xffff])

def is_pow2(n):
    return ((n & (n-1)) == 0)

class BoolVector:
    def __init__(self, dim, val):
        self.dim = dim
        self.mask = mask(dim)
        self.val = val

    def __getitem__(self, key):
        return (self.val >> key) & 1

    def increment(self):
        self.val = (self.val + 1) & self.mask

    def increment_masked(self, mask):
        self.val = ((self.val | ~mask) + 1) & mask

    def increment_masked_preserve_other(self, mask):
        self.val = (self.val & ~mask) | (((self.val | ~mask) + 1) & mask)

    def __invert__(self):
        return BoolVector(self.dim, ~self.val & self.mask)

    def ones(self):
        return popcnt(self.val)

    def zeroes(self):
        return self.dim - self.ones()

    def copy(self):
        return BoolVector(self.dim, self.val)

def volume2(start, dirs):
    current = BoolVector(dirs.dim, 0)
    increments_left = pow2(dirs.ones())
    while increments_left > 0:
        yield start + current.val
        current.increment_masked(dirs.val)
        increments_left -= 1