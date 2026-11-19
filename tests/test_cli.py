import contextlib
import io
import unittest

from sipl import cli
from .helpers import EXAMPLES


def call(*args):
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            cli.main(list(args))
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_run(self):
        code, out, _ = call("run", str(EXAMPLES / "power.sipl"), "--state", "X=5,Y=2")
        self.assertEqual(code, 0)
        self.assertIn("R ↦ 25", out)

    def test_eval_steps(self):
        code, out, _ = call("eval", str(EXAMPLES / "power.sipl"), "--state", "X=2,Y=2", "--steps")
        self.assertEqual(code, 0)
        self.assertIn("[AF_WH]", out)
        self.assertIn("R ↦ 4", out)

    def test_term_rules(self):
        code, out, _ = call("term", str(EXAMPLES / "max.sipl"), "--rules")
        self.assertIn("NS_Stm_If", out)
        self.assertIn("IF(S2(gr, X⇒, Y⇒)", out)

    def test_tree_formats(self):
        for fmt in ("text", "json", "dot"):
            code, out, _ = call("tree", str(EXAMPLES / "max.sipl"), "--format", fmt)
            self.assertEqual(code, 0)
            self.assertTrue(out.strip())

    def test_tree_check(self):
        code, _, err = call("tree", str(EXAMPLES / "max.sipl"), "--check")
        self.assertIn("синтаксично правильна: так", err)

    def test_parse(self):
        code, out, _ = call("parse", str(EXAMPLES / "max.sipl"))
        self.assertIn("If", out)

    def test_syntax_error_exit_code(self):
        code, _, err = call("run", str(EXAMPLES / "broken.sipl"))
        self.assertEqual(code, 1)
        self.assertIn("рядок", err)

    def test_undefined_exit_code(self):
        code, out, _ = call("eval", str(EXAMPLES / "loop_forever.sipl"), "--max-steps", "50")
        self.assertEqual(code, 2)
        self.assertIn("⊥", out)

    def test_runtime_error(self):
        code, _, err = call("run", str(EXAMPLES / "power.sipl"))
        self.assertEqual(code, 1)
        self.assertIn("не має значення", err)


if __name__ == "__main__":
    unittest.main()
