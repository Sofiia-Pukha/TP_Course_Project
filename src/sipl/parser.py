"""Синтаксичний аналіз SIPL (рекурсивний спуск).

Парсер будує дерево виводу за БНФ курсу (parse_tree.py). Неоднозначність БНФ
знімається пріоритетами:
  оператори:  ';' (найнижчий, ліва асоціативність) < решта операторів
  вирази:     + - (ліва асоціативність) < *
  умови:      ∨ (ліва асоціативність) < ¬ < порівняння (= >)
Тіла if/while - один оператор без ';', тому кілька операторів у циклі
треба брати в begin ... end.
"""
from .errors import SiplSyntaxError
from .lexer import tokenize
from .parse_tree import (ParseNode, PROG, STM, AEXP, BEXP, VAR, NUM, TERMINAL)


def describe(tok):
    if tok.kind == "EOF":
        return "кінець тексту"
    return f"'{tok.text}'"


class Parser:
    def __init__(self, source):
        self.tokens = tokenize(source)
        self.pos = 0

    # --- допоміжне ---
    def peek(self, shift=0):
        i = min(self.pos + shift, len(self.tokens) - 1)
        return self.tokens[i]

    def advance(self):
        tok = self.tokens[self.pos]
        if tok.kind != "EOF":
            self.pos += 1
        return tok

    def leaf(self, tok):
        return ParseNode(TERMINAL, "T", tok.span, [], tok.text)

    def expect(self, kind, what):
        tok = self.peek()
        if tok.kind != kind:
            raise SiplSyntaxError(f"очікувалось {what}, знайдено {describe(tok)}", tok.span)
        self.advance()
        return self.leaf(tok)

    def node(self, kind, rule, children):
        span = children[0].span.join(children[-1].span)
        return ParseNode(kind, rule, span, children)

    # --- програма та оператори ---
    def parse_program(self):
        b = self.expect("begin", "'begin'")
        body = self.parse_stm()
        e = self.expect("end", "'end' (або ';' чи новий оператор)")
        if self.peek().kind != "EOF":
            raise SiplSyntaxError(
                f"після завершального 'end' не може бути тексту, знайдено {describe(self.peek())}",
                self.peek().span)
        return self.node(PROG, "P1", [b, body, e])

    def parse_stm(self):
        left = self.parse_simple_stm()
        while self.peek().kind == ";":
            semi = self.leaf(self.advance())
            right = self.parse_simple_stm()
            left = self.node(STM, "S2", [left, semi, right])
        return left

    def parse_simple_stm(self):
        tok = self.peek()
        if tok.kind == "NAME":
            var = self.parse_var()
            assign = self.expect(":=", "':='")
            expr = self.parse_aexp()
            return self.node(STM, "S1", [var, assign, expr])
        if tok.kind == "if":
            kw = self.leaf(self.advance())
            cond = self.parse_bexp()
            then_kw = self.expect("then", "'then'")
            s1 = self.parse_simple_stm()
            else_kw = self.expect("else", "'else'")
            s2 = self.parse_simple_stm()
            return self.node(STM, "S3", [kw, cond, then_kw, s1, else_kw, s2])
        if tok.kind == "while":
            kw = self.leaf(self.advance())
            cond = self.parse_bexp()
            do_kw = self.expect("do", "'do'")
            body = self.parse_simple_stm()
            return self.node(STM, "S4", [kw, cond, do_kw, body])
        if tok.kind == "begin":
            b = self.leaf(self.advance())
            inner = self.parse_stm()
            e = self.expect("end", "'end'")
            return self.node(STM, "S5", [b, inner, e])
        if tok.kind == "skip":
            return self.node(STM, "S6", [self.leaf(self.advance())])
        raise SiplSyntaxError(f"очікувався оператор, знайдено {describe(tok)}", tok.span)

    def parse_var(self):
        tok = self.peek()
        if tok.kind != "NAME":
            raise SiplSyntaxError(f"очікувалась змінна, знайдено {describe(tok)}", tok.span)
        self.advance()
        return self.node(VAR, "NV", [self.leaf(tok)])

    # --- арифметичні вирази ---
    def parse_aexp(self):
        left = self.parse_term()
        while self.peek().kind in ("+", "-"):
            op = self.advance()
            right = self.parse_term()
            rule = "A3" if op.kind == "+" else "A4"
            left = self.node(AEXP, rule, [left, self.leaf(op), right])
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.peek().kind == "*":
            op = self.advance()
            right = self.parse_factor()
            left = self.node(AEXP, "A5", [left, self.leaf(op), right])
        return left

    def parse_factor(self):
        tok = self.peek()
        if tok.kind == "NUM":
            self.advance()
            num = self.node(NUM, "NN", [self.leaf(tok)])
            return self.node(AEXP, "A1", [num])
        if tok.kind == "-" and self.peek(1).kind == "NUM":
            # від'ємна константа, наприклад -1 (у БНФ число може бути від'ємним)
            minus = self.advance()
            digits = self.advance()
            lf = ParseNode(TERMINAL, "T", minus.span.join(digits.span), [], "-" + digits.text)
            num = self.node(NUM, "NN", [lf])
            return self.node(AEXP, "A1", [num])
        if tok.kind == "NAME":
            return self.node(AEXP, "A2", [self.parse_var()])
        if tok.kind == "(":
            lp = self.leaf(self.advance())
            inner = self.parse_aexp()
            rp = self.expect(")", "')'")
            return self.node(AEXP, "A6", [lp, inner, rp])
        raise SiplSyntaxError(f"очікувався вираз, знайдено {describe(tok)}", tok.span)

    # --- умови ---
    def parse_bexp(self):
        left = self.parse_bnot()
        while self.peek().kind == "∨":
            op = self.leaf(self.advance())
            right = self.parse_bnot()
            left = self.node(BEXP, "B3", [left, op, right])
        return left

    def parse_bnot(self):
        if self.peek().kind == "¬":
            op = self.leaf(self.advance())
            operand = self.parse_bnot()
            return self.node(BEXP, "B4", [op, operand])
        return self.parse_batom()

    def parse_batom(self):
        if self.peek().kind == "(":
            # дужка може відкривати і умову, і вираз: (X > 1) або (X + 1) > 2.
            # Спочатку пробуємо як умову, якщо не вийшло - як порівняння.
            saved = self.pos
            try:
                lp = self.leaf(self.advance())
                inner = self.parse_bexp()
                rp = self.expect(")", "')'")
                return self.node(BEXP, "B5", [lp, inner, rp])
            except SiplSyntaxError as e1:
                self.pos = saved
                try:
                    return self.parse_compare()
                except SiplSyntaxError as e2:
                    # показуємо ту помилку, що виникла далі в тексті
                    raise e1 if e1.span.start > e2.span.start else e2
        return self.parse_compare()

    def parse_compare(self):
        left = self.parse_aexp()
        tok = self.peek()
        if tok.kind not in ("=", ">"):
            raise SiplSyntaxError(f"очікувалось '=' або '>', знайдено {describe(tok)}", tok.span)
        op = self.leaf(self.advance())
        right = self.parse_aexp()
        return self.node(BEXP, "B1" if tok.kind == "=" else "B2", [left, op, right])


def parse_tree(source):
    """Текст -> дерево синтаксичного виводу."""
    return Parser(source).parse_program()
