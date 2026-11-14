---
name: "repo-agent-guide"
description: "Use when a repository has no CLAUDE.md or AGENTS.md, when the existing one is stale, generic or longer than about 200 lines, or when an AI agent keeps repeating the same mistakes in a codebase."
---

# Repo Agent Guide

The guide is written once by the strongest model, after reading the code, for the weakest model that will ever work in the repo. Every line must be checkable against the code and must change what an agent does.

## Process

1. **Evidence pass.** Read, in this order:
   - manifests and lockfiles (scripts, package manager, runtime version)
   - entry points and routing
   - the data layer and migrations
   - test, lint and CI config
   - `.env.example` for variable names
   - the last 30 commit subjects

   Treat the README as a claim to check. Never open `.env` files, key files or database dumps.
2. **Baseline.** If dependencies are installed, run typecheck, lint and tests and record what already fails. If they are not, write that the baseline was not recorded. Run nothing that writes data.
3. **Trap hunt.** Look for:
   - docs that contradict the code
   - leftover config for tools no longer used
   - two ways of doing one thing (find out which is current)
   - commands that look safe but touch real data or production
   - generated folders
   - code whose order matters
   - gates enforced only in the client
4. **Write** the sections below, in this order.
5. **Verify.** Every command exists in a manifest. Every path exists. Check five rules against the code at random. Fix or delete anything that fails.
6. **Present.** Show the user the result. When replacing an existing guide, list what was removed and why.

## Sections

```markdown
# <Project>

## What this is
3-5 sentences: what it does, who uses it, how the parts talk. State plainly what is real: users, money, production data.

## Folder map
Only the places an agent must find. One line each.

## Commands
Copied from the manifest, with a comment on each. Mark the dangerous ones.

## Things that touch real data
| Action | What it really does |

## Working rules
The owner's standing preferences: what needs asking first (commit, push, deploy, migrations), what never to read.

## Coding rules
Only where this repo differs from what a model would do by default. Name the reference file to copy.

## Design rules
UI repos only: tokens, primitives, states, themes.

## Mistakes a weaker model makes here
| Mistake | Do this instead |
10-25 rows, taken from the trap hunt.

## Before you say a task is done
- [ ] Checklist with the exact commands, ending with: report what was run, what was seen, what was not verified.

## Known baseline (<date>)
What already fails, so it is not blamed on the next change.
```

## Test every line

Delete a line when any of these is true:

- A model would do it anyway ("write clean code", "use meaningful names").
- It cannot be checked against the code.
- A linter, hook or CI job already enforces it. Name the tool once.
- It describes history instead of telling the agent what to do.

## Size and layout

- Keep the root file under about 200 lines.
- In a workspace of several repos, the root file holds what crosses repos: how the parts talk, working rules, the mistakes table, the done checklist. Each repo gets its own file for folder map, commands and coding rules.
- When other AI tools also work in the repo, put the content in `AGENTS.md` and make `CLAUDE.md` a single line: `@AGENTS.md`.

## Rules that must never be broken

Instruction files are advice, and a model can forget advice. For each rule in the guide that protects secrets, production data or deploys, tell the user which permission deny rule or hook would enforce it, and list those at the end of your reply.

## Reply format

1. The guide.
2. Traps found that the user may not know about.
3. Rules that should become deny rules or hooks.
4. What was not verified.