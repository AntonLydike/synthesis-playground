from dataclasses import dataclass
from typing import Literal
from .ast import ASTNode, ASTValue, Hole
from collections.abc import Iterable

Self = object()



@dataclass
class Terminal:
    name: str

@dataclass
class Nonterminal:
    name: str


class ProductionRule:
    name: str
    produce: tuple[ASTValue | ASTNode | Hole, ...]

    def __init__(self, name: str, produce: Iterable[ASTNode | ASTValue | Hole, ...]):
        self.name = name
        self.produce = tuple(
            _replace_self_in_prod_rules(self, rule) for rule in produce
        )

    def __hash__(self):
        return hash((self.name, self.produce))

    def __eq__(self, value):
        if not isinstance(value, ProductionRule):
            return False
        return value.name == self.name and value.produce == self.produce        

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={repr(self.name)}, produce={repr(self.produce)})"

    def __str__(self):
        repls = []
        for r in self.produce:
            match r:
                case Hole(p) if isinstance(p, ProductionRule):
                    repls.append(p.name)
                case Hole() as hole:
                    repls.append(str(hole))
                case ASTNode() as node:
                    repls.append(
                        node.to_string(lambda h: h.fill.name if isinstance(h.fill, ProductionRule) else "🕳")
                    )
                case ASTValue() as val:
                    repls.append(str(val))
                case val:
                    raise ValueError("Unknown value in production rules:", val)
        return f"{self.name} → {' | '.join(repls)}"


def _replace_self_in_prod_rules(self: ProductionRule, rule: ASTNode | ASTValue | Hole) -> ASTNode | ASTValue | Hole:
    match rule:
        case Hole(fill=x, constraints=c) if x is Self:
            return Hole(self, c)
        case ASTNode(name, children):
            return type(rule)(
                name,
                tuple(_replace_self_in_prod_rules(self, child) for child in children)
            )
        case _:
            return rule
