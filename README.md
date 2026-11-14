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
