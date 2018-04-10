import sys
import re
import time

from boolsim import *

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

scrambling_ruleset.add_rule('a=b', '(a>b)&(b>a)')

scrambling_ruleset.add_rule('a>b', '!a|b')

scrambling_ruleset.add_rule('a^b', '(a&!b)|(!a&b)')
scrambling_ruleset.add_rule('a=b', '(!a&!b)|(a&b)')

def main():
    start = time.time()

    print(Scrambler(scrambling_ruleset, parse_expression('A^B=C|(A&B)')).step(4).random_expr())

    print(time.time() - start)

if __name__ == '__main__':
    main()