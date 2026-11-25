---
name: session-fit
description: Use when a switchboard context hint says the session is large, when the user asks whether to start a new session or chat, how to cut the cost of a long session, or how to carry an artifact, decision or half-done task into a new session without losing it.
---

# Session Fit

Every message re-sends the whole session. Prompt caching makes that cheaper, but it still costs something on every message and keeps growing. A long session earns its cost only while the work builds on it. When the work moves on, a fresh session that starts from a short brief costs less per message.

The usual reason to stay is an artifact made here. A new session can open any artifact by its URL, though, so the URL list and a few lines of decisions carry over everything that matters.

## Steps

1. **Measure.** Use the size from the switchboard hint (`~<n>k tokens`). Without a hint, take the last `"usage"` in the session transcript: `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`.
2. **Pick one** with the table. When unsure, stay: a lost thread costs more than the tokens.
3. **Say it in one line**, with the size and the reason. Then do the work, or the handoff if the user agrees.

| The prompt | Do |
|---|---|
| Builds on this chat: same feature, same artifact, a correction, "now do X too" | **Stay.** |
| Self-contained, and only its result matters here: a search, a scan, a review, an isolated edit | **Subagent** (`Agent` tool), with a complete brief. Its tokens stay out of this session. |
| Unrelated to the work here, or a new phase after this one is done | **New session**, with a carry-over brief. |
| Unrelated but tiny (one question, one edit) | **Stay.** A handoff costs more than one cheap message. |

## Carry-over brief

Write it from this conversation, in your own words, under 40 lines:

```markdown
# Carry-over: <task>  (<YYYY-MM-DD>, from session <id or title>)

## Goal
<one or two lines: what the new session must finish>

## Artifacts
- <https://claude.ai/artifact/...>: <what it is, its local source file if any>
  Reopen with `Artifact` action `read` and this url. Update it by publishing with `url` set to it, so the link stays the same.

## Decided
- <decision>, because <reason>

## Open
- <next step or unanswered question>

## Files
- <repo-relative path>: <why it matters>
```

- Take the artifact URLs from the switchboard hint, or from `Artifact` calls in this session. Use `Artifact` action `list` to fill gaps. Never guess a URL.
- Keep secrets, tokens and personal data out of the brief.

## Hand it over

- **Desktop app:** start the new session with `mcp__ccd_session__start_session` (`context: "fresh"`) and the brief as its prompt. Use `initiation: "offer"` so the user picks.
- **CLI or no session tool:** save it to `.claude/handoffs/<YYYY-MM-DD>-<slug>.md` at the repo root (add `.claude/handoffs/` to that repo's `.gitignore` if it is missing, so briefs are never committed) and give the user the command to run:
  `claude "Read .claude/handoffs/<file>.md and continue from it"`
- **In the new session:** read the brief first, then `Artifact` action `read` on each URL before editing it. That pulls the live page into a local file you can edit. Then publish with that `url`.

## Rules

- Suggest a new session only when one of the table's rows says so; one line, then carry on.
- Never move the user to a new session without their yes.
- One subagent per self-contained job; do not nest them.
