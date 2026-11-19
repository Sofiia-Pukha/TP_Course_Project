"""Обчислення семантичного терму на стані (формули AF_*) з поясненням кроків."""
from dataclasses import dataclass, field

from . import semantics as T

MAX_STEPS = 100000

FUNCS = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mult": lambda a, b: a * b,
    "eq": lambda a, b: a == b,
    "gr": lambda a, b: a > b,
    "or": lambda a, b: a or b,
    "neg": lambda a: not a,
}


class Undefined(Exception):
    """Значення терму не визначене (⊥)."""


@dataclass
class TraceStep:
    depth: int
    rule: str
    text: str


@dataclass
class EvalResult:
    defined: bool
    state: dict = None
    reason: str = ""
    trace: list = field(default_factory=list)


def fmt_val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def fmt_state(st):
    return "[" + ", ".join(f"{k} ↦ {v}" for k, v in st.items()) + "]"


def short(term, n=70):
    s = str(term)
    return s if len(s) <= n else s[:n - 1] + "…"


class Evaluator:
    def __init__(self, max_steps=MAX_STEPS):
        self.max_steps = max_steps
        self.steps = 0
        self.trace = []
        self.depth = 0

    def log(self, rule, text):
        self.trace.append(TraceStep(self.depth, rule, text))

    def tick(self):
        self.steps += 1
        if self.steps > self.max_steps:
            raise Undefined(f"перевищено ліміт у {self.max_steps} кроків (цикл, імовірно, не завершується)")

    # --- значення термів TFA / TFB ---
    def value(self, t, st):
        if isinstance(t, T.Const):
            return t.value
        if isinstance(t, T.Deref):
            if t.var not in st:
                raise Undefined(f"змінна {t.var} не визначена у стані {fmt_state(st)}")
            return st[t.var]
        if isinstance(t, T.Superpos):
            vals = [self.value(a, st) for a in t.args]
            return FUNCS[t.func](*vals)
        raise TypeError(f"{t} не є термом-функцією над станом зі значенням")

    def explain(self, t, st):
        """Ланцюжок рівностей обчислення значення, як у практикумі (AF_S, AF_DNM)."""
        v = self.value(t, st)
        if isinstance(t, T.Const):
            return [f"{t}(st)", fmt_val(v)]
        if isinstance(t, T.Deref):
            return [f"{t}(st)", fmt_val(v)]
        args_st = ", ".join(f"{a}(st)" for a in t.args)
        args_v = ", ".join(fmt_val(self.value(a, st)) for a in t.args)
        return [f"{t}(st)", f"{t.func}({args_st})", f"{t.func}({args_v})", fmt_val(v)]

    # --- застосування термів TFS до стану ---
    def apply(self, t, st):
        self.tick()
        if isinstance(t, T.Id):
            self.log("AF_ID", f"id(st) = st = {fmt_state(st)}")
            return st
        if isinstance(t, T.AS):
            parts = self.explain(t.term, st)
            new = dict(st)
            new[t.var] = self.value(t.term, st)
            chain = " = ".join(f"st∇[{t.var} ↦ {p}]" for p in parts)
            self.log("AF_AS", f"{short(t)}(st) = {chain} = {fmt_state(new)}")
            return new
        if isinstance(t, T.Seq):
            self.log("AF_SEQ", f"{short(t)}(st) = f2(f1(st)), де st = {fmt_state(st)}")
            self.depth += 1
            mid = self.apply(t.first, st)
            res = self.apply(t.second, mid)
            self.depth -= 1
            return res
        if isinstance(t, T.IF):
            cv = self.value(t.cond, st)
            chain = " = ".join(self.explain(t.cond, st))
            branch = "fs1" if cv else "fs2"
            self.log("AF_IF", f"{chain}; умова {fmt_val(cv)}, тому IF(st) = {branch}(st)")
            self.depth += 1
            res = self.apply(t.then_term if cv else t.else_term, st)
            self.depth -= 1
            return res
        if isinstance(t, T.WH):
            return self.apply_while(t, st)
        raise TypeError(f"{t} не є термом-функцією над станом")

    def apply_while(self, t, st):
        i = 0
        cur = st
        while True:
            self.tick()
            chain = " = ".join(self.explain(t.cond, cur))
            cv = self.value(t.cond, cur)
            self.log("AF_WH", f"st{i} = {fmt_state(cur)}; {chain}")
            if not cv:
                break
            self.depth += 1
            cur = self.apply(t.body, cur)
            self.depth -= 1
            i += 1
        self.log("AF_WH", f"умова хибна, цикл завершено після {i} ітерацій: st{i} = {fmt_state(cur)}")
        return cur


def evaluate(term, state, max_steps=MAX_STEPS):
    """Застосувати терм до стану. Результат: кінцевий стан або невизначеність."""
    ev = Evaluator(max_steps)
    try:
        final = ev.apply(term, dict(state))
        return EvalResult(True, final, "", ev.trace)
    except Undefined as e:
        return EvalResult(False, None, str(e), ev.trace)
