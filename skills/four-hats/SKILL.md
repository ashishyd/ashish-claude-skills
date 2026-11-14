---
name: "four-hats"
description: "Use when deciding whether or how to build something: a new feature, an architecture or data-model choice, a rewrite, a new dependency or service, or a plan or diff that needs a go or no-go before work continues."
---

# Four Hats

One person holding four roles tends to answer only as the role they enjoy most. This review asks each role in turn and forces one verdict.

The order is fixed, because the earlier hats can stop the work most cheaply: Founder, Architect, Principal Engineer, Engineering Manager.

## Size it first

| Work | What to produce |
|---|---|
| Under an hour | Nothing. Do the work. |
| About a day | Verdict and the hat table only |
| More than a day, or any one-way door | The full output below |

## The hats

Read the relevant code, schema and instruction file before answering. Each finding names something specific: a file, a table, a number, a user. If there is no evidence, write the word `assumption`.

**1. Founder: should this exist?**
- Who needs it, and what do they do today without it?
- What is the smallest version that tests the bet?
- What does it cost to not do it this month?
- What result would make us stop or remove it?

**2. Architect: where does it live and what does it lock in?**
- Which existing boundary owns this, and what does it duplicate?
- What data does it create or change, and who else reads that data?
- Which parts are one-way doors: schema, public API, auth model, vendor, pricing?
- What breaks first at ten times the load, and is it acceptable to ignore that now?

**3. Principal Engineer: how does it fail?**
- What happens when a dependency is down, a request is retried, two run at once, or the input is hostile?
- At what level is it tested, and what signal says it is broken in production?
- What is the simplest implementation, and what can be deleted from the plan?
- What is the blast radius of a bug here?

**4. Engineering Manager: can it be delivered and kept alive?**
- How long is it, counting human review time and not only generation time?
- What does it displace?
- Who can fix it at 3am, and is that more than one person?
- Can it ship in slices, and how is each slice rolled back?

## Output

```markdown
## Verdict: BUILD | BUILD SMALLER | SPIKE FIRST | DEFER | DON'T
<one sentence: the deciding reason>

| Hat | Finding | Risk |
|---|---|---|
| Founder | <one line> | L/M/H |
| Architect | <one line> | L/M/H |
| Principal Engineer | <one line> | L/M/H |
| Engineering Manager | <one line> | L/M/H |

## One-way doors
- <decision>: <why it is hard to undo> -> <how to keep it reversible, or "accept">

## Smallest shippable slice
<what ships first and what it proves>

## Questions only the human can answer
- <at most three>

## Next step
<one action>
```

## Rules for the verdict

- The verdict comes first and is one of the five words.
- When two hats disagree, state the disagreement in the table. The verdict follows the higher risk.
- A High risk from the Founder hat caps the verdict at SPIKE FIRST.
- An unmitigated one-way door caps the verdict at BUILD SMALLER.
- Report findings as they are. A plan the user is attached to gets the same verdict as any other plan.

## Reviewing a diff with the four hats

- Founder: does the diff do only what was asked?
- Architect: did it cross a boundary or add a second way to do something?
- Principal Engineer: which failure case has no test?
- Engineering Manager: can a reviewer read it in one sitting? If not, name where to split it.