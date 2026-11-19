"""Дерево синтаксичного виводу (parse tree) за БНФ курсу."""
from dataclasses import dataclass, field

from .errors import SourceSpan

# синтаксичні категорії
PROG = "<програма>"
STM = "<оператор>"
AEXP = "<вираз>"
BEXP = "<умова>"
VAR = "<змінна>"
NUM = "<число>"
TERMINAL = "термінал"


@dataclass
class ParseNode:
    kind: str                 # категорія або TERMINAL
    rule: str                 # ім'я правила БНФ (P1, S1..S6, A1..A6, B1..B5, NV, NN) або "T"
    span: SourceSpan
    children: list = field(default_factory=list)
    text: str = ""            # тільки для листків

    @property
    def is_leaf(self):
        return self.kind == TERMINAL

    def leaves(self):
        """Листки зліва направо (обхід дерева)."""
        if self.is_leaf:
            return [self]
        result = []
        for ch in self.children:
            result.extend(ch.leaves())
        return result
