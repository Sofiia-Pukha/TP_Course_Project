"""Інтерпретатор SIPL: виконує AST над станом (словник змінна -> ціле)."""
from . import ast as A
from .errors import StepLimitExceeded, UndefinedVariableError

MAX_STEPS = 100000


class Interpreter:
    def __init__(self, max_steps=MAX_STEPS):
        self.max_steps = max_steps
        self.steps = 0

    def run(self, program, state=None):
        st = dict(state or {})
        self.steps = 0
        self.exec_stm(program.body, st)
        return st

    def exec_stm(self, s, st):
        self.steps += 1
        if self.steps > self.max_steps:
            raise StepLimitExceeded(
                f"перевищено ліміт у {self.max_steps} кроків (можливо, нескінченний цикл)", s.span)
        if isinstance(s, A.Assign):
            st[s.var] = self.eval_a(s.expr, st)
        elif isinstance(s, A.Seq):
            self.exec_stm(s.first, st)
            self.exec_stm(s.second, st)
        elif isinstance(s, A.If):
            if self.eval_b(s.cond, st):
                self.exec_stm(s.then_branch, st)
            else:
                self.exec_stm(s.else_branch, st)
        elif isinstance(s, A.While):
            while self.eval_b(s.cond, st):
                self.exec_stm(s.body, st)
                self.steps += 1
                if self.steps > self.max_steps:
                    raise StepLimitExceeded(
                        f"перевищено ліміт у {self.max_steps} кроків (можливо, нескінченний цикл)",
                        s.span)
        elif isinstance(s, A.Block):
            self.exec_stm(s.body, st)
        elif isinstance(s, A.Skip):
            pass
        else:
            raise TypeError(f"невідомий оператор {s}")

    def eval_a(self, e, st):
        if isinstance(e, A.Num):
            return e.value
        if isinstance(e, A.Var):
            if e.name not in st:
                raise UndefinedVariableError(f"змінна {e.name} не має значення", e.span)
            return st[e.name]
        if isinstance(e, A.ParenA):
            return self.eval_a(e.inner, st)
        if isinstance(e, A.BinOp):
            l = self.eval_a(e.left, st)
            r = self.eval_a(e.right, st)
            if e.op == "+":
                return l + r
            if e.op == "-":
                return l - r
            return l * r
        raise TypeError(f"невідомий вираз {e}")

    def eval_b(self, b, st):
        if isinstance(b, A.Compare):
            l = self.eval_a(b.left, st)
            r = self.eval_a(b.right, st)
            return l == r if b.op == "=" else l > r
        if isinstance(b, A.Or):
            # обидві частини обчислюються: ∨ тут - звичайна функція or
            l = self.eval_b(b.left, st)
            r = self.eval_b(b.right, st)
            return l or r
        if isinstance(b, A.Not):
            return not self.eval_b(b.operand, st)
        if isinstance(b, A.ParenB):
            return self.eval_b(b.inner, st)
        raise TypeError(f"невідома умова {b}")


def run(program, state=None, max_steps=MAX_STEPS):
    return Interpreter(max_steps).run(program, state)
