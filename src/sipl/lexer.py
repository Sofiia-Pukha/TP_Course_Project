"""Лексичний аналіз SIPL: текст -> список токенів."""
import re
from bisect import bisect_right
from dataclasses import dataclass

from .errors import SourceSpan, SiplSyntaxError

KEYWORDS = {"begin", "end", "if", "then", "else", "while", "do", "skip", "or", "not"}

# or/not - це ASCII-варіанти для символів ∨ та ¬
ALIASES = {"or": "∨", "not": "¬"}

TOKEN_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<num>[0-9]+)
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<sym>:=|[;+\-*()=>∨¬])
""", re.VERBOSE)


@dataclass(frozen=True)
class Token:
    kind: str    # NUM, NAME, EOF, або сам символ/ключове слово
    text: str
    span: SourceSpan


class SourceMap:
    """Перетворює зміщення в тексті на рядок і колонку."""

    def __init__(self, source):
        self.line_starts = [0]
        for i, ch in enumerate(source):
            if ch == "\n":
                self.line_starts.append(i + 1)

    def position(self, offset):
        line = bisect_right(self.line_starts, offset)
        return line, offset - self.line_starts[line - 1] + 1

    def span(self, start, end):
        l1, c1 = self.position(start)
        l2, c2 = self.position(end)
        return SourceSpan(start, end, l1, c1, l2, c2)


def tokenize(source):
    smap = SourceMap(source)
    tokens = []
    pos = 0
    while pos < len(source):
        m = TOKEN_RE.match(source, pos)
        if m is None:
            span = smap.span(pos, pos + 1)
            raise SiplSyntaxError(f"недопустимий символ '{source[pos]}'", span)
        text = m.group()
        span = smap.span(pos, m.end())
        pos = m.end()
        if m.lastgroup == "ws":
            continue
        if m.lastgroup == "num":
            tokens.append(Token("NUM", text, span))
        elif m.lastgroup == "name":
            if text in KEYWORDS:
                tokens.append(Token(ALIASES.get(text, text), text, span))
            else:
                tokens.append(Token("NAME", text, span))
        else:
            tokens.append(Token(text, text, span))
    tokens.append(Token("EOF", "", smap.span(len(source), len(source))))
    return tokens
