"""v0.10.5 (R12, Derivanta Engine reported 4 import cycles): the four cycles (community<->packs, ptbr<->router,
router<->temporal, compare->patterns->project->router->ptbr) close only through imports inside functions, which
run after every module has loaded. A cycle among *module-level* imports would make import order matter; this test
keeps that from appearing, and checks that every module imports on its own in a fresh interpreter."""
import ast
import subprocess
import sys
import unittest
from collections import defaultdict
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "voznativa"


def module_level_graph() -> dict[str, set[str]]:
    mods = {p.stem for p in PKG.glob("*.py")}
    graph = defaultdict(set)
    for path in PKG.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:   # module level only (also inside top-level if/try blocks)
            stack = [node]
            while stack:
                cur = stack.pop()
                if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    continue
                if isinstance(cur, ast.ImportFrom) and cur.level == 1:
                    names = [cur.module] if cur.module else [a.name for a in cur.names]
                    for name in names:
                        target = name.split(".")[0]
                        if target in mods and target != path.stem:
                            graph[path.stem].add(target)
                stack.extend(ast.iter_child_nodes(cur))
    return graph


def find_cycle(graph):
    state = {}

    def dfs(node, path):
        state[node] = 1
        for nxt in sorted(graph.get(node, ())):
            if state.get(nxt) == 1:
                return path[path.index(nxt):] + [nxt]
            if nxt not in state:
                found = dfs(nxt, path + [nxt])
                if found:
                    return found
        state[node] = 2
        return None

    for start in sorted(graph):
        if start not in state:
            found = dfs(start, [start])
            if found:
                return found
    return None


class ImportGraph(unittest.TestCase):
    def test_no_cycle_among_module_level_imports(self):
        self.assertIsNone(find_cycle(module_level_graph()))

    def test_the_detector_sees_a_cycle(self):
        self.assertEqual(find_cycle({"a": {"b"}, "b": {"a"}}), ["a", "b", "a"])

    def test_cycle_members_import_alone_in_a_fresh_interpreter(self):
        for mod in ("community", "packs", "ptbr", "router", "temporal", "compare", "patterns", "project"):
            done = subprocess.run([sys.executable, "-c", f"import voznativa.{mod}"], cwd=PKG.parent,
                                  capture_output=True, timeout=120)
            self.assertEqual(done.returncode, 0, (mod, done.stderr[-400:]))


if __name__ == "__main__":
    unittest.main()
