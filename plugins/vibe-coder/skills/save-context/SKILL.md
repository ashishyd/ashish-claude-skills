---
name: "save-context"
description: "Use on every coding task: reading, searching, editing, debugging, reviewing or explaining code in this repo. Keeps the session's context small: grep before reading, subagents for whole-project questions, diffs instead of whole files, no restating, short answers, and /compact or a new session when the task changes."
---

# Save Context

Context is a budget. Every file you read and every line you write stays in the session and makes later turns slower, costlier and less accurate. Spend it only on what the task needs.

## Rules

- **Grep before you read.** Find the symbol or string first, then read only those line ranges (`offset`/`limit`). Read a whole file only when it is short or you truly need all of it.
- **Whole-project questions go to a subagent.** "How is this project structured?", "where is X handled?" across many files: send an Explore (or general-purpose) subagent and ask it for a short summary back. Do not pull the files into this session.
- **Show the diff, not the file.** After an edit, show the changed hunk or `git diff`, never the full file. Do not read a file back after editing it to check.
- **Do not restate decisions.** Anything already decided or explained in this session: refer to it in a few words, or not at all.
- **Short by default.** Answer, then stop. Expand only when asked or when the detail changes what the user does next.
- **When the task changes, say so.** On a switch to unrelated work, suggest `/compact` (keep this thread) or a new session (clean start), in one line.

## Not a reason to skip

Saving context never beats correctness. Read what you need to make the change safely: callers, tests, config. If a short answer would hide a risk, say the risk.
