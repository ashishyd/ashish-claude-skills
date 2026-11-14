#!/usr/bin/env python3
"""Find import cycles in a Python or JS/TS source tree. Stdlib only.

Usage: python3 cycles.py [ROOT]   (default: .)
Exit code 1 if any cycle is found, 0 if none.
shortcut: only static imports are seen (no dynamic import(), no importlib),
and JS path aliases (tsconfig "paths") are not resolved. Upgrade to
madge / import-linter when you need alias or layer-contract support.
"""
import ast
import os
import re
import sys

SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "target"}
JS_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
JS_IMPORT = re.compile(r"""(?:from|import|require\()\s*\(?\s*['"](\.[^'"]*)['"]""")


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            yield os.path.join(d, f)


def py_module(root, path):
    parts = os.path.relpath(path, root)[:-3].split(os.sep)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def py_edges(root, files):
    mods = {py_module(root, f): f for f in files}
    for mod, path in mods.items():
        is_pkg = os.path.basename(path) == "__init__.py"
        pkg = mod.split(".") if is_pkg else mod.split(".")[:-1]
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for n in ast.walk(tree):
            names = []
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                base = pkg[: len(pkg) - (n.level - 1)] if n.level else []
                head = ".".join(base + ([n.module] if n.module else []))
                names = [head] + [f"{head}.{a.name}".strip(".") for a in n.names]
            for name in names:
                while name and name not in mods:  # longest known prefix
                    name = name.rpartition(".")[0]
                if name and name != mod:
                    yield path, mods[name]


def js_resolve(frm, spec):
    base = os.path.normpath(os.path.join(os.path.dirname(frm), spec))
    for c in [base] + [base + e for e in JS_EXT] + [os.path.join(base, "index" + e) for e in JS_EXT]:
        if os.path.isfile(c):
            return c


def js_edges(files):
    for path in files:
        for spec in JS_IMPORT.findall(open(path, encoding="utf-8", errors="ignore").read()):
            target = js_resolve(path, spec)
            if target and target != path:
                yield path, target


def sccs(graph):
    """Tarjan, iterative so deep trees do not hit the recursion limit."""
    index, low, on, stack, out, n = {}, {}, set(), [], [], [0]
    for start in graph:
        if start in index:
            continue
        work = [(start, iter(graph[start]))]
        index[start] = low[start] = n[0]; n[0] += 1; stack.append(start); on.add(start)
        while work:
            v, it = work[-1]
            for w in it:
                if w not in index:
                    index[w] = low[w] = n[0]; n[0] += 1; stack.append(w); on.add(w)
                    work.append((w, iter(graph.get(w, ()))))
                    break
                if w in on:
                    low[v] = min(low[v], index[w])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[v])
                if low[v] == index[v]:
                    comp = []
                    while True:
                        w = stack.pop(); on.discard(w); comp.append(w)
                        if w == v:
                            break
                    if len(comp) > 1:
                        out.append(sorted(comp))
    return out


def main(root):
    files = list(walk(root))
    graph = {}
    py = [f for f in files if f.endswith(".py")]
    js = [f for f in files if f.endswith(JS_EXT)]
    for a, b in list(py_edges(root, py)) + list(js_edges(js)):
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set())
    cycles = sccs(graph)
    for i, comp in enumerate(cycles, 1):
        print(f"cycle {i} ({len(comp)} files):")
        for f in comp:
            print(f"  {os.path.relpath(f, root)} -> " + ", ".join(sorted(os.path.relpath(t, root) for t in graph[f] if t in comp)))
    print(f"{len(cycles)} cycle group(s) in {len(graph)} files")
    return 1 if cycles else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
