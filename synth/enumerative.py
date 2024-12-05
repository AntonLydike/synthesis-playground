from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
import itertools
from collections import defaultdict


from synth.constraints import DoesNotEvaluateTo, DistinctChildren
from synth import ast
from synth.ast import Node, Value, SymmetricNode
from synth.grammar import ProductionRule
from synth.eval import ASTEvaluator
from synth.symbols import Nonterminal


@dataclass(unsafe_hash=True, eq=True, slots=True)
class Grammar:
    start: Nonterminal
    _maps: dict[str, list[ProductionRule]] = field(default_factory=lambda: defaultdict(list), init=False)

    def __iadd__(self, other: ProductionRule):
        self._maps[other.lhs.name].append(other)
        return self

    def __str__(self):
        res = ['Grammar:']
        longest_name = max(len(sym) for sym in self._maps)
        space = ' ' * longest_name
        # collapse rules without constraints together
        for sym, rules in self._maps.items():
            if all(not rule.constraints for rule in rules):
                res.append(f"{sym:<{longest_name}} ::= {' | '.join(str(x.rhs) for x in rules)}")
            else:
                res.append(f'{sym:<{longest_name}} ::= ')
                for rule in rules:
                    constraint_str = ', '.join(str(c) for c in rule.constraints)
                    constr = "" if not rule.constraints else f": {constraint_str}"
                    res.append(f'{space}     {rule.rhs}{constr}')

        return "\n\t".join(res)

    def enumerate_bottom_up(self, depth: int, screen: EnumerationFilter) -> Iterable[Node | Value]:
        for prod in self._maps[self.start.name]:
            for ast in self.perform_substitution(prod, depth=depth):
                if screen.is_useful_program(ast):
                    yield ast
                    screen.register_program(ast)

    def enumerate_forever(self, screen: EnumerationFilter):
        for depth in range(0, 10000):
            yield from self.enumerate_bottom_up(depth, screen)

    def perform_substitution(self, production: ProductionRule | Nonterminal, depth: int) -> Iterable[Node | Value]:
        """
        Fill all holes in `production` with all possible productions of their production rules.
        """
        # if we run out of depth, return empty
        if depth <= 0:
            return

        # If we're given a nonterminal instead of a rule, iterate over all rues of the nonterminal
        # and check against the nonterminals constraints
        if isinstance(production, Nonterminal):
            sym: Nonterminal = production
            for rule in self._maps[sym.name]:
                yield from filter(
                    sym.accepts,
                    self.perform_substitution(rule, depth)
                )
            return

        # specialise on what the rule produces:
        match production.rhs:
            # another nontermial => recurse without reducing depth
            case Nonterminal() as sym:
                # replace symbol by all things that can be produced from that symbol
                # apply constraints
                yield from filter(
                    production.can_substitute,
                    itertools.chain(*(self.perform_substitution(val, depth=depth) for val in self._maps[sym.name]))
                )
            # an ast node => recurse on all children of the AST node that are nonterminals, reducing depth:
            case Node() as node:
                # find all "holes" in the symbol
                hole_ids = node.holes_indices
                holes = node.holes
                # fill them
                for fill in itertools.product(*(self.perform_substitution(hole, depth=depth-1) for hole in holes)):
                    new_node = node.replace_children(hole_ids, fill)
                    # check constraints of production rule
                    if production.can_substitute(new_node):
                        yield new_node
            # a Terminal => return terminal:
            case Value() as val:
                if not production.can_substitute(val):
                    return
                yield val
            # something else => Error:
            case _:
                raise ValueError(f"Unknown hole", production)


class EnumerationFilter(ABC):
    @abstractmethod
    def is_useful_program(self, ast: Node | Value) -> bool:
        pass

    @abstractmethod
    def register_program(self, ast: Node | Value):
        pass


class EquivalenceScreen(EnumerationFilter):
    generated_programs: set[Node | Value]

    def __init__(self):
        self.generated_programs = set()

    def is_useful_program(self, ast: Node | Value) -> bool:
        return ast not in self.generated_programs

    def register_program(self, ast: Node | Value):
        self.generated_programs.add(ast)


if __name__ == '__main__':
    """
    A   := int | var | `add` A A | `sub` A A
    int := 0 | 1
    var := x | y
    """

    evaluator = ASTEvaluator(
        {
            'add': lambda n, vals: vals[0] + vals[1],
            'sub': lambda n, vals: vals[0] - vals[1],
        }
    )
    vars = {'x': 1, 'y': 2}
    C_Nonzero = DoesNotEvaluateTo(0, evaluator, vars)


    val = Nonterminal('val')
    A = Nonterminal('A')

    g = Grammar(A)

    g += ProductionRule(val, ast.Int(0))
    g += ProductionRule(val, ast.Int(1))
    g += ProductionRule(val, ast.Var('x'))
    g += ProductionRule(val, ast.Var('y'))

    g += ProductionRule(A, val)
    g += ProductionRule(
        A,
        SymmetricNode('add', (A + C_Nonzero, A + C_Nonzero)),
        (DistinctChildren(),)
    )
    g += ProductionRule(
        A,
        ast.Node('sub', (A, A + C_Nonzero)),
        (DistinctChildren(),)
    )

    """
    Siddharth says:
        A = Nonterminal("A")
        t_int = Terminal('int')
        a2int = ProductionRule(A, t_int)
        a2add = ProductionRule(A, ASTNode('add', l=A, r=A))
    """
    #C_Notone = DoesNotEvaluateTo(1, evaluator, vars)

    print(g)
    screen = EquivalenceScreen()


    print("\ndepth = 1")
    for ast in g.enumerate_bottom_up(depth=1, screen=screen):
        print(ast, end="")
        print(" = ", end="")
        print(evaluator.eval(ast, vars))
    print("\ndepth = 2")
    for ast in g.enumerate_bottom_up(depth=2, screen=screen):
        print(ast, end="")
        print(" = ", end="")
        print(evaluator.eval(ast, vars))
    print("\ndepth = 3")
    for ast in g.enumerate_bottom_up(depth=3, screen=screen):
        print(ast, end="")
        print(" = ", end="")
        print(evaluator.eval(ast, vars))

