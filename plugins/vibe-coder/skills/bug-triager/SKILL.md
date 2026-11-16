---
name: "bug-triager"
description: "Use when a bug, edge case, failing case or code-review finding turns up and you must decide whether to fix it now; when tempted to add handling for a rare or hypothetical case; or when the user asks to triage, prioritise or rate bugs. Scores each one on frequency and severity (1-10 each); a product below 5 becomes an issue and the code is left alone."
---

# Bug Triager

Not every bug is worth a code change now. Score it, then act on the score.

## Score

Give each bug two scores from 1 to 10, one line of evidence each:

| Score | 1 | 5 | 10 |
|---|---|---|---|
| **Frequency**: how often real users hit it | needs an unusual input nobody has reported | some users, some of the time | every user, every time on a main path |
| **Severity**: how bad it is when they do | cosmetic, easy to work around | a feature breaks, there is a workaround | data loss, a security hole, money wrong, the app down |

**Priority = frequency × severity.**

Base frequency on evidence (logs, reports, how common the input is), not on what is possible. When unsure, choose the lower frequency and say so.

## Act

- **Below 5 → file it, leave the code alone.** Draft an issue: title, steps to reproduce, both scores with the reason for each, and the suspected cause with `file:line`. Show the draft and ask before running `gh issue create` (filing is public). If the repo has no issue tracker, or the user says no, list it under "Noticed, not fixed" in your report.
- **5 or more → fix it**, smallest fix at the root cause, plus a test that reproduces it.
- **Severity 9-10 (data loss, security, money)**: always tell the user now, whatever the product, and do not settle it by score alone.

Show the scores in one table before acting on several bugs:

| Bug | Freq | Sev | Priority | Action |
|---|---|---|---|---|

## Do not

- Design for rare or future cases nobody asked about: no extra guards, options, retries or abstractions "just in case". A case that only exists in your head gets no code and no issue.
- Raise a score to justify a fix you want to make, or bundle low-scoring fixes into an unrelated change.
- Use this to skip a bug the user asked you to fix; their request wins.
