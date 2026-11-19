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

A plugin in `plugins/quality-gates/` with ten short skills and one hook.

| Skill | When Claude uses it |
|-------|---------------------|
| `typescript-types` | Writing or changing TypeScript, or fixing a type error. |
| `vitest-tests` | Writing or fixing unit and component tests with Vitest. |
| `playwright-tests` | Writing or fixing Playwright end-to-end tests. |
| `security-code-audit` | Code touching auth, input, queries, uploads, webhooks or secrets is being written or was just changed. Writing rules for input validation, keeping secrets out of code, password hashing and safe defaults, plus a diff review. |
| `login-and-access` | Sign-in, sessions, roles or permissions are being written or changed. Rules for who signs in, how long they stay in and what each person can see, an access matrix review, and the tests every protected route needs. |
| `personal-data` | Code stores, sends, logs, exports or deletes information about people. Rules for what is kept and why, how it is processed and shared, when it is deleted, and how rules change by country (GDPR, CCPA, LGPD, DPDP and more), with a data-map review. Flags legal questions; does not answer them. |
| `threat-model` | Planning a feature or integration, getting ready to launch, or changing deploy, infra or CI config. Maps where someone could break in (STRIDE at each trust boundary, abuse cases), a launch checklist, automated scans and a penetration test plan. Runs scans only against localhost, or a staging host you name. |
| `design-audit` | A UI component or page was just built or changed: how it looks. |
| `ux-audit` | A user-facing flow was just built or changed: how it works, including accessibility. |
| `claude-md-sync` | A change touched business logic, data model, API, architecture or commands, so CLAUDE.md may need a line. |

The hook runs after each file edit and names the skill that fits the file (by extension and path), once per skill per session. Nothing is added to context for other files, and a skill's body is read only when Claude loads it.

Install it from inside Claude Code (2.1.275 or later):

```
/plugin install quality-gates --marketplace ashishyd/ashish-claude-skills
```

On older versions, run `/plugin marketplace add ashishyd/ashish-claude-skills` first, then `/plugin install quality-gates@ashish-claude-skills`. The hook needs `python3` on the PATH.

**Optional: [obscura](https://github.com/h4ckf0r0day/obscura).** The skills that open pages (`design-audit`, `ux-audit`, `playwright-tests`, feature-flow's `new-feature` and vibe-coder's `tailscale-links`) use obscura first if it is on the PATH. It is a headless browser written in Rust and faster than Chrome. They run it with `--allow-private-network` because obscura blocks localhost by default. Without obscura, they use the Chrome browser tool. Install it from the release binaries or with `cargo`.

## feature-flow plugin

A plugin in `plugins/feature-flow/` that runs every new-feature request the same way:

1. **Plan with Opus.** The `feature-planner` agent (Opus, effort high, read-only) explores the repo and returns explicit dev, test and docs steps, each with its files, a "done when" and a check command, plus any open decisions. Step 1 always puts the feature behind a flag: the repo's existing flag system, or a `FEATURE_<NAME>_ENABLED` env var (default off) when there is none.
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

## vibe-coder plugin

A plugin in `plugins/vibe-coder/` with five skills and one hook.

**Hook `trim_output.py` (PreToolUse, Bash):** noisy commands (installs, builds, test runs, `docker build`, `make`) with no pipe or redirect of their own are rewritten to pipe through a trimmer with `pipefail`, so the exit code is kept. It keeps the first 30 and last 80 lines, up to 60 error or warning lines in between, and collapses repeated lines. Add `# no-trim` to a command, or set `CLAUDE_NO_TRIM=1`, to see everything. It sets no permission decision, so your permission prompts are unchanged.

| Skill | What it does |
|---|---|
| `tailscale-links` | Any link to something running on this machine (preview, review page, dashboard) is published with `tailscale serve`, opened by Claude to check it works, and sent as a Tailscale link, never localhost. Needs Serve enabled on your tailnet. |
| `save-context` | On every coding task: grep before reading, subagents for whole-project questions, diffs instead of whole files, no restating decisions, short answers, and a nudge to `/compact` or start a new session when the task changes. |
| `state-machine-hunter` | Finds implicit state machines (boolean soup, string statuses, step counters, null-as-loading), reports them ranked by user harm with the impossible states each allows, then on your yes makes one explicit at a time (discriminated union, reducer or enum + transition table in the repo's own idiom) behind pinned tests, keeping external shapes unchanged. |
| `bug-triager` | Scores each bug 1-10 on frequency and severity. A product below 5 is drafted as an issue (filed on your yes) and the code is left alone; 5 or more gets a root-cause fix with a test. Data-loss, security and money bugs are always raised. No code for rare or future cases nobody asked about. |
| `improve` | A retro over this project's past sessions. `scripts/session_digest.py` reads the local transcripts and prints only friction (your corrections, denied tool calls, interrupts, repeated tool errors) with the context before each. Claude groups them into patterns (two or more moments), proposes one fix per pattern in the right home (edit an existing rule, a hook plan, a skill lesson, repo `CLAUDE.md`, then `~/.claude/CLAUDE.md` last), and applies only the cards you accept. A run log outside the repo records what was scanned and what you rejected, so nothing is re-proposed. |

Install it with `/plugin install vibe-coder --marketplace ashishyd/ashish-claude-skills`.

## pr-review plugin

A plugin in `plugins/pr-review/` with three skills and no hooks.

| Skill | What it does |
|---|---|
| `reviewer-brief` | Writes a one-screen brief for the human reviewer: what changed and why, where to look hard (`file:line`, riskiest first), how it was verified, what was not, risk if wrong and rollback. Goes into the PR body only on your yes. |
| `agent-spend` | Token usage per repo, branch and PR from your local Claude Code transcripts (`scripts/spend_by_pr.py`), PRs mapped with `gh`. Shows dollars only with a rates file you supply. |
| `pr-splitter` | Plans a large branch as a stack of small PRs, one concern each, that build and pass tests on their own. On your yes it creates the branches from the original (left untouched), checks the stack's final diff equals the original, and asks before pushing. |

Install it with `/plugin install pr-review --marketplace ashishyd/ashish-claude-skills`.

## repo-health plugin

A plugin in `plugins/repo-health/` with three skills and no hooks. They work in any stack.

| Skill | What it does |
|---|---|
| `env-doctor` | Read-only. Compares what the repo declares (runtime versions, package manager, tools, env var names, services) with what this machine has, and gives one fix per gap, blocking gaps first. Never opens `.env` files or prints values. |
| `api-drift` | Lists server routes and client calls across common frameworks, normalises paths, and reports missing routes, method and shape mismatches, and routes with no caller, with `file:line` on both sides. |
| `flag-cleanup` | Inventories feature flags for any vendor or home-made flags, asks which are settled, then removes one flag per change, keeping the winning branch and deleting the losing one. Never changes vendor state. |

Install it with `/plugin install repo-health --marketplace ashishyd/ashish-claude-skills`.

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
