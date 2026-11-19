"""Командний рядок: python -m sipl <команда> файл.sipl"""
import argparse
import sys

from . import ast as A
from .errors import SiplError, format_error
from .evaluator import evaluate, fmt_state
from .interpreter import run
from .parser import parse_tree
from .semantics import build_term
from . import visualization as V


def parse_state(text):
    """'X=5,Y=2' -> {'X': 5, 'Y': 2}"""
    st = {}
    if not text:
        return st
    for item in text.split(","):
        name, sep, value = item.partition("=")
        if not sep:
            raise argparse.ArgumentTypeError(f"очікувався формат ІМ'Я=число, отримано '{item}'")
        try:
            st[name.strip()] = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"'{value}' не є цілим числом")
    return st


def build_parser():
    ap = argparse.ArgumentParser(prog="sipl", description="Інструменти для мови SIPL")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("parse", help="показати AST")
    p.add_argument("file")

    p = sub.add_parser("tree", help="дерево синтаксичного виводу")
    p.add_argument("file")
    p.add_argument("--format", choices=["text", "json", "dot"], default="text")
    p.add_argument("--check", action="store_true",
                   help="перевірити синтаксичну правильність за листками дерева")

    p = sub.add_parser("term", help="семантичний терм програми")
    p.add_argument("file")
    p.add_argument("--rules", action="store_true", help="показати застосовані правила sem_*")

    p = sub.add_parser("run", help="виконати програму (інтерпретатор)")
    p.add_argument("file")
    p.add_argument("--state", type=parse_state, default={}, help="початковий стан, напр. X=5,Y=2")
    p.add_argument("--max-steps", type=int, default=100000)

    p = sub.add_parser("eval", help="застосувати семантичний терм до стану")
    p.add_argument("file")
    p.add_argument("--state", type=parse_state, default={}, help="початковий стан, напр. X=5,Y=2")
    p.add_argument("--steps", action="store_true", help="показати кроки застосування формул AF_*")
    p.add_argument("--max-steps", type=int, default=100000)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    with open(args.file, encoding="utf-8") as f:
        source = f.read()
    try:
        return execute(args, source)
    except SiplError as e:
        print(format_error(source, e), file=sys.stderr)
        sys.exit(1)


def execute(args, source):
    tree = parse_tree(source)
    program = A.build_ast(tree)

    if args.cmd == "parse":
        print(A.dump(program))
    elif args.cmd == "tree":
        if args.format == "text":
            print(V.tree_to_text(tree))
        elif args.format == "json":
            print(V.tree_to_json(tree, source))
        else:
            print(V.tree_to_dot(tree))
        if args.check:
            ok, from_leaves, from_source = V.check_syntax(tree, source)
            print("\nлистки зліва направо:", V.leaves_listing(tree), file=sys.stderr)
            print("синтаксично правильна:", "так" if ok else "ні", file=sys.stderr)
    elif args.cmd == "term":
        log = [] if args.rules else None
        term = build_term(program, source, log)
        if log:
            for step in log:
                print(f"{step.rule}: {step.left} = {step.right}")
            print()
        print(term)
    elif args.cmd == "run":
        print(fmt_state(run(program, args.state, args.max_steps)))
    elif args.cmd == "eval":
        term = build_term(program, source)
        res = evaluate(term, args.state, args.max_steps)
        if args.steps:
            for s in res.trace:
                print("  " * s.depth + f"[{s.rule}] {s.text}")
            print()
        if res.defined:
            print(fmt_state(res.state))
        else:
            print("результат не визначений (⊥):", res.reason)
            sys.exit(2)
    return 0
