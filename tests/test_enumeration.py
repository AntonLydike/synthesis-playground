from synth.enumerative import *
def test_fill_hole():
    prod = ProductionRule('p', (ASTInt(1), ASTInt(2)))

    assert tuple(fill_holes_of(Hole(prod), depth=1)) == (ASTInt(1), ASTInt(2))


def test_fill_hole_constr():
    eval = ASTEvaluator({})
    constr = DoesNotEvaluateTo(1, eval, {})
    prod = ProductionRule('p', (ASTInt(1), ASTInt(2)))


    assert tuple(fill_holes_of(Hole(prod, (constr,)), depth=1)) == (ASTInt(2),)


def test_fill_nonterm():
    term = ProductionRule('p', (ASTInt(1),))
    nonterm = ProductionRule('A', (
        ASTNode('add', (Hole(term), Hole(term))),
    ))

    assert tuple(fill_holes_of(Hole(nonterm), depth=2)) == (ASTNode('add', (ASTInt(1), ASTInt(1))),)


def test_fill_nonterm_constr():
    eval = ASTEvaluator({'add': lambda _, x: x[0] + x[1]})
    nonzero = DoesNotEvaluateTo(0, eval, {})
    notone = DoesNotEvaluateTo(1, eval, {})


    term = ProductionRule('p', (ASTInt(0),ASTInt(1)))
    nonterm = ProductionRule('A', (
        ASTNode('add', (
            Hole(term, (nonzero,)),
            Hole(term, (notone,)),
        )),
    ))


    assert tuple(fill_holes_of(Hole(nonterm), depth=2)) == (ASTNode('add', (ASTInt(1), ASTInt(0))),)
