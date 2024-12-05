from dataclasses import dataclass
from typing import Callable, Any

from .ast import ASTNode, ASTValue, ASTVar, ASTInt, ASTString


@dataclass
class ASTEvaluator:
    evals: dict[str, Callable[[ASTNode, tuple[Any, ...]], Any]]

    def eval(self, node: ASTNode | ASTValue, binds: dict[str, Any]) -> ASTValue:
        match node:
            case ASTVar(name):
                return binds[name]
            case ASTInt(val):
                return val
            case ASTString(val):
                return val
            case ASTValue() as val:
                return val
            case ASTNode(name, children):
                return self.evals[name](node, tuple(
                    self.eval(child, binds) for child in children
                ))
