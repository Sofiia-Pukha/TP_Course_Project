"""SIPL Language Toolkit."""
from .parser import parse_tree
from .parse_tree import ParseNode
from .ast import build_ast


def parse(source):
    """Текст програми -> AST."""
    return build_ast(parse_tree(source))


__all__ = ["parse", "parse_tree", "build_ast", "ParseNode"]
__version__ = "0.5.0"
