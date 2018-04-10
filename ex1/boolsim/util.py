def pow2(n):
    return 1 << n

def mask(n):
    return (1 << n) - 1

def popcnt(n):
    b = 0
    while n != 0:
        if n & 1:
            b += 1
        n >>= 1
    return b

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