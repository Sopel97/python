import sys
import re
import time
import random
import itertools
import fileinput

from boolsim import *

def test(expr_str, expected_expr_str):
    expr = parse_expression(expr_str)
    expected_expr = parse_expression(expected_expr_str)
    eval_simplified = expr.try_simplify_by_evaluation(try_lookup_expression)

    full_simplifier = FullSimplifier(full_simplification_ruleset, expr)
    cnf = CnfSimplifier(KarnaughMap, expr).best_expr()
    dnf = DnfSimplifier(KarnaughMap, expr).best_expr()

    print('[Base; Complexity: {0}]: {1}'.format(expr.complexity, expr))
    print('[Eval; Complexity: {0}]: {1}'.format(eval_simplified.complexity, eval_simplified))
    print('[CNF; Complexity: {0}]: {1}'.format(cnf.complexity, cnf))
    cnf2 = Qmc.from_expression(expr).to_cnf()
    print('[CNF2; Complexity: {0}]: {1}'.format(cnf2.complexity, cnf2))
    print('[DNF; Complexity: {0}]: {1}'.format(dnf.complexity, dnf))
    dnf2 = Qmc.from_expression(expr).to_dnf()
    print('[DNF2; Complexity: {0}]: {1}'.format(dnf2.complexity, dnf2))

    step_id = 1
    while not full_simplifier.is_completed:
        full_simplifier.step()
        current_best_expr = full_simplifier.best_expr()
        print('[Step: {0}; Complexity: {1}]: {2}'.format(step_id, current_best_expr.complexity, current_best_expr))
        step_id += 1

    min_expr = full_simplifier.best_expr()
    print('[Min; Complexity: {0}]: {1}'.format(min_expr.complexity, min_expr))

    if not are_equal_by_evaluation(expr, min_expr):
        print('Invalid simplification!')
    elif min_expr.complexity > expected_expr.complexity:
        print('Subpar simplification! Expected [Complexity: {0}; Expr: {1}]'.format(expected_expr.complexity, expected_expr))
    elif min_expr.complexity < expected_expr.complexity:
        print('Expected worse expression! Expected [Complexity: {0}; Expr: {1}]'.format(expected_expr.complexity, expected_expr))

    print('------------------------------------------------------------')

