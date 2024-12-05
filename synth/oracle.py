from synth import ast

class Oracle:
    def assess(self, candidate: ast.Node | ast.Value):
        raise NotImplementedError()


