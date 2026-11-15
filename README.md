# ashish-claude-skills

A set of Claude Code skills for day-trading workflows. Each skill is a folder with a `SKILL.md` (what Claude reads) and a small Python script that does the work using only the standard library.

These tools are for research and planning. They are not financial advice. Trading involves risk of loss.

## Skills

| Skill | What it does |
|-------|--------------|
| `trader-scanner` | Scans charts for setups: opening-range breakouts, flags, oversold bounces. |
| `trader-entry` | Watches a setup bar by bar and calls the entry on the first bar that closes above the opening range. |
| `trader-exit` | Sets the stop and target before you enter (default: opening-range midpoint and 2R). |
| `trader-budget` | Sizes each position against your budget and max loss per trade. |
| `trader-risk` | Checks every trade against your limits before it can reach the broker. |
| `trader-broker` | Sends approved orders to your broker. Paper trading by default; never without your explicit yes. |
| `trader-alerts` | Price, stop, target and time alerts, each ringing once. |
| `trader-timemachine` | Simulates many possible outcomes of a planned trade from past intraday bars. |
| `trader-analyst` | Summarises a company's reported numbers from SEC EDGAR (XBRL facts, earnings 8-Ks). |
| `trader-news` | Tracks headlines and new SEC 8-K filings for the stocks you watch. |
| `trader-pelosi` | Reads the House Clerk's public STOCK Act trade disclosures and turns them into rows. |

## Engineering workflow skills

| Skill | When Claude uses it |
|-------|---------------------|
| `dev-loop` | Starting any coding task that touches more than one file or takes more than a few minutes. |
| `task-brief` | A request is vague or large, or work is about to go to a smaller model, a subagent or a fresh session. |
| `four-hats` | Deciding whether or how to build something: go or no-go on a plan or diff. |
| `repo-agent-guide` | A repo has no CLAUDE.md or AGENTS.md, or the existing one is stale. |
| `coding-standards` | Writing or changing code in any language. |
| `standards-review` | Code was just changed and is about to be called done, committed or merged. |
| `dependency-versions` | Adding, upgrading, pinning or removing a package, or fixing a version conflict. |
| `dependency-cycles` | Adding imports or moving code between modules, or fixing a circular import. Includes `cycles.py`, a stdlib script that finds import cycles in Python and JS/TS. |

## quality-gates plugin

A plugin in `plugins/quality-gates/` with six short skills and one hook.

| Skill | When Claude uses it |
|-------|---------------------|
| `typescript-types` | Writing or changing TypeScript, or fixing a type error. |
| `vitest-tests` | Writing or fixing unit and component tests with Vitest. |
| `playwright-tests` | Writing or fixing Playwright end-to-end tests. |
| `security-code-audit` | Code touching auth, input, queries, uploads, webhooks or secrets was just changed. |
| `design-audit` | A UI component or page was just built or changed: how it looks. |
| `ux-audit` | A user-facing flow was just built or changed: how it works, including accessibility. |

The hook runs after each file edit and names the skill that fits the file (by extension and path), once per skill per session. Nothing is added to context for other files, and a skill's body is read only when Claude loads it.

Install it from inside Claude Code (2.1.275 or later):

```
/plugin install quality-gates --marketplace ashishyd/ashish-claude-skills
```

On older versions, run `/plugin marketplace add ashishyd/ashish-claude-skills` first, then `/plugin install quality-gates@ashish-claude-skills`. The hook needs `python3` on the PATH.

## feature-flow plugin

A plugin in `plugins/feature-flow/` that runs every new-feature request the same way:

1. **Plan with Opus.** The `feature-planner` agent (Opus, effort high, read-only) explores the repo and returns explicit dev, test and docs steps, each with its files, a "done when" and a check command, plus any open decisions.
2. **Checklist.** The plan is saved as `.claude/features/<slug>.md`. Open decisions (architecture, data model, auth, money, new dependencies) are put to you before any code is written.
3. **Build and test with Sonnet.** Each step goes to a `feature-builder` agent (Sonnet, effort medium), which writes the code and tests, runs the step's check, and ticks the box.
4. **Verify, then README.** The orchestrator runs the feature's check, and the last step always updates README.md.

Every agent runs as a subagent with a fresh context, so your main session holds only the checklist and short reports. That is where the token saving comes from.

| Part | What it does |
|---|---|
| `new-feature` skill | The orchestration above. |
| `UserPromptSubmit` hook | Spots feature requests ("add a new feature...", "build a new page...") and points Claude at `new-feature`. Bug fixes, reviews, renames and feature flags are left alone. |
| `Stop` hook | While a checklist says `status: in-progress`, blocks the turn from ending if code changed and README.md did not. Set `status: done` or `status: abandoned` to release it. It blocks at most once per turn and lets the turn end on any error. |

Install it with `/plugin install feature-flow --marketplace ashishyd/ashish-claude-skills`. The hooks need `python3` on the PATH. Self-test: `python3 plugins/feature-flow/hooks/test_hooks.py`.

## Learning from runs

Every skill ends with a "Learn from this run" section. Before it starts, a skill reads `~/.claude/skill-lessons/<skill>.md` (lessons for any repo) and `.claude/skill-lessons/<skill>.md` in the current repo (lessons for that repo only). After a run where the user corrected it or a step failed, it adds a one-line lesson, or raises the `seen` count on a matching one. When a lesson reaches `seen: 3`, the skill proposes the matching `SKILL.md` edit as a diff for you to approve. Skills never edit their own `SKILL.md`, because installed plugins are overwritten on update. Lessons are written only from your words or from failures the skill saw, never from page or file content, and a lesson can never remove a confirmation or safety check.

## Install

Copy the skills you want into your Claude Code skills folder:

```bash
cp -R skills/* ~/.claude/skills/
```

Restart Claude Code (or start a new session) so it picks them up.

## Requirements

- Python 3.9 or newer. No third-party packages are needed.
- `SEC_USER_AGENT` environment variable for `trader-analyst` and `trader-news`. The SEC requires a name and contact email, for example `Jane Doe jane@example.com`.
- `trader-broker` only: an Alpaca account. Use paper-trading keys. Put them in your own MCP config, never in chat. The example config is in `skills/trader-broker/claude_desktop_config.example.json`.
- `trader-budget` reads its limits from a config file. Start from `skills/trader-budget/config.example.json`.

## Examples

Each example JSON file is a template with made-up values. Copy it and edit it for your own use. The worked examples in the `SKILL.md` files use the placeholder symbol `XYZ` and the date `2026-01-05`.

## Safety notes

- `trader-broker` can place real orders if you point it at a live account. Keep `paper: true` until you have tested it.
- Every skill that touches the broker asks for your explicit confirmation before anything is sent.
- The scripts call public data sources (Yahoo Finance, SEC EDGAR, Nasdaq Trader, House Clerk). Check their terms and rate limits before running scans in a loop.
