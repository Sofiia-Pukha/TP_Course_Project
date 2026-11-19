"""SEM-02: застосування терму до стану."""
import unittest

import sipl
from sipl.evaluator import evaluate, fmt_state
from sipl.semantics import build_term
from .helpers import read_example


def ev(text, state, **kw):
    return evaluate(build_term(sipl.parse(text), text), state, **kw)


class EvaluatorTests(unittest.TestCase):
    def test_power_5_2(self):
        # приклад з практичної роботи 2
        res = ev(read_example("power.sipl"), {"X": 5, "Y": 2})
        self.assertTrue(res.defined)
        self.assertEqual(res.state, {"X": 5, "Y": 0, "R": 25})

    def test_trace_rules(self):
        res = ev(read_example("power.sipl"), {"X": 5, "Y": 2})
        rules = {s.rule for s in res.trace}
        self.assertTrue({"AF_SEQ", "AF_AS", "AF_WH"} <= rules)
        self.assertTrue(any("gr(2, 0) = true" in s.text for s in res.trace))
        self.assertTrue(any("2 ітерацій" in s.text for s in res.trace))

    def test_if_and_id_rules(self):
        res = ev("begin if X > 0 then skip else Y := 1 end", {"X": 1})
        self.assertEqual({s.rule for s in res.trace}, {"AF_IF", "AF_ID"})

    def test_undefined_variable_gives_bottom(self):
        res = ev("begin X := Y end", {})
        self.assertFalse(res.defined)
        self.assertIn("Y", res.reason)

    def test_nonterminating_loop_is_undefined(self):
        res = ev(read_example("loop_forever.sipl"), {}, max_steps=200)
        self.assertFalse(res.defined)
        self.assertIsNone(res.state)

    def test_fmt_state(self):
        self.assertEqual(fmt_state({"X": 1, "Y": 2}), "[X ↦ 1, Y ↦ 2]")

    def test_input_state_not_modified(self):
        st = {"X": 1}
        ev("begin X := 7 end", st)
        self.assertEqual(st, {"X": 1})


if __name__ == "__main__":
    unittest.main()
