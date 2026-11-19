"""CORE-01: позитивні та негативні приклади граматики."""
import unittest

import sipl
from sipl.errors import SiplSyntaxError

VALID = [
    "begin skip end",
    "begin X := 1 end",
    "begin X := -1 end",
    "begin X := 1; Y := 2 end",
    "begin X := (1 + 2) * 3 - Y end",
    "begin if X > 0 then Y := 1 else Y := 2 end",
    "begin while X > 0 do X := X - 1 end",
    "begin begin skip end end",
    "begin while X > 0 do begin X := X - 1; Y := Y + X end end",
    "begin if X = 1 ∨ Y > 2 then skip else skip end",
    "begin if ¬ (X > 1) then skip else skip end",
    "begin if (X + 1) > 2 then skip else skip end",
    "begin if (X > 1) ∨ (Y = 0) then skip else skip end",
    "begin if X > 1 or not Y = 0 then skip else skip end",
    "begin if X > 0 then if Y > 0 then skip else skip else skip end",
]

INVALID = [
    "",                                   # порожній текст
    "skip",                               # немає begin/end
    "begin end",                          # порожній блок
    "begin X := end",                     # немає виразу
    "begin X = 1 end",                    # = замість :=
    "begin X := 1; end",                  # зайва ;
    "begin if X > 0 then skip end",       # немає else
    "begin while X > 0 skip end",         # немає do
    "begin while X do skip end",          # умова без порівняння
    "begin X := 1 + end",                 # немає другого операнда
    "begin X := (1 + 2 end",              # не закрита дужка
    "begin X := 1 end end",               # зайвий end
    "begin 5 := 1 end",                   # число замість змінної
    "begin begin := 1 end",               # ключове слово як змінна
    "begin X := 1 # 2 end",               # недопустимий символ
    "begin X := 1 2 end",                 # два числа підряд
]


class GrammarTests(unittest.TestCase):
    def test_valid(self):
        for text in VALID:
            with self.subTest(text=text):
                sipl.parse(text)

    def test_invalid(self):
        for text in INVALID:
            with self.subTest(text=text):
                with self.assertRaises(SiplSyntaxError):
                    sipl.parse(text)

    def test_enough_cases(self):
        self.assertGreaterEqual(len(VALID), 10)
        self.assertGreaterEqual(len(INVALID), 10)


class LarkGrammarTests(unittest.TestCase):
    """Файл grammar/sipl.lark має приймати і відхиляти те саме, що й парсер."""

    def setUp(self):
        try:
            import lark
        except ImportError:
            self.skipTest("lark не встановлено")
        import pathlib
        path = pathlib.Path(__file__).resolve().parent.parent / "grammar" / "sipl.lark"
        self.parser = lark.Lark(path.read_text(encoding="utf-8"), start="start")
        self.lark_error = lark.exceptions.LarkError

    def test_valid(self):
        for text in VALID:
            with self.subTest(text=text):
                self.parser.parse(text)

    def test_invalid(self):
        for text in INVALID:
            with self.subTest(text=text):
                with self.assertRaises(self.lark_error):
                    self.parser.parse(text)


if __name__ == "__main__":
    unittest.main()
