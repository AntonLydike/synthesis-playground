from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
from typing import Sequence

from synth.ordered import Ordered
from synth.symbols import Nonterminal


@dataclass(frozen=True, slots=True, unsafe_hash=True)
class Node(Ordered):
    name: str
    children: tuple[Node | Value | Nonterminal, ...]

    @property
    def holes_indices(self) -> tuple[int, ...]:
        """
        Tuple of indices indicating which children of this node are holes.
        """
        return tuple(
            idx for idx, e in enumerate(self.children) if isinstance(e, Nonterminal)
        )
    
    @property
    def holes(self) -> tuple[Nonterminal, ...]:
        """
        All children who are Holes of this AST Node
        """
        return tuple(
            c for c in self.children if isinstance(c, Nonterminal)
        )

    def replace_children(self, ids: Sequence[int], replacements: Sequence[Node | Value | Nonterminal]) -> Node:
        """
        Clones the ASTNode, applying replacements.

        `ids` is a list of indices of children which are to be replaced.

        `replacements` is a list of ASTNodes or Holes by which the children identified by `ids` are replaced.

        The child identified by the i-th index in `ids`, is replaced with the i-th element in replacements.
        """
        assert len(ids) == len(replacements)
        repl = iter(replacements)
        id_set = set(ids)
    
        return Node(
            self.name,
            tuple(c if i not in id_set else next(repl) for i, c in enumerate(self.children))
        )

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        kids = []
        for c in self.children:
            match c:
                case Node() as node:
                    kids.append(str(node))
                case Value() as val:
                    kids.append(str(val))
                case Nonterminal() as sym:
                    kids.append(str(sym))
                case v:
                    raise ValueError("Unknown value in children", v)
        
        return f"{self.name}({', '.join(kids)})"

    def key(self):
        return tuple((self.name, *(x.key() for x in self.children)))


@dataclass(frozen=True, slots=True, eq=True, unsafe_hash=True)
class Value(Ordered, ABC):
    pass


@dataclass(frozen=True, slots=True, eq=True, unsafe_hash=True)
class Int(Value):
    val: int

    def __str__(self):
        return str(self.val)

    def key(self):
        return str(self.val),


@dataclass(frozen=True, slots=True, eq=True, unsafe_hash=True)
class String(Value):
    val: str

    def __str__(self):
        return repr(self.val)

    def key(self):
        return self.val,


@dataclass(frozen=True, slots=True, eq=True, unsafe_hash=True)
class Var(Value):
    name: str

    def __str__(self):
        return self.name

    def key(self):
        return self.name,


@dataclass(frozen=True, slots=True)
class SymmetricNode(Node):
    def __eq__(self, other):
        if isinstance(other, SymmetricNode) and set(other.children) == set(self.children):
            return True
        return Node.__eq__(self, other)

    def replace_children(self, ids: Sequence[int], replacements: Sequence[Node | Value | Nonterminal]) -> Node:
        match tuple(replacements):
            case (lhs, rhs):
                return SymmetricNode(self.name, (lhs, rhs))
            case (a,):
                SymmetricNode(
                    self.name,
                    (a, self.children[1]) if ids[0] == 0 else (self.children[0], a),
                )
            case ():
                return self

    def __hash__(self):
        if self.holes:
            return super().__hash__()
        return hash((self.name, *sorted(self.children)))

    def __lt__(self, other):
        if isinstance(other, Node):
            return (self.name, *self.children) < (other.name, *other.children)
