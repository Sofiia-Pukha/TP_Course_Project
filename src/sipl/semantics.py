"""Семантичні терми SIPL та їх побудова з AST (правила sem_P, sem_S, sem_A, sem_B)."""
from dataclasses import dataclass

from . import ast as A


# --- терми програмної алгебри ---
@dataclass(frozen=True)
class Const:
    value: int

    def __str__(self):
        return str(self.value)


@dataclass(frozen=True)
class Deref:
    """Функція розіменування x⇒"""
    var: str

    def __str__(self):
        return f"{self.var}⇒"


@dataclass(frozen=True)
class Superpos:
    """Суперпозиція S^n(f, g1, ..., gn)"""
    func: str
    args: tuple

    def __str__(self):
        inside = ", ".join([self.func] + [str(a) for a in self.args])
        return f"S{len(self.args)}({inside})"


@dataclass(frozen=True)
class AS:
    """Присвоювання AS_x(f)"""
    var: str
    term: object

    def __str__(self):
        return f"AS_{self.var}({self.term})"


@dataclass(frozen=True)
class Seq:
    first: object
    second: object

    def __str__(self):
        right = f"({self.second})" if isinstance(self.second, Seq) else str(self.second)
        return f"{self.first} · {right}"


@dataclass(frozen=True)
class IF:
    cond: object
    then_term: object
    else_term: object

    def __str__(self):
        return f"IF({self.cond}, {self.then_term}, {self.else_term})"


@dataclass(frozen=True)
class WH:
    cond: object
    body: object

    def __str__(self):
        return f"WH({self.cond}, {self.body})"


@dataclass(frozen=True)
class Id:
    def __str__(self):
        return "id"


ARITH_FUNCS = {"+": "add", "-": "sub", "*": "mult"}
BOOL_FUNCS = {"=": "eq", ">": "gr"}


@dataclass
class RuleStep:
    """Один крок побудови терму: яке правило застосували і до чого."""
    rule: str
    left: str
    right: str


class Builder:
    def __init__(self, source="", log=None):
        self.source = source
        self.log = log

    def frag(self, node):
        return " ".join(node.span.text(self.source).split())

    def record(self, rule, node, right_text):
        if self.log is None:
            return
        self.log.append(RuleStep(rule, f"{self.kind_name(node)}({self.frag(node)})", right_text))

    @staticmethod
    def kind_name(node):
        if isinstance(node, A.Program):
            return "sem_P"
        if isinstance(node, (A.Num, A.Var, A.BinOp, A.ParenA)):
            return "sem_A"
        if isinstance(node, (A.Compare, A.Or, A.Not, A.ParenB)):
            return "sem_B"
        return "sem_S"

    def sem_p(self, p):
        self.record("NS_Prog", p, f"sem_S({self.frag(p.body)})")
        return self.sem_s(p.body)

    def sem_s(self, s):
        if isinstance(s, A.Assign):
            self.record("NS_Stm_As", s, f"AS_{s.var}(sem_A({self.frag(s.expr)}))")
            return AS(s.var, self.sem_a(s.expr))
        if isinstance(s, A.Seq):
            self.record("NS_Stm_Seq", s,
                        f"sem_S({self.frag(s.first)}) · sem_S({self.frag(s.second)})")
            return Seq(self.sem_s(s.first), self.sem_s(s.second))
        if isinstance(s, A.If):
            self.record("NS_Stm_If", s,
                        f"IF(sem_B({self.frag(s.cond)}), sem_S({self.frag(s.then_branch)}), "
                        f"sem_S({self.frag(s.else_branch)}))")
            return IF(self.sem_b(s.cond), self.sem_s(s.then_branch), self.sem_s(s.else_branch))
        if isinstance(s, A.While):
            self.record("NS_Stm_Wh", s, f"WH(sem_B({self.frag(s.cond)}), sem_S({self.frag(s.body)}))")
            return WH(self.sem_b(s.cond), self.sem_s(s.body))
        if isinstance(s, A.Block):
            self.record("NS_Stm_BE", s, f"(sem_S({self.frag(s.body)}))")
            return self.sem_s(s.body)
        if isinstance(s, A.Skip):
            self.record("NS_Stm_skip", s, "id")
            return Id()
        raise TypeError(f"невідомий оператор {s}")

    def sem_a(self, a):
        if isinstance(a, A.Num):
            self.record("NS_A_Num", a, str(a.value))
            return Const(a.value)
        if isinstance(a, A.Var):
            self.record("NS_A_Var", a, f"{a.name}⇒")
            return Deref(a.name)
        if isinstance(a, A.BinOp):
            f = ARITH_FUNCS[a.op]
            rule = {"+": "NS_A_Add", "-": "NS_A_Sub", "*": "NS_A_Mult"}[a.op]
            self.record(rule, a, f"S2({f}, sem_A({self.frag(a.left)}), sem_A({self.frag(a.right)}))")
            return Superpos(f, (self.sem_a(a.left), self.sem_a(a.right)))
        if isinstance(a, A.ParenA):
            self.record("NS_A_Par", a, f"sem_A({self.frag(a.inner)})")
            return self.sem_a(a.inner)
        raise TypeError(f"невідомий вираз {a}")

    def sem_b(self, b):
        if isinstance(b, A.Compare):
            f = BOOL_FUNCS[b.op]
            rule = "NS_B_eq" if b.op == "=" else "NS_B_gr"
            self.record(rule, b, f"S2({f}, sem_A({self.frag(b.left)}), sem_A({self.frag(b.right)}))")
            return Superpos(f, (self.sem_a(b.left), self.sem_a(b.right)))
        if isinstance(b, A.Or):
            self.record("NS_B_or", b, f"S2(or, sem_B({self.frag(b.left)}), sem_B({self.frag(b.right)}))")
            return Superpos("or", (self.sem_b(b.left), self.sem_b(b.right)))
        if isinstance(b, A.Not):
            self.record("NS_B_neg", b, f"S1(neg, sem_B({self.frag(b.operand)}))")
            return Superpos("neg", (self.sem_b(b.operand),))
        if isinstance(b, A.ParenB):
            self.record("NS_B_Par", b, f"sem_B({self.frag(b.inner)})")
            return self.sem_b(b.inner)
        raise TypeError(f"невідома умова {b}")


def build_term(program, source="", log=None):
    """AST програми -> семантичний терм.
    Якщо передати список log (і текст програми source), у нього запишуться
    застосовані правила в порядку, як у розв'язках з практикуму."""
    return Builder(source, log).sem_p(program)
