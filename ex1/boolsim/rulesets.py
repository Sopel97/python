from .parser import *

class RuleType:
    Permuting = 1
    Reducing = 2
    Any = Permuting | Reducing

class Ruleset:
    def __init__(self):
        self._reducing_rules = []
        self._permuting_rules = []

    def add_rule(self, to_match, to_apply, add_reverse=False, only_if=RuleType.Any):
        expr_to_match = parse_expression(to_match)
        expr_to_apply = parse_expression(to_apply)

        self._add_rule(expr_to_match, expr_to_apply, only_if)
        if add_reverse:
            self._add_rule(expr_to_apply, expr_to_match, only_if)

    def _add_rule(self, to_match, to_apply, only_if):
        if only_if & RuleType.Permuting and to_apply.complexity >= to_match.complexity:
            self._permuting_rules += [(to_match, to_apply)]
        elif only_if & RuleType.Reducing and to_apply.complexity < to_match.complexity:
            self._reducing_rules += [(to_match, to_apply)]

    @property
    def reducing_rules(self):
        return self._reducing_rules

    @property
    def permuting_rules(self):
        return self._permuting_rules

full_simplification_ruleset = Ruleset()
# Some rules can be disabled due to methods employed in other
# parts of the simplification process being their superset.
# Some decisions are just trying out other heuristics, and
# may not be better in every case.
# Should be altered carefully, and in consideration
# with the whole simplification process.

# These rules are not needed if simplification (of subexpressions)
# by evaluation is used.
# Removing them can speed up the simplification almost twice.
'''
full_simplification_ruleset.add_rule('!0', '1')
full_simplification_ruleset.add_rule('!1', '0')

full_simplification_ruleset.add_rule('a|0', 'a')
full_simplification_ruleset.add_rule('a|1', '1')
full_simplification_ruleset.add_rule('a&0', '0')
full_simplification_ruleset.add_rule('a&1', 'a')
full_simplification_ruleset.add_rule('a^0', 'a')
full_simplification_ruleset.add_rule('a^1', '!a')
full_simplification_ruleset.add_rule('a=0', '!a')
full_simplification_ruleset.add_rule('a=1', 'a')
full_simplification_ruleset.add_rule('a>0', '!a')
full_simplification_ruleset.add_rule('a>1', '1')

full_simplification_ruleset.add_rule('a&!a', '0')
full_simplification_ruleset.add_rule('a|!a', '1')
full_simplification_ruleset.add_rule('a^!a', '1')
full_simplification_ruleset.add_rule('a>!a', '!a')
full_simplification_ruleset.add_rule('a=!a', '0')

full_simplification_ruleset.add_rule('a|a', 'a')
full_simplification_ruleset.add_rule('a&a', 'a')
full_simplification_ruleset.add_rule('a^a', '0')
full_simplification_ruleset.add_rule('a=a', '1')
full_simplification_ruleset.add_rule('a>a', '1')
# '''
# up to here

# These rules are not needed because symmetry is accounted for
# in the try_match method of (symmetric) binary operator
# and expression (that is to be captured by a symbol)
# equality is checked with truth table.
# So it requires add_if_no_conflict to check equality with
# truth tables, and the SymmetricBinaryOperator to branch
# on try_match.
# Doing it in try_match is more performant because
# it only applies symmetry to places where it matters for
# later simplification.
# There may be some problems in long CNF or DNF forms,
# because the first level won't permute as much. It could
# probably be solved by adding more rules of type a&(b&c)
# instead of direct symmetry ones, though. To be tested.
'''
full_simplification_ruleset.add_rule('a&b', 'b&a')
full_simplification_ruleset.add_rule('a|b', 'b|a')
full_simplification_ruleset.add_rule('a^b', 'b^a')
full_simplification_ruleset.add_rule('a=b', 'b=a')
# '''
# up to here

# Having b&a instead of a&b (for each rule) turns out much better
# in profiling for some reason.
# Though using (c&a)&b (take conjuntion of bordering expression) may
# be better for overall simplification quality, because
# it would allow those expressions to get near each other (but it remains untested).
# Probably it would be the best to have both variants, but it
# would slow the simplification. Remains to be tested.
full_simplification_ruleset.add_rule('a&(b&c)', '(a&b)&c')
full_simplification_ruleset.add_rule('a|(b|c)', '(a|b)|c')
full_simplification_ruleset.add_rule('a^(b^c)', '(a^b)^c')
full_simplification_ruleset.add_rule('a=(b=c)', '(a=b)=c')

full_simplification_ruleset.add_rule('a=(b^c)', '(a^b)=c')

# The following rules have to be included as a replacement
# for lacking symmetry rules. (otherwise sequences of
# symmetrical operations never get scrambled enough)
full_simplification_ruleset.add_rule('a&(b&c)', '(c&a)&b')
full_simplification_ruleset.add_rule('a|(b|c)', '(c|a)|b')
full_simplification_ruleset.add_rule('a^(b^c)', '(c^a)^b')
full_simplification_ruleset.add_rule('a=(b=c)', '(c=a)=b')

# These may not be necessary, also they worsen runtime by ~30x,
# possibly due to heavy use of DNF and CNF
'''
full_simplification_ruleset.add_rule('a&(b|c)', '(a&b)|(a&c)')
full_simplification_ruleset.add_rule('a|(b&c)', '(a|b)&(a|c)')
# '''

