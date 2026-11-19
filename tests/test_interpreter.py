import unittest

import sipl
from sipl.errors import StepLimitExceeded, UndefinedVariableError
from sipl.interpreter import run


def go(text, state=None, **kw):
    return run(sipl.parse(text), state, **kw)


class InterpreterTests(unittest.TestCase):
    def test_assign_and_seq(self):
        self.assertEqual(go("begin X := 2; Y := X * 3 end"), {"X": 2, "Y": 6})

    def test_if_both_branches(self):
        prog = "begin if X > 0 then R := 1 else R := 2 end"
        self.assertEqual(go(prog, {"X": 5})["R"], 1)
        self.assertEqual(go(prog, {"X": 0})["R"], 2)

    def test_while_zero_iterations(self):
        self.assertEqual(go("begin while X > 0 do X := X - 1 end", {"X": 0}), {"X": 0})

    def test_skip_and_block(self):
        self.assertEqual(go("begin begin skip end end", {"X": 1}), {"X": 1})

    def test_conditions(self):
        prog = "begin if ¬ (X = 1) ∨ Y > 5 then R := 1 else R := 0 end"
        self.assertEqual(go(prog, {"X": 1, "Y": 9})["R"], 1)
        self.assertEqual(go(prog, {"X": 1, "Y": 2})["R"], 0)
        self.assertEqual(go(prog, {"X": 3, "Y": 2})["R"], 1)

    def test_input_state_not_modified(self):
        st = {"X": 1}
        go("begin X := 5 end", st)
        self.assertEqual(st, {"X": 1})

    def test_undefined_variable(self):
        with self.assertRaises(UndefinedVariableError) as cm:
            go("begin X := Y + 1 end")
        self.assertIn("Y", cm.exception.message)

    def test_step_limit(self):
        with self.assertRaises(StepLimitExceeded):
            go("begin X := 1; while X > 0 do X := X + 1 end", max_steps=100)


if __name__ == "__main__":
    unittest.main()
