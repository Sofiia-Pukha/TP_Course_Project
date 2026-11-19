"""SEM-01: golden-тести семантичних термів."""
import unittest

import sipl
from sipl.semantics import build_term
from .helpers import read_example


def term_of(text):
    return str(build_term(sipl.parse(text), text))


class SemanticTermTests(unittest.TestCase):
    def test_power_matches_practicum(self):
        # терм із практичної роботи 2
        expected = ("AS_R(1) · WH(S2(gr, Y⇒, 0), "
                    "AS_R(S2(mult, R⇒, X⇒)) · AS_Y(S2(sub, Y⇒, 1)))")
        self.assertEqual(term_of(read_example("power.sipl")), expected)

    def test_div(self):
        expected = ("AS_R(0) · WH(S1(neg, S2(gr, Y⇒, X⇒)), "
                    "AS_X(S2(sub, X⇒, Y⇒)) · AS_R(S2(add, R⇒, 1)))")
        self.assertEqual(term_of(read_example("div.sipl")), expected)

    def test_if(self):
        self.assertEqual(term_of(read_example("max.sipl")),
                         "IF(S2(gr, X⇒, Y⇒), AS_M(X⇒), AS_M(Y⇒))")

    def test_skip(self):
        self.assertEqual(term_of("begin skip end"), "id")

    def test_parentheses_are_transparent(self):
        self.assertEqual(term_of("begin X := (1 + 2) * 3 end"),
                         "AS_X(S2(mult, S2(add, 1, 2), 3))")

    def test_or_eq(self):
        self.assertEqual(term_of("begin if X = 1 ∨ Y > 2 then skip else skip end"),
                         "IF(S2(or, S2(eq, X⇒, 1), S2(gr, Y⇒, 2)), id, id)")

    def test_seq_left_assoc_printing(self):
        self.assertEqual(term_of("begin X := 1; Y := 2; Z := 3 end"),
                         "AS_X(1) · AS_Y(2) · AS_Z(3)")

    def test_rules_log(self):
        src = "begin R := 1 end"
        log = []
        build_term(sipl.parse(src), src, log)
        self.assertEqual([s.rule for s in log], ["NS_Prog", "NS_Stm_As", "NS_A_Num"])
        self.assertEqual(log[1].right, "AS_R(sem_A(1))")


if __name__ == "__main__":
    unittest.main()
