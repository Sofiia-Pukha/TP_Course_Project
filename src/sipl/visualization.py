"""Відображення дерева виводу: текст, JSON, DOT та перевірка за листками."""
import json

from .lexer import tokenize
from .parse_tree import ParseNode


def _numbering(root):
    return {id(leaf): i for i, leaf in enumerate(root.leaves(), start=1)}


def tree_to_text(root):
    num = _numbering(root)
    lines = []

    def walk(node, prefix, is_last, is_root):
        if node.is_leaf:
            label = f"[{num[id(node)]}] {node.text}"
        else:
            label = f"{node.kind} ({node.rule})"
        if is_root:
            lines.append(label)
            child_prefix = ""
        else:
            lines.append(prefix + ("└── " if is_last else "├── ") + label)
            child_prefix = prefix + ("    " if is_last else "│   ")
        for i, ch in enumerate(node.children):
            walk(ch, child_prefix, i == len(node.children) - 1, False)

    walk(root, "", True, True)
    return "\n".join(lines)


def tree_to_dict(node, source=None):
    d = {"kind": node.kind, "rule": node.rule, "span": node.span.to_dict()}
    if source is not None:
        d["source"] = node.span.text(source)
    if node.is_leaf:
        d["text"] = node.text
    else:
        d["children"] = [tree_to_dict(c, source) for c in node.children]
    return d


def tree_to_json(root, source=None):
    return json.dumps(tree_to_dict(root, source), ensure_ascii=False, indent=2)


def _esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def tree_to_dot(root):
    num = _numbering(root)
    lines = ["digraph parse_tree {", '  node [fontname="Helvetica"];']
    counter = [0]

    def walk(node):
        my = counter[0]
        counter[0] += 1
        if node.is_leaf:
            lines.append(f'  n{my} [shape=plaintext, label="{_esc(node.text)}\\n({num[id(node)]})"];')
        else:
            lines.append(f'  n{my} [shape=box, label="{_esc(node.kind)}\\n{node.rule}"];')
        for ch in node.children:
            child_id = walk(ch)
            lines.append(f"  n{my} -> n{child_id};")
        return my

    walk(root)
    lines.append("}")
    return "\n".join(lines)


def leaves_listing(root):
    """Листки з номерами обходу зліва направо, як у практикумі."""
    return " ".join(f"{i} {leaf.text}" for i, leaf in enumerate(root.leaves(), start=1))


def check_syntax(root, source):
    """Перевірка синтаксичної правильності: слова в листках, прочитані зліва направо,
    мають збігатися з програмою. Повертає (збіглось?, текст з листків, текст програми)."""
    from_leaves = "".join(leaf.text for leaf in root.leaves())
    from_source = "".join(t.text for t in tokenize(source))
    return from_leaves == from_source, from_leaves, from_source
