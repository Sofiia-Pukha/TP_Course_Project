"""Приклади з каталогу examples: інтерпретатор і семантичний терм мають давати однаковий результат."""
import unittest

import sipl
from sipl.evaluator import evaluate
from sipl.interpreter import run
from sipl.semantics import build_term
from .helpers import read_example

# (файл, початковий стан, очікувані значення змінних)
CASES = [
    ("power.sipl", {"X": 5, "Y": 2}, {"R": 25}),
    ("power.sipl", {"X": 2, "Y": 10}, {"R": 1024}),
    ("power.sipl", {"X": 3, "Y": 0}, {"R": 1}),
    ("div.sipl", {"X": 7, "Y": 4}, {"R": 1}),
    ("div.sipl", {"X": 9, "Y": 3}, {"R": 3}),
    ("div.sipl", {"X": 2, "Y": 5}, {"R": 0}),
    ("sum_arith.sipl", {"N": 3}, {"S": 12}),
    ("sum_arith.sipl", {"N": 10}, {"S": 110}),
    ("parity.sipl", {"N": 5}, {"E": 0}),
    ("parity.sipl", {"N": 4}, {"E": 1}),
    ("fib.sipl", {"N": 3}, {"A": 2}),
    ("fib.sipl", {"N": 10}, {"A": 55}),
    ("max.sipl", {"X": 3, "Y": 8}, {"M": 8}),
    ("max.sipl", {"X": 9, "Y": 2}, {"M": 9}),
    ("divisible.sipl", {"X": 9, "Y": 5}, {"R": 0}),
    ("divisible.sipl", {"X": 10, "Y": 5}, {"R": 1}),
]


class ExampleTests(unittest.TestCase):
    def test_interpreter(self):
        for name, state, expected in CASES:
            with self.subTest(name=name, state=state):
                prog = sipl.parse(read_example(name))
                final = run(prog, state)
                for var, val in expected.items():
                    self.assertEqual(final[var], val)

    def test_term_agrees_with_interpreter(self):
        for name, state, expected in CASES:
            with self.subTest(name=name, state=state):
                src = read_example(name)
                prog = sipl.parse(src)
                res = evaluate(build_term(prog, src), state)
                self.assertTrue(res.defined)
                self.assertEqual(res.state, run(prog, state))


if __name__ == "__main__":
    unittest.main()
