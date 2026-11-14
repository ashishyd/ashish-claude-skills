---
name: "task-brief"
description: "Use when a coding request is vague or large, when work is about to be handed to a smaller or cheaper model, a subagent or a fresh session, or when a previous attempt at the task went wrong."
---

# Task Brief

A weaker model succeeds when the task leaves nothing to infer. A brief is the thinking done once, up front, by the strongest reasoner available, so the executor only executes.

Skip this for a change where the file and the edit are already named.

## Steps

1. **Read before writing.** Open the project's instruction file (CLAUDE.md or AGENTS.md), the files the task touches, and one neighbouring feature that already does something similar. Never write a brief from memory of the codebase.
2. **Resolve unknowns.** Anything you would have to guess goes to the user in one batch of at most three questions. Whatever stays unanswered is written in the brief as an assumption.
3. **Fill the template.** Every section is required. Write `none` in a section that has nothing; do not delete it.
4. **Size check.** If the brief touches more than five files, more than one repo, or mixes a schema change with UI work, split it into ordered briefs. Each one must be verifiable by itself.
5. **Hand over.** Show the brief to the user. After approval, execute it or dispatch it.

## Template

```markdown
# Brief: <verb + object, under 10 words>

## Outcome
One sentence: what is true when this is done that is not true now, and who notices.

## Why
One or two sentences. The reason is what lets the executor make the unlisted decisions the right way.

## Read first
- <path>: <why> (at most 6 paths; the file to copy the pattern from goes first)

## Change
1. <file>: <what changes>
2. ...
Each step is small enough to verify alone.

## Do not
- <the tempting out-of-scope work: refactors, renames, new dependencies, adjacent bugs>

## Decisions already made
- <choice>: <reason>. The executor does not reopen these.

## Assumptions
- <what was guessed and what changes if it is wrong>

## Verify
- `<exact command>` -> <expected result>
- Behaviour check: <what to open, click or call, and what you should see>

## Stop and report if
- a listed file is missing or does not look as described
- the change needs a file that is not listed
- a verify command still fails after two fix attempts
- anything touches secrets, production data, migrations or deploys

## Report
Files changed. Commands run with their results. What was not verified. Open questions.
```

## Check the brief before handing over

- A contractor with no access to this chat could do the work from the brief alone.
- Every "it", "this" and "the bug" is replaced by a name or a path.
- Every step names its cases. Rewrite any step that says "appropriately", "as needed" or "handle edge cases".
- Verify commands are copied from the project's manifest or instruction file.
- The Do-not list has at least one entry: there is always something tempting nearby.

## Which model gets the work

| Keep on the strongest model | Hand to the smaller model with a brief |
|---|---|
| Unclear requirements | Executing a written brief |
| Architecture, data model, public API | A mechanical change that copies an existing pattern |
| A bug whose cause is unknown | Tests for behaviour that is already specified |
| Auth, money, permissions, migrations | Formatting, renames, wiring |

**Escalation rule:** two failed attempts at the same step means the brief is wrong, not the wording of the prompt. Stop. Take the brief plus the failure evidence back to the strongest model and rewrite the step.