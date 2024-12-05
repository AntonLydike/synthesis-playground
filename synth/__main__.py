import time
from abc import abstractmethod, ABC
import math
from dataclasses import dataclass

from synth import ast

from typing import TypeVar, Generic, Literal, Any

from synth.constraints import DoesNotEvaluateTo, DistinctChildren, Dynamic
from synth.enumerative import Grammar, EquivalenceScreen
from synth.eval import ASTEvaluator
from synth.grammar import ProductionRule
from synth.symbols import Nonterminal

Feedback = TypeVar("Feedback")
Input = TypeVar("Input")


@dataclass
class SynthesisContext:
    grammar: Grammar
    evaluator: ASTEvaluator
    variables: tuple[str, ...]


class Guesser(Generic[Feedback, Input], ABC):
    def __init__(self, inp: Input, ctx: SynthesisContext):
        self.ctx = ctx

    @abstractmethod
    def generate_guess(self) -> ast.Node | ast.Value:
        raise NotImplementedError()

    @abstractmethod
    def feedback(self, guess: ast.Node | ast.Value, feedback: Feedback):
        raise NotImplementedError()


class Oracle(Generic[Feedback, Input], ABC):
    def __init__(self, inp: Input, ctx: SynthesisContext):
        self.ctx = ctx

    @abstractmethod
    def evaluate(self, guess: ast.Node | ast.Value) -> Literal[True] | Feedback:
        raise NotImplementedError()


class InOutExampleOracle(Oracle[bool, list[tuple[dict[str, Any], Any]]]):
    def __init__(self, inp: list[tuple[Any, Any]], ctx: SynthesisContext):
        super().__init__(inp, ctx)
        self.examples = inp

    def evaluate(self, guess: ast.Node | ast.Value) -> bool:
        for inputs, output in self.examples:
            if self.ctx.evaluator.eval(guess, inputs) != output:
                return False
        return True


class EnumerativeGuesser(Guesser[bool, Any]):
    def __init__(self, inp: Any, ctx: SynthesisContext):
        super().__init__(inp, ctx)

        self.enum = ctx.grammar.enumerate_forever(EquivalenceScreen())

    def generate_guess(self) -> ast.Node | ast.Value:
        return next(self.enum)

    def feedback(self, guess: ast.Node | ast.Value, feedback: Feedback):
        pass


@dataclass
class Synthesis(Generic[Feedback, Input]):
    guesser: Guesser[Feedback, Input]
    oracle: Oracle[Feedback, Input]

    timeout: float

    def run(self) -> ast.Node | ast.Value | None:
        print("running synthesis on grammar:")
        print(self.guesser.ctx.grammar)
        print("with in-out examples:")
        for inp, out in self.oracle.examples:
            print(f"  {inp} -> {out}")

        start = time.time()
        # until timeout:
        while start + self.timeout > time.time():
            # generate guess
            guess = self.guesser.generate_guess()
            # evaluate
            res = self.oracle.evaluate(guess)
            # if it works:
            if res is True:
                # return success
                print(f"correct guess: {guess}")
            else:
                #print(f"wrong guess: {guess}")
                # provide feedback
                self.guesser.feedback(guess, res)


eval = ASTEvaluator(
    {
        'add': lambda _, x: x[0] + x[1],
        'sub': lambda _, x: x[0] - x[1],
        'mul': lambda _, x: x[0] * x[1],
        'div': lambda _, x: x[0] / x[1],
        'floordiv': lambda _, x: x[0] // x[1],
        'shl': lambda _, x: x[0] << x[1],
        'shr': lambda _, x: x[0] >> x[1],
        'pow': lambda _, x: x[0] ** x[1],
        'ln': lambda _, x: math.log(x[0]),
        'exp': lambda _, x: math.exp(x[0]),
        'lt': lambda _, x: int(x[0] < x[1]),
        'ge': lambda _, x: int(x[0] >= x[1]),
        'ite': lambda _, x: x[1] if x[0] else x[2],
    }
)
vars = ('x', 'y')

A = Nonterminal("A")
val = Nonterminal("val")
G = Grammar(A)

nonzero = DoesNotEvaluateTo(0, eval, {})
notone = DoesNotEvaluateTo(1, eval, {})

# add vars
for var in vars:
    G += ProductionRule(val, ast.Var(var))

# add integers
for int_val in (0,1,-1):
    G += ProductionRule(val, ast.Int(int_val))

# add functions
G += ProductionRule(A, val)
G += ProductionRule(A, ast.SymmetricNode('add', (A + nonzero, A + nonzero)), (DistinctChildren(), Dynamic()))
G += ProductionRule(A, ast.SymmetricNode('mul', (A + notone + nonzero, A + notone + nonzero)), (Dynamic(),))
G += ProductionRule(A, ast.Node('sub', (A, A + nonzero)), (DistinctChildren(), Dynamic()))
G += ProductionRule(A, ast.Node('ite', (A, A, A)), (Dynamic(),))

ctx = SynthesisContext(
    G,
    eval,
    vars,
)

inputs = [
    ({'x': 0, 'y': 1}, -1),
    ({'x': 4, 'y': 1}, 3),
    ({'x': 1, 'y': 4}, 3),
    ({'x': 2, 'y': 2}, 3),
]

synth = Synthesis(
    guesser=EnumerativeGuesser(inputs, ctx),
    oracle=InOutExampleOracle(inputs, ctx),
    timeout=.5,
)

synth.run()
