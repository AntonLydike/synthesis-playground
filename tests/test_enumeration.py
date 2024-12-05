from synth.enumerative import *
from synth import ast
def test_subst():
    P = Nonterminal('P')
    g = Grammar(P)
    g += ProductionRule(P, ast.Int(1))
    g += ProductionRule(P, ast.Int(2))

    assert tuple(g.perform_substitution(P, depth=1)) == (ast.Int(1), ast.Int(2))


def test_subst_constr():
    eval = ASTEvaluator({})
    constr = DoesNotEvaluateTo(1, eval, {})

    P = Nonterminal('P')
    g = Grammar(P)
    g += ProductionRule(P, ast.Int(1), (constr,))
    g += ProductionRule(P, ast.Int(2), (constr,))

    assert tuple(g.perform_substitution(P, depth=1)) == (ast.Int(2),)


def test_subst_constr2():
    eval = ASTEvaluator({})
    constr = DoesNotEvaluateTo(1, eval, {})

    P = Nonterminal('P')
    g = Grammar(P)
    g += ProductionRule(P, ast.Int(1))
    g += ProductionRule(P, ast.Int(2))

    assert tuple(g.perform_substitution(P + constr, depth=1)) == (ast.Int(2),)


def test_subst_nested():
    P = Nonterminal('P')
    A = Nonterminal('A')
    g = Grammar(P)
    g += ProductionRule(P, ast.Int(1))
    g += ProductionRule(A, Node('add', (P, P)))

    assert tuple(g.perform_substitution(A, depth=2)) == (Node('add', (ast.Int(1), ast.Int(1))),)


def test_subst_nested_constr():
    eval = ASTEvaluator({'add': lambda _, x: x[0] + x[1]})
    nonzero = DoesNotEvaluateTo(0, eval, {})

    P = Nonterminal('P')
    A = Nonterminal('A')
    g = Grammar(A)
    g += ProductionRule(P, ast.Int(0))
    g += ProductionRule(P, ast.Int(1))
    g += ProductionRule(A, Node('add', (P + nonzero, P)))

    assert tuple(g.perform_substitution(A, depth=2)) == (Node('add', (ast.Int(1), ast.Int(0))),Node('add', (ast.Int(1), ast.Int(1))))