# some are added with reverses, becuase depending on depth penalty
# for complexity they may be reducing the other way
full_simplification_ruleset.add_rule('(a&b)|(a&c)', 'a&(b|c)', add_reverse=True, only_if=RuleType.Reducing)
full_simplification_ruleset.add_rule('(a|b)&(a|c)', 'a|(b&c)', add_reverse=True, only_if=RuleType.Reducing)
full_simplification_ruleset.add_rule('a|(a&b)', 'a')
full_simplification_ruleset.add_rule('a&(a|b)', 'a')
full_simplification_ruleset.add_rule('a|(!a&b)', 'a|b')
full_simplification_ruleset.add_rule('a&(!a|b)', 'a&b')

full_simplification_ruleset.add_rule('a^(a&b)', '!b&a')
full_simplification_ruleset.add_rule('a=(a&b)', 'b|!a')

full_simplification_ruleset.add_rule('!!a', 'a')
full_simplification_ruleset.add_rule('!a&!b', '!(a|b)', add_reverse=True)
full_simplification_ruleset.add_rule('!a|!b', '!(a&b)', add_reverse=True)

full_simplification_ruleset.add_rule('(a>b)&(b>a)', 'a=b')

full_simplification_ruleset.add_rule('a>b', '!a|b', add_reverse=True)
full_simplification_ruleset.add_rule('a=b', '!a^b', add_reverse=True, only_if=RuleType.Reducing)
full_simplification_ruleset.add_rule('a^b', '!a=b', add_reverse=True, only_if=RuleType.Reducing)

full_simplification_ruleset.add_rule('(a&b)>(a&c)', '(a&b)>c')
full_simplification_ruleset.add_rule('(a&b)=(a&c)', 'a>(b=c)')
full_simplification_ruleset.add_rule('(a&b)^(a&c)', 'a&(b^c)')

full_simplification_ruleset.add_rule('a^b', '(a&!b)|(!a&b)', add_reverse=True, only_if=RuleType.Reducing)
full_simplification_ruleset.add_rule('a=b', '(!a&!b)|(a&b)', add_reverse=True, only_if=RuleType.Reducing)

full_simplification_ruleset.add_rule('a^b', '(!a|!b)&(a|b)', add_reverse=True, only_if=RuleType.Reducing)
full_simplification_ruleset.add_rule('a=b', '(a|!b)&(!a|b)', add_reverse=True, only_if=RuleType.Reducing)

# No idea how to prove these by only symbolic transformations.
# But they are true and may be helpful.
# Currently done by LUT
'''
full_simplification_ruleset.add_rule('(B&A)|C<=>B^A', '(B|A<=>C)&!(B&A)', add_reverse=True)
full_simplification_ruleset.add_rule('C|A|B=>C&(A^B)', 'C|(A&B)<=>A^B', add_reverse=True)
'''

scrambling_ruleset = Ruleset()

scrambling_ruleset.add_rule('a', 'a|0')
scrambling_ruleset.add_rule('a', 'a&1')
scrambling_ruleset.add_rule('a', 'a^0')
scrambling_ruleset.add_rule('!a', 'a^1')
scrambling_ruleset.add_rule('!a', 'a=0')
scrambling_ruleset.add_rule('a', 'a=1')
scrambling_ruleset.add_rule('!a', 'a>0')

scrambling_ruleset.add_rule('!a', 'a>!a')

#scrambling_ruleset.add_rule('a', 'a|a')
#scrambling_ruleset.add_rule('a', 'a&a')

scrambling_ruleset.add_rule('a&b', 'b&a')
scrambling_ruleset.add_rule('a|b', 'b|a')
scrambling_ruleset.add_rule('a^b', 'b^a')
scrambling_ruleset.add_rule('a=b', 'b=a')

scrambling_ruleset.add_rule('a&(b&c)', '(b&a)&c')
scrambling_ruleset.add_rule('a|(b|c)', '(b|a)|c')
scrambling_ruleset.add_rule('a^(b^c)', '(b^a)^c')
scrambling_ruleset.add_rule('a=(b=c)', '(b=a)=c')

scrambling_ruleset.add_rule('a&(b|c)', '(a&b)|(a&c)')
scrambling_ruleset.add_rule('a|(b&c)', '(a|b)&(a|c)')

scrambling_ruleset.add_rule('a', '!!a')
scrambling_ruleset.add_rule('!(a|b)', '!a&!b')
scrambling_ruleset.add_rule('!(a&b)', '!a|!b')

scrambling_ruleset.add_rule('!b&a', 'a^(a&b)')
scrambling_ruleset.add_rule('b|!a', 'a=(a&b)')

scrambling_ruleset.add_rule('a=b', '(a>b)&(b>a)')

scrambling_ruleset.add_rule('a>b', '!a|b')
scrambling_ruleset.add_rule('a=b', '!a^b')
scrambling_ruleset.add_rule('a^b', '!a=b')

scrambling_ruleset.add_rule('a^b', '(a&!b)|(!a&b)')
scrambling_ruleset.add_rule('a^b', '(!a|!b)&(a|b)')
scrambling_ruleset.add_rule('a=b', '(!a&!b)|(a&b)')
scrambling_ruleset.add_rule('a=b', '(a|!b)&(!a|b)')

scrambling_ruleset.add_rule('(a&b)>c', '(a&b)>(a&c)')
scrambling_ruleset.add_rule('a>(b=c)', '(a&b)=(a&c)')
scrambling_ruleset.add_rule('a&(b^c)', '(a&b)^(a&c)')

scrambling_ruleset.add_rule('a|b', 'a|(!a&b)')
scrambling_ruleset.add_rule('a&b', 'a&(!a|b)')