def main():
    start = time.time()

    #print(parse_expression('a|b'))
    #d1 = {}
    #d2 = {}
    #d3 = {}
    #d4 = {}
    #d5 = {}
    #print(parse_expression('A|B').try_match(parse_expression('a&b'), d1))
    #print(parse_expression('A|B').try_match(parse_expression('a|b'), d2))
    #print(parse_expression('A|(C&D^0)').try_match(parse_expression('a|b'), d3))
    #print(parse_expression('!(C&D^0)|!(C&D^0)').try_match(parse_expression('a|a'), d4))
    #print(parse_expression('(C&D^0)|!(C&D^0)').try_match(parse_expression('a|a'), d5))
    #print(d1)
    #print(d2)
    #print(d3)
    #print(d4)
    #print(d5)
    #print(parse_expression(sys.argv[1]).evaluate({'a' : True, 'b' : False, 'c' : False}))
    #p = parse_expression('((C|C)|(C&D^0))|((C|C)|(C&D^0))').get_paths_to_matching_nodes(parse_expression('a|a'))
    #print(p)

    #print(parse_expression('a|b=b').substitute({'a' : 'A&A', 'b' : 'B^B'}))

    '''
    # Used to determine what rules to use to get all possibilities, but
    # respecting symmetry
    # It has to generate exactly 3 expressions.
    # {((c|a)|b), ((a|b)|c), ((b|c)|a)}

    temp_ruleset = Ruleset()

    temp_ruleset.add_rule('a|(b|c)', '(a|b)|c')
    temp_ruleset.add_rule('a|(b|c)', '(c|a)|b')

    all_exprs = {parse_expression('a|(b|c)')}
    for i in range(10):
        new_exprs = set()
        for e in all_exprs:
            for to_match, to_apply in temp_ruleset.permuting_rules:
                new_exprs.update(e.apply_pattern_recursively_to_all(to_match, to_apply))
        all_exprs = new_exprs

    print(all_exprs)
    # '''

    '''
    print(parse_expression('   A A &    \t B   '))
    print(parse_expression('   A &    \t B   '))
    parse_expression('!!!')
    parse_expression('((A&B)')
    parse_expression('A&B)')
    parse_expression('A&')
    parse_expression('&A')
    parse_expression('A_')
    '''

    #expr = parse_expression('(a|b)&((c|d)&(e&f))|(a|e)&((f|d)&(g&f))|(i|b)&((h|d)|(j&f))|p|q')
    #print(len(gather_symbols_from_expr(expr)))
    #print(Qmc(expr).to_dnf())
    #print(KarnaughMap.from_expression(expr).to_dnf())

    #'''
    test('(a|b)&(((c|d)&(e&f))|((c|d)&(e&f)))', '(a|b)&((c|d)&(e&f))')
    test('!a|b', 'a>b')
    test('!!!!X', 'X')
    test('!!!!!!!X', '!X')
    test('a|1&1', '1')
    test('(a>b)&(b>a)', 'A=B')
    test('((A|B|C)&(!(D|E)))|((A|B|C)&(D|E))', 'A|B|C')
    test('a|(!a&b)', 'A|B')
    test('a&(!a|b)', 'A&B')
    test('(X&Z)|(Z&(!X|(X&Y)))', 'Z')
    test('!(A|B)&!(C|D|E)|!(A|B)', '!(A|B)')
    test('!(!A&!B|!C|!D|!E)', '(A|B)&C&D&E')
    test('(A&B)|((A&B)&C)|((A&B)&(C&D))|((A&B)&(C&D&E))|((A&B)&(C&D&E&F))', 'A&B')
    test('(!(!A&!B|!C|!D|!E))=((A|B)&C&(D&E))', '1')
    test('(A&B&!C&!D)|(A&B&!C&D)|(A&!B&!C&D)|(A&B&C&D)|(A&!B&C&D)|(A&B&C&!D)|(A&!B&C&!D)', 'A&(B|C|D)')
    test('A&(B|C|D)', 'A&(B|C|D)')
    test('!a|!d', '!(a&d)')
    test('((a&c)|b)|(a&c)', '(a&c)|b')
    test('(A&B&!C&!D)|(!B&C&!D)|(A&!C&D)|(A&!B&!C)|(B&C&!D)', '!(C&D)&(A|C)') # follows nicely from karnaugh -> product of sums
    test('(!(A^B)&!(C|(A&B)))|((A^B)&(C|(A&B)))|(!(A^B)&!(C|(A&B)))|((A^B)&(C|(A&B)))|(!(A^B)&!(C|(A&B)))|((A^B)&(C|(A&B)))|(!(A^B)&!(C|(A&B)))|((A^B)&(C|(A&B)))', 'A^B=C|(A&B)')
    test('(((A^B<=>C|(A&B))|(A^B<=>C|(A&B)))&((A^B<=>C|(A&B))|(A^B<=>C|(A&B))))|(((A^B<=>C|(A&B))|(A^B<=>C|(A&B)))&((A^B<=>C|(A&B))|(A^B<=>C|(A&B))))', 'A^B=C|(A&B)')
    test('(A^B=>(C|(A&B)|(A&B))&(C|(A&B)|(A&B)))&((C|(A&B)|(A&B))&(C|(A&B)|(A&B))=>A^B)', 'A^B=C|(A&B)')
    test('!((A^B=>C|(A&B))&(C|(A&B)=>A^B)=>!((A^B=>(C|A)&(C|B))&(C|(A&B)=>A^B)))', 'A^B=C|(A&B)')
    test('(!a&((b|c)&d))|(!((c|b)&d)&a)', 'a^(b|c&d)')
    test('A&B|C&D|E&F|G&H', 'A&B|C&D|E&F|G&H')
    test('A1A1&B00B2', 'A1A1&B00B2')
    # '''

    #print(CnfSimplifier(parse_expression('(!((a|b)&(((c|d)&(e&f))|((c|d)&(e&f))))&!(!A&!B|!C|!D|!E))|(((a|b)&(((c|d)&(e&f))|((c|d)&(e&f))))&(!A&!B|!C|!D|!E))')).best_expr())

    #print(Scrambler(scrambling_ruleset, parse_expression('A^B=C|(A&B)')).step(3).random_expr())

    '''
    for r in full_simplification_ruleset.reducing_rules:
        if not are_equal_by_evaluation(r[0], r[1]):
            print(str(r[0]) + ' ' + str(r[1]) + ' wrong rule')

    i = 0
    for expr in expression_lookup_tables[2]:
        if bool_array_to_int(evall(expr, ['a', 'b'])) != i:
            print('wrong 2d: ' + str(i))

        i += 1

    i = 0
    for expr in expression_lookup_tables[3]:
        if bool_array_to_int(evall(expr, ['a', 'b', 'c'])) != i:
            print('wrong 3d: ' + str(i))

        i += 1

    i = 0
    perms = [
        ['a', 'b', 'c'],
        ['a', 'c', 'b'],
        ['c', 'a', 'b'],
        ['c', 'b', 'a'],
        ['b', 'a', 'c'],
        ['b', 'c', 'a']
    ]
    for expr in expression_lookup_tables[3]:
        ids = [bool_array_to_int(evall(expr, perm)) for perm in perms]
        es = [expression_lookup_tables[3][bool_array_to_int(evall(expr, perm))] for perm in perms]

        i += 1

        if len({e.complexity for e in es}) == 1:
            continue

        print(i-1)
        print([e.complexity for e in es])
        print([str(e) for e in es])
        print('----------------------------')
    # '''

    print(time.time() - start)

def bool_array_to_int(arr):
    i = 0
    for e in reversed(arr):
        i <<= 1
        i += e
    return i

def evall(expr, ids_to_symbols):
    dim = len(ids_to_symbols)
    return [expr.evaluate(symbol_dict_from_index(ids_to_symbols, BoolVector(dim, i))) for i in range(pow2(dim))]



if __name__ == '__main__':
    main()

    #print(bool_array_to_int(evall(parse_expression('a^b=c|(a&b)'), ['a', 'b', 'c'])))
