from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from synth.ast import GenerationConstraint, ASTNode, ASTValue
from synth.eval import ASTEvaluator


@dataclass
class DoesNotEvaluateTo(GenerationConstraint):
    """
    Checks that a program does not evaluate to a constant
    """
    val: Any
    eval: ASTEvaluator
    binds: dict[str, Any]

    def is_valid_entry(self, ast: ASTNode | ASTValue):
        return self.eval.eval(ast, self.binds) != self.val


class DistinctChildren(GenerationConstraint):
    """
    Make sure children are pairwise distinct.

    Returns True for ASTValue.
    """
    def is_valid_entry(self, ast: ASTNode | ASTValue):
        if isinstance(ast, ASTValue):
            return True

        for child1 in ast.children:
            for child2 in ast.children:
                if child1 is not child2 and child1 == child2:
                    return False
        return True
