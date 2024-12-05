from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
import itertools
from typing import Sequence

from synth.constraints import DoesNotEvaluateTo, DistinctChildren
from .ast import ASTInt, ASTNode, Hole, ASTValue, ASTVar
from .grammar import ProductionRule, Self
from .eval import ASTEvaluator


@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True)
class Grammar:
    terminals: tuple[ProductionRule, ...]
    nonterminals: tuple[ProductionRule, ...]

    def __str__(self):
        return "\n".join([
            "Grammar:",
            *(
                "  " + str(x) for x in self.nonterminals
            ),
            *(
                "  " + str(x) for x in self.terminals
            )
        ])

    def enumerate_bottom_up(self, depth: int, screen: EnumerationFilter) -> Iterable[ASTNode | ASTValue]:
        starting_nonterm = self.nonterminals[0]

        for prod in starting_nonterm.produce:
            for ast in fill_holes_of(prod, depth=depth):
                if screen.is_useful_program(ast):
                    yield ast
                    screen.register_program(ast)


def fill_holes_of(production: ASTNode | Hole, depth: int) -> Iterable[ASTNode | ASTValue]:
    """
    Fill all holes in `production` with all possible productions of their production rules.
    """
    # if we run out of depth, return empty
    if depth <= 0:
        return
    match production:
        case Hole(fill=f) as h if isinstance(f, ProductionRule):
            # replace holes by their definition
            assert isinstance(f, ProductionRule)
            assert isinstance(h, Hole)
            yield from filter(
                h.can_substitute,
                itertools.chain(*(fill_holes_of(val, depth=depth) for val in f.produce))
            )
        case ASTNode() as node:
            hole_ids = node.holes_indices
            holes = node.holes
            
            for fill in itertools.product(*(fill_holes_of(hole, depth=depth - 1) for hole in holes)):
                yield node.replace_children(hole_ids, fill)
        case ASTValue() as val:
            if depth != 1:
                return
            yield val
        case _:
            raise ValueError(f"Unknown hole", production)


@dataclass(frozen=True, slots=True)
class AddNode(ASTNode):
    def __eq__(self, other):
        if isinstance(other, AddNode) and set(other.children) == set(self.children):
            return True
        return super().__eq__(other)

    def replace_children(self, ids: Sequence[int], replacements: Sequence[ASTNode | ASTValue | Hole]) -> ASTNode:
        match tuple(replacements):
            case (lhs, rhs):
                return AddNode('add', (lhs, rhs))
            case (a,):
                AddNode(
                    'add',
                    (a, self.children[1]) if ids[0] == 0 else (self.children[0], a),
                )
            case ():
                return self

    def __hash__(self):
        if self.holes:
            return super().__hash__()
        return hash((self.name, *sorted(self.children)))

    def __lt__(self, other):
        if isinstance(other, ASTNode):
            return (self.name, *self.children) < (other.name, *other.children)




class EnumerationFilter(ABC):
    @abstractmethod
    def is_useful_program(self, ast: ASTNode | ASTValue) -> bool:
        pass

    @abstractmethod
    def register_program(self, ast: ASTNode | ASTValue):
        pass


class EquivalenceScreen(EnumerationFilter):
    generated_programs: set[ASTNode | ASTValue]

    def __init__(self):
        self.generated_programs = set()

    def is_useful_program(self, ast: ASTNode | ASTValue) -> bool:
        return ast not in self.generated_programs

    def register_program(self, ast: ASTNode | ASTValue):
        self.generated_programs.add(ast)


if __name__ == '__main__':
    """
    A   := int | var | `add` A A | `sub` A A
    int := 0 | 1
    var := x | y
    """

    t_int = ProductionRule('int', (
        ASTInt(0),
        ASTInt(1),
    ))
    t_var = ProductionRule('var', (
        ASTVar('x'),
        ASTVar('y'),
    ))

    """
    Siddharth says:
        A = Nonterminal("A")
        t_int = Terminal('int')
        a2int = ProductionRule(A, t_int)
        a2add = ProductionRule(A, ASTNode('add', l=A, r=A))
    """

    evaluator = ASTEvaluator(
        {
            'add': lambda n, vals: vals[0] + vals[1],
            'sub': lambda n, vals: vals[0] - vals[1],
        }
    )
    vars = {'x': 1, 'y': 2}
    C_Nonzero = DoesNotEvaluateTo(0, evaluator, vars)
    #C_Notone = DoesNotEvaluateTo(1, evaluator, vars)

    A = ProductionRule('A', (
        AddNode('add', (Hole(Self, (C_Nonzero,)), Hole(Self, (C_Nonzero,)))),
        ASTNode('sub', (Hole(Self, (C_Nonzero,)), Hole(Self, (C_Nonzero,)))),
        Hole(t_int),
        Hole(t_var),
    ))

    simple_g = Grammar(
        (t_int, t_var),
        (A,),
    )
    print(simple_g)
    print(repr(simple_g))
    screen = EquivalenceScreen()


    print("\ndepth = 1")
    for ast in simple_g.enumerate_bottom_up(depth=1, screen=screen):
        print(ast, end="")
        print(" = ", end="")
        print(evaluator.eval(ast, vars))
    print("\ndepth = 2")
    for ast in simple_g.enumerate_bottom_up(depth=2, screen=screen):
        print(ast, end="")
        print(" = ", end="")
        print(evaluator.eval(ast, vars))
    print("\ndepth = 3")
    for ast in simple_g.enumerate_bottom_up(depth=3, screen=screen):
        print(ast, end="")
        print(" = ", end="")
        print(evaluator.eval(ast, vars))

