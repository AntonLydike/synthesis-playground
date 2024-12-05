from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Callable
from .ordered import Ordered


@dataclass(frozen=True, slots=True, eq=True, unsafe_hash=True)
class ASTNode(Ordered):
    name: str
    children: tuple[ASTNode | ASTValue | Hole, ...]

    @property
    def holes_indices(self) -> tuple[int, ...]:
        """
        Tuple of indices indicating which children of this node are holes.
        """
        return tuple(
            idx for idx, e in enumerate(self.children) if isinstance(e, Hole)
        )
    
    @property
    def holes(self) -> tuple[Hole, ...]:
        """
        All children who are Holes of this AST Node
        """
        return tuple(
            c for c in self.children if isinstance(c, Hole)
        )

    def replace_children(self, ids: Sequence[int], replacements: Sequence[ASTNode | ASTValue | Hole]) -> ASTNode:
        """
        Clones the ASTNode, applying replacements.

        `ids` is a list of indices of children which are to be replaced.

        `replacements` is a list of ASTNodes or Holes by which the children identified by `ids` are replaced.

        The child identified by the i-th index in `ids`, is replaced with the i-th element in replacements.
        """
        assert len(ids) == len(replacements)
        repl = iter(replacements)
        id_set = set(ids)
    
        return ASTNode(
            self.name,
            tuple(c if i not in id_set else next(repl) for i, c in enumerate(self.children))
        )

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self, hole_mapper: Callable[[Hole], str] | str = "🕳") -> str:
        kids = []
        for c in self.children:
            match c:
                case Hole() as h:
                    kids.append(hole_mapper if isinstance(hole_mapper, str) else hole_mapper(h))
                case ASTNode() as node:
                    kids.append(str(node))
                case ASTValue() as val:
                    kids.append(str(val))
                case v:
                    raise ValueError("Unknown value in children", v)
        
        return f"{self.name}({' '.join(kids)})"

    def __lt__(self, other):
        if isinstance(other, ASTNode):
            return (self.name, *self.children) < (other.name, *other.children)

    def key(self):
        return tuple((self.name, *(x.key() for x in self.children)))


@dataclass(frozen=True, slots=True, eq=True, unsafe_hash=True)
class ASTValue(Ordered, ABC):
    pass


@dataclass(frozen=True, slots=True, eq=True, unsafe_hash=True)
class ASTInt(ASTValue):
    val: int

    def __str__(self):
        return str(self.val)

    def key(self):
        return str(self.val),


@dataclass(frozen=True, slots=True, eq=True, unsafe_hash=True)
class ASTString(ASTValue):
    val: str

    def __str__(self):
        return repr(self.val)

    def key(self):
        return self.val,


@dataclass(frozen=True, slots=True, eq=True, unsafe_hash=True)
class ASTVar(ASTValue):
    name: str

    def __str__(self):
        return self.name

    def key(self):
        return self.name,



class GenerationConstraint:
    @abstractmethod
    def is_valid_entry(self, ast: ASTNode | ASTValue):
        """
        check if an ast node or value (without holes) is a valid placement candidate here
        """
        raise NotImplementedError()


@dataclass(frozen=True, slots=True, unsafe_hash=True, eq=True)
class Hole(Ordered):
    fill: Any

    constraints: tuple[GenerationConstraint, ...] = field(default=())

    def __str__(self) -> str:
        return str(self.fill)

    def key(self):
        return str(self.fill),

    def can_substitute(self, ast: ASTNode | ASTValue):
        return all(c.is_valid_entry(ast) for c in self.constraints)