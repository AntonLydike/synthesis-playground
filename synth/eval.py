from dataclasses import dataclass
from typing import Callable, Any

import synth.ast as ast


@dataclass
class ASTEvaluator:
    evals: dict[str, Callable[[ast.Node, tuple[Any, ...]], Any]]

    def eval(self, node: ast.Node | ast.Value, binds: dict[str, Any]) -> ast.Value:
        match node:
            case ast.Var(name):
                return binds[name]
            case ast.Int(val):
                return val
            case ast.String(val):
                return val
            case ast.Value() as val:
                return val
            case ast.Node(name, children):
                return self.evals[name](node, tuple(
                    self.eval(child, binds) for child in children
                ))
