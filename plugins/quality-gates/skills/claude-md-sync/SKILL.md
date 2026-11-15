---
name: claude-md-sync
description: Use after changing business logic, domain rules, data models, APIs, architecture, commands, config or dependencies, before calling the work done, to keep CLAUDE.md true to the code. Also when the user says "update CLAUDE.md", "sync the docs" or "is CLAUDE.md still right".
---

# CLAUDE.md Sync

CLAUDE.md is what the next session believes about this repo. After a change, make it true again with the smallest edit. A stale line is worse than a missing one.

## Steps

1. **Scope.** The diff (`git diff` plus staged, or the files named). Find every CLAUDE.md that governs them: the repo root and any in a parent directory of a changed file. Do not open CLAUDE.local.md or files listed in `.gitignore` unless asked.
2. **Classify** each change with the table. Stop with "CLAUDE.md: no update needed (<reason>)" if nothing qualifies.
3. **Read** the governing CLAUDE.md in full. Find the lines the change makes false, incomplete or redundant.
4. **Edit.** Fix the false lines first, then add only what a future session cannot learn from the code quickly. Put each fact in the nearest CLAUDE.md for its directory.
5. **Check.** Every command, path, file name and identifier you wrote exists (grep or run `--help`). Do not run a command that writes, migrates or deploys to verify it.
6. **Report.**

## Does it qualify?

| Change | Update? | What to write |
|---|---|---|
| Business rule, invariant, pricing/limit/eligibility logic, state machine | Yes | The rule in one line, where it is enforced (`path:symbol`) |
| Data model, schema, migration, new entity or field with meaning | Yes | What it means, who owns writes, any constraint not visible in the schema |
| Public API, route, event, job, webhook added/removed/changed contract | Yes | Name, purpose, the non-obvious contract |
| Architecture: new layer, module boundary, service, data flow | Yes | The boundary and the rule ("UI never imports `db/`") |
| Build/test/run/lint command, env var name, required tool or version | Yes | The exact command or variable name (names only, never values) |
| New dependency that replaces a pattern ("use zod, not hand checks") | Yes | The convention |
| Gotcha discovered while making the change | Yes | The trap and how to avoid it |
| Rename/move of something CLAUDE.md names | Yes | Fix the reference |
| Refactor with same behaviour, styling, copy, tests only, bug fix restoring documented behaviour | No | — |

## Writing rules

- Edit in place; do not append a changelog or a "Recent changes" section. CLAUDE.md is current state, not history (git has history).
- One fact per line, imperative or declarative, under ~25 words. Point to code (`src/billing/tax.ts:applyTax`) instead of copying it.
- Keep the file's existing headings and voice. Add a heading only if no existing one fits.
- Delete lines the change made obsolete. A net-zero or shorter file is a fine outcome.
- Never write secrets, tokens, customer data or `.env` values. Variable names only.
- If the root CLAUDE.md is over ~200 lines after your edit, say so in the report; do not restructure it unasked.
- If the repo has no CLAUDE.md, do not create one; say so and suggest `/init` or `repo-agent-guide`.

## Output

```markdown
## CLAUDE.md: UPDATED | NO UPDATE NEEDED | NEEDS DECISION
Files: <CLAUDE.md paths edited>
Changes:
- <file>: <+/-/~> <the line, short> (because <code change>)
Verified: <commands/paths checked>
Open: <anything unsure, e.g. a rule you could not confirm in the code>
```

## Rules

- Write only facts you confirmed in the code or diff. If the intent of a business rule is unclear, write NEEDS DECISION and ask; do not guess the why.
- Touch only CLAUDE.md files. Do not commit.
- When the user's or the repo's instructions conflict with this skill, they win.

## Opus advisor

Key decisions in this skill: a new architecture rule or module boundary, a business-rule wording you cannot confirm in the code, and moving facts between CLAUDE.md files.

Before acting on one, get a second opinion: call the `Agent` tool with `model: "opus"` (`subagent_type` `Plan`, read-only). Give it the decision, each option in one line, the evidence (`file:line`, measurements, the diff) and the constraints. Ask for a pick, the main risk of that pick, and what would change its mind. Do not send secrets or `.env` contents.

- One call per decision, not per finding. Skip it for routine choices the steps above already settle.
- If the advisor disagrees with you, show both views to the user in one line each and let them choose. Do not pick silently on architecture, auth, data model or money.
- In the report, list each advised decision: `Advisor: <decision> -> <pick> (<agreed | overruled because ...>)`.
