import unittest

import sipl
from sipl import ast as A
from sipl.errors import SiplSyntaxError, format_error
from sipl.parser import parse_tree


def stm(text):
    """AST єдиного оператора всередині begin ... end"""
    return sipl.parse(f"begin {text} end").body


class ParserTests(unittest.TestCase):
    def test_mult_before_add(self):
        e = stm("X := 1 + 2 * 3").expr
        self.assertEqual(e.op, "+")
        self.assertEqual(e.right.op, "*")

    def test_left_assoc_minus(self):
        e = stm("X := 10 - 3 - 2").expr
        self.assertEqual(e.op, "-")
        self.assertIsInstance(e.left, A.BinOp)
        self.assertIsInstance(e.right, A.Num)

    def test_seq_is_left_assoc(self):
        s = stm("X := 1; Y := 2; Z := 3")
        self.assertIsInstance(s, A.Seq)
        self.assertIsInstance(s.first, A.Seq)
        self.assertIsInstance(s.second, A.Assign)

    def test_while_body_is_single_statement(self):
        # ';' після тіла циклу належить зовнішній послідовності
        s = stm("while X > 0 do X := X - 1; Y := 1")
        self.assertIsInstance(s, A.Seq)
        self.assertIsInstance(s.first, A.While)

    def test_negative_number(self):
        self.assertEqual(stm("X := -5").expr.value, -5)
        e = stm("X := Y - -1").expr
        self.assertEqual(e.op, "-")
        self.assertEqual(e.right.value, -1)

    def test_not_binds_tighter_than_or(self):
        c = stm("if ¬ X > 1 ∨ Y = 2 then skip else skip").cond
        self.assertIsInstance(c, A.Or)
        self.assertIsInstance(c.left, A.Not)

    def test_ascii_or_not(self):
        c = stm("if not X > 1 or Y = 2 then skip else skip").cond
        self.assertIsInstance(c, A.Or)

    def test_paren_condition_and_expression(self):
        c1 = stm("if (X > 1) ∨ Y = 2 then skip else skip").cond
        self.assertIsInstance(c1.left, A.ParenB)
        c2 = stm("if (X + 1) > 2 then skip else skip").cond
        self.assertIsInstance(c2, A.Compare)
        self.assertIsInstance(c2.left, A.ParenA)

    def test_spans(self):
        src = "begin\n  X := 1 + 2\nend"
        prog = sipl.parse(src)
        assign = prog.body
        self.assertEqual(assign.span.text(src), "X := 1 + 2")
        self.assertEqual((assign.span.line, assign.span.column), (2, 3))
        self.assertEqual(assign.expr.span.text(src), "1 + 2")
        self.assertEqual(prog.span.text(src), src)

    def test_error_position(self):
        src = "begin\n  X := 1 +\nend"
        with self.assertRaises(SiplSyntaxError) as cm:
            sipl.parse(src)
        self.assertEqual(cm.exception.span.line, 3)
        msg = format_error(src, cm.exception)
        self.assertIn("рядок 3", msg)
        self.assertIn("^", msg)

    def test_lexer_error_position(self):
        src = "begin X := 1 @ 2 end"
        with self.assertRaises(SiplSyntaxError) as cm:
            sipl.parse(src)
        self.assertEqual(cm.exception.span.column, 14)

    def test_parse_tree_rule_names(self):
        t = parse_tree("begin X := 1 end")
        self.assertEqual(t.rule, "P1")
        self.assertEqual(t.children[1].rule, "S1")


if __name__ == "__main__":
    unittest.main()
