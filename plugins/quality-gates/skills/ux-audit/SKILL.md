---
name: ux-audit
description: Use when a user-facing flow, form, page or interactive component has just been built or changed and needs a usability and accessibility check, when the user asks for a UI/UX review, or when users get stuck, confused or drop off in a flow.
---

# UX Audit

Do the task the way the user would and record where it breaks, slows or confuses. This skill audits how the interface works; `design-audit` covers how it looks.

## Set up

1. Name the user and the task in one line: "A new customer adds a card and pays an invoice."
2. Open the app with a browser tool and do the task from the entry point to the end state. Then do it again with the keyboard only.
3. No way to run it: walk the flow from the code, and say so at the top of the report.

## Checklist

| Area | Ask |
|---|---|
| Flow | How many steps, and is each needed? Any dead end? Do back, refresh and a shared link keep the user's place? |
| Feedback | Does every action respond at once? Is there a loading sign for waits over a second, and a clear success message? |
| States | Does each screen handle empty, loading, error, partial, no permission, offline, and one, many and very long items? |
| Errors | Does the message say what happened and how to fix it, next to the field, with the user's input kept? |
| Forms | Visible labels? Right input type and `autocomplete`? Validation on blur or submit, not on each key? Sensible defaults? |
| Destructive actions | Undo, or a confirmation that names what will be lost? |
| Wayfinding | Does the user know where they are and what happens next? Page title and focus updated on route change? |
| Copy | Do buttons say what they do ("Send invoice", not "Submit")? One word for one thing throughout? |
| Keyboard | Is everything reachable in a sensible order? Focus always visible? Escape closes overlays, and focus returns? No trap? |
| Screen reader | Real `<button>`, `<a>`, `<label>` and headings in order? Names on icon buttons? Alt text? Async changes announced? |
| Sight and motor | Usable at 200% zoom? Targets at least 24px? Nothing shown by colour alone? |
| Mobile | Main action within thumb reach? Does the keyboard cover the field or the submit button? |
| Perceived speed | Does content jump as it loads? Is the first useful thing shown quickly? |

Run axe or Lighthouse if the repo or the browser tool has it. They find about a third of accessibility problems; the keyboard pass finds the rest.

## Severity

- **Blocker:** a user cannot finish the task, or a WCAG 2.2 A failure.
- **Major:** a user finishes with struggle or error, or a WCAG 2.2 AA failure.
- **Minor:** friction. At most five.

## Every finding

```
Step <n>: <what the user is doing> [SEVERITY]
Happens: <what the user meets>
Evidence: <screenshot or file:line>
Source: <usability heuristic or WCAG criterion number>
Fix: <the change>
```

## Output

```markdown
## Verdict: SHIP | FIX FIRST
User and task: <one line> | Evidence: used the app | code only
Passes done: mouse | keyboard | screen-reader tree | mobile width

### Blockers
### Major
### Minor
### Not checked
```

## Rules

- Report findings; change code only when asked.
- Every finding names the step and a source. Preference with no source is labelled `opinion` and filed under Minor.
- Audit the flow that exists. Do not propose new features.
