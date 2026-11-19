import pathlib

EXAMPLES = pathlib.Path(__file__).resolve().parent.parent / "examples"


def read_example(name):
    return (EXAMPLES / name).read_text(encoding="utf-8")
