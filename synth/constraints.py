from __future__ import annotations

import itertools
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

from synth import ast as ast
from synth.eval import ASTEvaluator


@dataclass(unsafe_hash=True, frozen=True)
class GenerationConstraint:
    @abstractmethod
    def is_valid_entry(self, node: ast.Node | ast.Value):
        """
        check if an ast node or value (without holes) is a valid placement candidate here
        """
        raise NotImplementedError()


@dataclass(unsafe_hash=True, frozen=True)
class DoesNotEvaluateTo(GenerationConstraint):
    """
    Checks that a program does not evaluate to a constant
    """
    val: Any
    eval: ASTEvaluator
    binds: dict[str, Any]

    def is_valid_entry(self, node: ast.Node | ast.Value):
        try:
            return self.eval.eval(node, self.binds) != self.val
        except KeyError:
            return True

    def __str__(self):
        return f"≠{self.val}"


@dataclass(unsafe_hash=True, frozen=True)
class DistinctChildren(GenerationConstraint):
    """
    Make sure children are pairwise distinct.

    Returns True for ASTValue.
    """
    def is_valid_entry(self, node: ast.Node | ast.Value):
        if isinstance(node, ast.Value):
            return True

        for a, b in itertools.permutations(node.children, r=2):
            if a == b:
                return False
        return True

    def __str__(self):
        return f"distinct"


@dataclass(unsafe_hash=True, frozen=True)
class Dynamic(GenerationConstraint):
    """
    Checks that at least one of the children refers to an ast.Var.
    """
    def is_valid_entry(self, node: ast.Node | ast.Value):
        match node:
            case ast.Var():
                return True
            case ast.Node(children=children):
                return any(self.is_valid_entry(child) for child in children)
            case _:
                return False

    def __str__(self):
        return "dyn"
