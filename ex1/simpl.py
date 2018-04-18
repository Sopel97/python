import sys
import re
import time
import random
import argparse

from boolsim import *

def verbose_callback(msg):
    print(msg)

def full(args):
    #print('\nOriginal: ' + str(args.expr))
    #print(parse_expression(args.expr).complexity)
    simplifier = FullSimplifier(
        full_simplification_ruleset,
        parse_expression(args.expr),
        args.c,
        args.m,
        args.q,
        args.p,
        verbose_callback if args.v else None
        )
    if args.s == -1:
        simplifier.step_until_done()
    else:
        for i in range(args.s):
            simplifier.step()

    print(simplifier.best_expr())
    #print(simplifier.best_expr().complexity)

def select_algo(s):
    return {
        'karnaugh' : KarnaughMap,
        'quine' : Qmc
    }[s]

def cnf(args):
    print(CnfSimplifier(select_algo(args.a), parse_expression(args.expr)).best_expr())

def dnf(args):
    print(DnfSimplifier(select_algo(args.a), parse_expression(args.expr)).best_expr())

def scramble(args):
    print(Scrambler(scrambling_ruleset, parse_expression(args.expr), args.q).step(args.s).random_expr())

def complexity(args):
    print(parse_expression(args.expr).complexity)

def main():
    #start = time.time()

    parser = argparse.ArgumentParser(prog='PROG')
    subparsers = parser.add_subparsers(help='The type of simplification')

    parser_full = subparsers.add_parser('full', help='Try reduce the expression using all implemented methods (CNF, DNF, evaluation, lookup tables, term rewriting).', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_full.add_argument('-p', type=int, default=3, help='number of permuting steps in one simplification step')
    parser_full.add_argument('-c', type=float, default=2.5, help='early pruning of expressions that are much worse than others')
    parser_full.add_argument('-m', type=int, default=10, help='expressions with complexity less than this won\'t be pruned early')
    parser_full.add_argument('-q', type=int, default=8, help='max number of expressions that qualify to the next step')
    parser_full.add_argument('-s', type=int, default=-1, help='max number of steps to execute')
    parser_full.add_argument('-v', action='store_true', help='adds trace of the simplification process to the output')
    parser_full.add_argument('expr', type=str, help='expression to simplify')
    parser_full.set_defaults(func=full)

    parser_cnf = subparsers.add_parser('cnf', help='Reduces the expression to minimal CNF form (Conjunctive Normal Form)')
    parser_cnf.add_argument('-a', type=str, default='karnaugh', choices=['karnaugh', 'quine'], help='max number of steps to execute')
    parser_cnf.add_argument('expr', type=str, help='expression to simplify')
    parser_cnf.set_defaults(func=cnf)

    parser_dnf = subparsers.add_parser('dnf', help='Reduces the expression to minimal DNF form (Disjunctive Normal Form)')
    parser_dnf.add_argument('-a', type=str, default='karnaugh', choices=['karnaugh', 'quine'], help='max number of steps to execute')
    parser_dnf.add_argument('expr', type=str, help='expression to simplify')
    parser_dnf.set_defaults(func=dnf)

    parser_comp = subparsers.add_parser('complexity', help='Computes complexity of the expression (as used in program\'s heuristic')
    parser_comp.add_argument('expr', type=str, help='expression to simplify')
    parser_comp.set_defaults(func=complexity)

    parser_scramble = subparsers.add_parser('scramble', help='Scrambles the expression, produces a more complex one. Doesn\'t add variables.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_scramble.add_argument('-s', type=int, default=3, help='number of steps')
    parser_scramble.add_argument('-q', type=int, default=16, help='max number of expressions that qualify to the next step (taken at random)')
    parser_scramble.add_argument('expr', type=str, help='expression to scramble')
    parser_scramble.set_defaults(func=scramble)
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    else:
        args = parser.parse_args()
        args.func(args)

    #print(time.time() - start)

if __name__ == '__main__':
    main()