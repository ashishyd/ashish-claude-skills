---
name: "dependency-cycles"
description: "Use when adding an import, moving code between modules or packages, splitting or merging files, or seeing circular import errors, undefined-at-import-time values, or a bundler or linter warning about a dependency cycle."
---

# Dependency Cycles

A cycle means two or more modules cannot be understood, tested or loaded alone. They also fail at runtime in ways that depend on import order. Prevent them by keeping imports pointing one way; detect them before they merge.

## Detect

Run the bundled script on the source root. It reads Python and JS/TS files, resolves relative imports, and prints each group of files that import each other (exit 1 if any):

```bash
python3 <skill folder>/cycles.py src
```

Run it before the change and after it. Only cycles that are new after your change are yours to fix; report the old ones, one line each.

If the repo already has a stronger tool, use that instead: `madge --circular`, `eslint-plugin-import` (`import/no-cycle`), `import-linter`, `cargo` (cycles between crates are a build error). The script does not see dynamic imports or path aliases (`tsconfig` `paths`).

## Symptoms that point to a cycle

- Python: `ImportError: cannot import name X from partially initialized module`.
- JS/TS: a value is `undefined` at import time but fine later; a class "is not a constructor"; `Cannot access 'X' before initialization`.
- A test that imports one module pulls in half the codebase.

## Break the cycle

Find the smallest edge to cut. In order of preference:

| Fix | Use when |
|---|---|
| Move the shared piece (type, constant, helper) into a new module both sides import | Both modules need the same small thing. Most cycles are this. |
| Invert the dependency: the lower layer defines an interface or callback; the higher layer supplies it | A low-level module calls up into a high-level one. |
| Merge the files | They always change together and neither is used alone. |
| Pass the value in as an argument instead of importing it | The import is used by one function. |
| Type-only import (`import type`, `if TYPE_CHECKING:`) | The edge exists only for annotations. It removes the runtime cycle, not the design coupling; say so. |
| Import inside the function | Last resort. It hides the cycle from tools. Add a comment naming the cycle and the fix you deferred. |

Do not fix by reordering imports, by re-exporting through an `index`/`__init__` barrel, or by silencing the linter. Those hide the cycle or make it worse.

## Prevent

- Name the direction before adding an import: domain and utilities at the bottom, services in the middle, entry points (routes, CLI, UI) on top. An import goes down, never up or sideways into a peer that imports you back.
- Before importing module B from A, check that B does not already import A, directly or through a third module (`grep -n "import.*A" B`; the script shows the whole chain).
- Barrel files (`index.ts`, `__init__.py` that re-export everything) join every module below them into one cycle risk. Import from the file that defines the thing.
- Package-level cycles: if two packages in a monorepo or workspace depend on each other, stop and tell the user. The fix is a design change, not an import edit.
- Add the check to CI or the pre-commit step when the user agrees; do not add it unasked.

## Stop and tell the user when

- Breaking the cycle needs a public API change or moves code between packages.
- The cut needs a new module whose name or home is a design choice. Offer two options and recommend one.
- The same cycle is still reported after two fix attempts.

## Report

```markdown
**Cycles before / after:** <n> / <n>
**Cut:** <file A -> file B, and the fix used>
**Evidence:** `python3 <skill folder>/cycles.py <root>` -> <output lines>
**Not seen by the check:** <dynamic imports, aliases, other languages>
**Pre-existing, not fixed:** <one line each, or "nothing">
```

Related: when the loop comes from a package version change, use the `dependency-versions` skill.
