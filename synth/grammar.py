from __future__ import annotations

from dataclasses import dataclass, field

import synth.ast as ast
from synth.symbols import Nonterminal
from synth.constraints import GenerationConstraint


@dataclass(frozen=True, unsafe_hash=True)
class ProductionRule:
    lhs: Nonterminal
    rhs: ast.Value | ast.Node | Nonterminal

    constraints: tuple[GenerationConstraint, ...] = field(default=())

    def __str__(self):
        constraint_str = ', '.join(str(c) for c in self.constraints)
        constr = "" if not self.constraints else f": {constraint_str}"
        return f"{self.lhs} \t:= {self.rhs}{constr}"

    def can_substitute(self, node: ast.Node | ast.Value):
        return all(c.is_valid_entry(node) for c in self.constraints)


