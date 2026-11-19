"""VIS-01: дерево виводу."""
import json
import unittest

from sipl.parser import parse_tree
from sipl import visualization as V
from .helpers import read_example


class VisualizationTests(unittest.TestCase):
    def setUp(self):
        self.src = read_example("power.sipl")
        self.tree = parse_tree(self.src)

    def test_leaf_check_ok(self):
        ok, _, _ = V.check_syntax(self.tree, self.src)
        self.assertTrue(ok)

    def test_leaves_count_matches_practicum(self):
        # у практикумі для цієї програми 24 листки
        self.assertEqual(len(self.tree.leaves()), 24)
        self.assertTrue(V.leaves_listing(self.tree).startswith("1 begin 2 R 3 := 4 1 5 ;"))

    def test_text(self):
        text = V.tree_to_text(self.tree)
        self.assertTrue(text.startswith("<програма> (P1)"))
        self.assertIn("[24] end", text)

    def test_json_links_nodes_to_source(self):
        data = json.loads(V.tree_to_json(self.tree, self.src))
        self.assertEqual(data["kind"], "<програма>")
        self.assertEqual(data["source"], self.src.strip())
        first_leaf = data["children"][0]
        self.assertEqual(first_leaf["text"], "begin")
        self.assertEqual(first_leaf["span"]["line"], 1)

    def test_dot(self):
        dot = V.tree_to_dot(self.tree)
        self.assertTrue(dot.startswith("digraph"))
        self.assertTrue(dot.rstrip().endswith("}"))
        self.assertEqual(dot.count("->"), dot.count("[shape=") - 1)

    def test_negative_number_leaf(self):
        src = "begin X := -1 end"
        ok, _, _ = V.check_syntax(parse_tree(src), src)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
