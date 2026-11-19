"""Абстрактний синтаксис SIPL (AST) та побудова його з дерева виводу."""
from dataclasses import dataclass, fields

from .errors import SourceSpan
from .parse_tree import ParseNode


@dataclass(frozen=True)
class Node:
    span: SourceSpan


# --- арифметичні вирази ---
@dataclass(frozen=True)
class Num(Node):
    value: int


@dataclass(frozen=True)
class Var(Node):
    name: str


@dataclass(frozen=True)
class BinOp(Node):
    op: str          # '+', '-', '*'
    left: Node
    right: Node


@dataclass(frozen=True)
class ParenA(Node):
    inner: Node


# --- умови ---
@dataclass(frozen=True)
class Compare(Node):
    op: str          # '=', '>'
    left: Node
    right: Node


@dataclass(frozen=True)
class Or(Node):
    left: Node
    right: Node


@dataclass(frozen=True)
class Not(Node):
    operand: Node


@dataclass(frozen=True)
class ParenB(Node):
    inner: Node


# --- оператори ---
@dataclass(frozen=True)
class Assign(Node):
    var: str
    expr: Node


@dataclass(frozen=True)
class Seq(Node):
    first: Node
    second: Node


@dataclass(frozen=True)
class If(Node):
    cond: Node
    then_branch: Node
    else_branch: Node


@dataclass(frozen=True)
class While(Node):
    cond: Node
    body: Node


@dataclass(frozen=True)
class Block(Node):
    body: Node


@dataclass(frozen=True)
class Skip(Node):
    pass


@dataclass(frozen=True)
class Program(Node):
    body: Node


# --- побудова AST з дерева виводу (за іменем правила БНФ) ---
def build_ast(tree):
    if tree.rule != "P1":
        raise ValueError("очікувався корінь <програма>")
    return Program(tree.span, build_stm(tree.children[1]))


def build_stm(n):
    c = n.children
    if n.rule == "S1":
        return Assign(n.span, c[0].children[0].text, build_aexp(c[2]))
    if n.rule == "S2":
        return Seq(n.span, build_stm(c[0]), build_stm(c[2]))
    if n.rule == "S3":
        return If(n.span, build_bexp(c[1]), build_stm(c[3]), build_stm(c[5]))
    if n.rule == "S4":
        return While(n.span, build_bexp(c[1]), build_stm(c[3]))
    if n.rule == "S5":
        return Block(n.span, build_stm(c[1]))
    if n.rule == "S6":
        return Skip(n.span)
    raise ValueError(f"невідоме правило оператора {n.rule}")


def build_aexp(n):
    c = n.children
    if n.rule == "A1":
        return Num(n.span, int(c[0].children[0].text))
    if n.rule == "A2":
        return Var(n.span, c[0].children[0].text)
    if n.rule in ("A3", "A4", "A5"):
        return BinOp(n.span, c[1].text, build_aexp(c[0]), build_aexp(c[2]))
    if n.rule == "A6":
        return ParenA(n.span, build_aexp(c[1]))
    raise ValueError(f"невідоме правило виразу {n.rule}")


def build_bexp(n):
    c = n.children
    if n.rule in ("B1", "B2"):
        return Compare(n.span, c[1].text, build_aexp(c[0]), build_aexp(c[2]))
    if n.rule == "B3":
        return Or(n.span, build_bexp(c[0]), build_bexp(c[2]))
    if n.rule == "B4":
        return Not(n.span, build_bexp(c[1]))
    if n.rule == "B5":
        return ParenB(n.span, build_bexp(c[1]))
    raise ValueError(f"невідоме правило умови {n.rule}")


def dump(node, indent=0):
    """Текстовий вигляд AST (без позицій) для виводу в консоль."""
    pad = "  " * indent
    simple = []
    kids = []
    for f in fields(node):
        if f.name == "span":
            continue
        v = getattr(node, f.name)
        if isinstance(v, Node):
            kids.append(v)
        else:
            simple.append(f"{f.name}={v!r}")
    lines = [pad + type(node).__name__ + (" " + " ".join(simple) if simple else "")]
    for k in kids:
        lines.append(dump(k, indent + 1))
    return "\n".join(lines)
