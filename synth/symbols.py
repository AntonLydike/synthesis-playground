from dataclasses import dataclass, field
from abc import ABC
from typing import Any


@dataclass(frozen=True, slots=True, eq=True, order=True)
class Nonterminal:
    name: str
    constraints: tuple[Any, ...] = field(default=())

    def __str__(self):
        if not self.constraints:
            return self.name
        return f"{self.name}: {', '.join(map(str, self.constraints))}"

    def __add__(self, other: Any):
        return Nonterminal(self.name, (*self.constraints, other))

    def accepts(self, node: Any):
        return all(c.is_valid_entry(node) for c in self.constraints)
