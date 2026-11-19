"""Позиції в тексті програми та помилки SIPL."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpan:
    """Фрагмент вихідного тексту: зміщення (з 0) та рядок/колонка (з 1)."""
    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int

    def join(self, other):
        """Спан від початку self до кінця other."""
        return SourceSpan(self.start, other.end, self.line, self.column,
                          other.end_line, other.end_column)

    def text(self, source):
        return source[self.start:self.end]

    def to_dict(self):
        return {"start": self.start, "end": self.end,
                "line": self.line, "column": self.column,
                "end_line": self.end_line, "end_column": self.end_column}


class SiplError(Exception):
    def __init__(self, message, span=None):
        super().__init__(message)
        self.message = message
        self.span = span


class SiplSyntaxError(SiplError):
    pass


class SiplRuntimeError(SiplError):
    pass


class UndefinedVariableError(SiplRuntimeError):
    pass


class StepLimitExceeded(SiplRuntimeError):
    pass


def format_error(source, err):
    """Повідомлення з номером рядка, самим рядком і стрілкою до місця помилки."""
    if err.span is None:
        return err.message
    sp = err.span
    lines = source.split("\n")
    line_text = lines[sp.line - 1] if sp.line - 1 < len(lines) else ""
    if sp.end_line == sp.line:
        width = max(1, sp.end_column - sp.column)
    else:
        width = 1
    pointer = " " * (sp.column - 1) + "^" * width
    return f"рядок {sp.line}, колонка {sp.column}: {err.message}\n  {line_text}\n  {pointer}"
