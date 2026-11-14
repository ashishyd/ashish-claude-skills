---
name: "standards-review"
description: "Use when code has just been written or changed and before it is called done, committed or merged, or when the user asks whether code follows coding standards or best practices."
---

# Standards Review

Review the change against the standard that governs it, with evidence for every finding. Tools check what tools can check; you check what they cannot. You report findings; you change code only when asked.

## Steps

1. **Scope.** Take the diff (`git diff` plus staged changes) or the files the user named. Review the changed lines and the code they call.
2. **Standard.** For each file, work out the governing standard using the order of authority in the `coding-standards` skill: project instructions and enforced config, then surrounding code, then the language standard. Load that skill if it is not loaded.
3. **Machines first.** Run the formatter check, linter, type checker and the tests covering the changed files, with the project's own commands. Record each command and its result.
4. **Read pass.** Read the diff from the files, not from memory, in the order below.
5. **Classify and report** in the output format.
6. **After fixes.** Re-run step 3 and report again.

## Read pass, in this order

| Area | Ask |
|---|---|
| Correctness | Does it do what was asked, including empty, null, zero, duplicate and very large inputs? Any off-by-one or wrong operator? |
| Security | Is input validated at the boundary? Any string-built query or command? Is authorisation checked on the server? Any secret or personal data in code or logs? |
| Errors | Is any error swallowed or turned into a default value? Does each failure reach a caller or a log with context? |
| Types and contracts | Any untyped value crossing a module boundary? Do both sides of a changed API still agree? |
| Concurrency and resources | Any un-awaited call, missing timeout, unclosed handle, or retry that is unsafe to repeat? |
| Tests | Does new logic have a test that would fail if the logic were wrong? Is any test asserting implementation detail? |
| Naming and readability | Would a new reader understand each name without the diff description? Any function doing two jobs? |
| Idiom | Is the code written the way this language and framework version expect, or transliterated from another? |
| Consistency | Does it match the neighbouring files' structure, helpers and error style? Does it add a second way to do something? |

## Severity

- **BLOCKER:** a bug, a security hole, data loss, or a break of a rule the project marks as never.
- **SHOULD:** a standards violation with a real maintenance or reliability cost.
- **NIT:** style that no formatter catches. At most five.

## Every finding has four parts

```
<file>:<line> [SEVERITY] <rule broken>
Source: <project instruction file | linter rule id | PEP 8 | Effective Go | ...>
Why here: <the concrete consequence in this code>
Fix: <the change, as a snippet of at most 10 lines>
```

A finding with no source is labelled `opinion` and filed under nits.

## Output

```markdown
## Verdict: PASS | PASS WITH FIXES | FAIL
Standard applied: <one line per language in the diff>

Tools:
- `<command>` -> <result>

### Blockers
### Should fix
### Nits
### Pre-existing, not from this change
<at most three, one line each>
### Not checked
<what could not be run or read, and why>
```

## Rules

- The verdict comes first. Any blocker means FAIL.
- For issues a formatter or linter fixes automatically, give the one command to run and stop there.
- Problems that existed before the change go in their own section and do not affect the verdict.
- When nothing is wrong, write "No findings" and list what was checked.
- The report contains findings only: no praise and no summary of what the code does.
- When the code under review was written in this same session, say so in the report. A fresh session or a separate reviewer agent gives a more independent read.