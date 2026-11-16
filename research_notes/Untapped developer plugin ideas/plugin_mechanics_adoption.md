# Claude Code Plugin Mechanics and Adoption (as of Nov 2026)

## What do Anthropic docs say about plugin structure, hook events, skill descriptions/triggering, and marketplaces?

### Takeaway
A plugin is a `.claude-plugin/plugin.json` plus convention folders (skills, commands, agents, hooks, MCP, LSP, output-styles, monitors, themes, workflows, bin). Hooks now cover 33 lifecycle events with five handler types (command, http, mcp_tool, prompt, agent). Skills trigger only from a description truncated at 1,536 chars, inside a listing budget of ~1% of the context window, so the description is the whole trigger surface.

### Cited Findings
**Plugin structure**
- Components and default locations: `skills/<name>/SKILL.md`, `commands/*.md`, `agents/*.md`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`, `output-styles/`, `monitors/monitors.json` (experimental), `themes/` (experimental), `workflows/*.js`, `bin/` (put on the Bash tool's PATH while the plugin is enabled). — [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)
- `plugin.json` fields include `name` (required, namespaces every component), `version` ("keeps users on that version until you change it"), `dependencies` (other plugins that must be enabled), `defaultEnabled`, `userConfig`, `channels`, and directory-listing fields (`icon`, `documentationUrl`, `privacyPolicyUrl`, etc.) that Claude Code itself does not read. — [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)
- `userConfig` gives a typed settings dialog (`string|number|boolean|directory|file`, `sensitive: true` stores in secure storage); values reach hooks as `CLAUDE_PLUGIN_OPTION_<KEY>`. `options` pickers require Claude Code v2.1.271+, and older clients cannot load the plugin at all. — [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)
- `${CLAUDE_PLUGIN_ROOT}` (install dir), `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/<id>/`, persisted across updates: use it for caches, node_modules, state), `${CLAUDE_PROJECT_DIR}`. These are NOT in the env of Bash commands Claude runs. — [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)
- Constraints: a plugin-root `CLAUDE.md` is not loaded as context; claude.ai and Cowork will not install a plugin that has `bin/`; strict objects (userConfig, channels, lspServers, monitors) with unknown keys make the plugin fail to load; paths must be relative `./` and cannot escape the root. Monitors do not start under `-p`. — [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)
- Statusline is not listed as a plugin component on the manifest reference page. — [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)

**Hook events (33 listed)**
- SessionStart, Setup, UserPromptSubmit, UserPromptExpansion, PreToolUse, PermissionRequest, PermissionDenied, PostToolUse, PostToolUseFailure, PostToolBatch, Notification, MessageDisplay, SubagentStart, SubagentStop, TaskCreated, TaskCompleted, Stop, StopFailure, TeammateIdle, InstructionsLoaded, ConfigChange, CwdChanged, DirectoryAdded, FileChanged (matcher = filenames to watch), WorktreeCreate, WorktreeRemove, PreCompact, PostCompact, PreModelSwitch, PostModelSwitch, Elicitation, ElicitationResult, SessionEnd. — [Hooks reference](https://code.claude.com/docs/en/hooks)
- Handler types: `command`, `http`, `mcp_tool`, `prompt`, `agent`; most tool/turn events accept all five, config/compaction/worktree events accept only command/http/mcp_tool. — [Hooks reference](https://code.claude.com/docs/en/hooks)
- Key outputs: PreToolUse `permissionDecision`, `updatedInput` (rewrite the call), `additionalContext`; PostToolUse `updatedToolOutput`/`updatedMCPToolOutput` (rewrite what the model sees), `decision`/`reason`; PostToolBatch can inject context or stop before the next model call; Stop/SubagentStop `decision: block` + reason forces continuation; UserPromptSubmit can set `sessionTitle` and `suppressOriginalPrompt`; PermissionDenied can return `retry: true`. — [Hooks reference](https://code.claude.com/docs/en/hooks)
- Skills can register their own hooks in frontmatter (`hooks:`), active for the rest of the session once the skill is invoked. — [Skills docs](https://code.claude.com/docs/en/skills)

**Skill descriptions and triggering**
- Claude loads a listing of names + descriptions; `description` + `when_to_use` truncated at 1,536 chars; "Put the key use case first". Listing budget is 1% of context window; on overflow, descriptions of least-invoked skills are dropped first (`skillListingBudgetFraction`, `SLASH_COMMAND_TOOL_CHAR_BUDGET` raise it). — [Skills docs](https://code.claude.com/docs/en/skills)
- Frontmatter: `disable-model-invocation` (manual only), `allowed-tools`, `context: fork` (run in subagent), `paths` (globs; auto-load only on matching files), `hooks`. Body loads only when used. — [Skills docs](https://code.claude.com/docs/en/skills)
- Troubleshooting: not triggering -> add words users naturally say; triggering too often -> narrow description or `disable-model-invocation: true`. — [Skills docs](https://code.claude.com/docs/en/skills)
- Authoring guidance: third person, what + when ("Use when..."), SKILL.md under 500 lines, references one level deep, TOC on reference files >100 lines, low-freedom scripts for fragile operations, build ~3 eval scenarios before writing much. — [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

**Marketplaces**
- Official marketplace `claude-plugins-official` is built in; 101 plugins as of March 2026 (33 Anthropic-built incl. 12 LSP plugins, 68 partner plugins). Community indexes: ClaudePluginHub (14,083+ indexed), Build with Claude (2,865 marketplaces), claude-plugins.dev. — [BuildToLaunch, Mar 2026](https://buildtolaunch.substack.com/p/best-claude-code-plugins-tested-review)
- Install path for a GitHub marketplace: `/plugin marketplace add owner/repo` then `/plugin install name@marketplace`. — [Firecrawl blog](https://www.firecrawl.dev/blog/best-claude-code-skills)
- Plugin manifest has an `experimental.evals` directory, and `claude plugin validate` exists, i.e. first-party validation/eval tooling for authors. — [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)

### Inferences
- `${CLAUDE_PLUGIN_DATA}` + SessionStart/PostCompact `additionalContext` = a supported, update-safe place for durable per-user state (memory, ledgers, baselines).
- Because `bin/` blocks claude.ai/Cowork installs, a plugin wanting cross-surface reach should ship scripts under `scripts/` invoked via hooks rather than `bin/`.
- The 1%-budget + least-invoked-dropped rule means a plugin bundling many skills can silently lose triggering for its rarely used ones; few, sharply described skills beat big packs.

### Gaps
- Marketplace page scrape did not return details on `marketplace.json` source types, auto-update, `extraKnownMarketplaces`, or the official-directory submission process; verify at https://code.claude.com/docs/en/plugin-marketplaces directly.
- Statusline as a plugin component is unconfirmed.

## Which hook-based or deterministic-check ideas are uniquely possible in Claude Code and under-used?

### Takeaway
The newer events (PostToolBatch, FileChanged, CwdChanged, InstructionsLoaded, PostCompact, PermissionDenied, StopFailure, Pre/PostModelSwitch) and output-rewriting fields (`updatedInput`, `updatedToolOutput`) allow deterministic harness-side behaviour that prompt-only tools cannot do. GitHub issues show users asking for exactly these as built-ins, which signals plugin openings.

### Cited Findings
- Requested as built-ins (so plugin-fillable): "Run only the tests affected by Claude's edits after each batch of edits" (#101251) — [Issue](https://github.com/anthropics/claude-code/issues/101251); "Verification summary generated by the harness (not the model) at the end of each turn" (#101247) — [Issue](https://github.com/anthropics/claude-code/issues/101247); "Harness-enforced adversarial review gate on every commit" (#90887) — [Issue](https://github.com/anthropics/claude-code/issues/90887).
- Multi-session coordination: "Cross-session coordination for independently-launched sessions" (#76727, 25 comments) — [Issue](https://github.com/anthropics/claude-code/issues/76727); "Shared cross-session edit log, so sessions and sub-agents notice files changed by others" (#104352) — [Issue](https://github.com/anthropics/claude-code/issues/104352); list running sessions and state (#94620) — [Issue](https://github.com/anthropics/claude-code/issues/94620).
- Compaction: "Supported compaction instructions, and a kick-off prompt after compaction" (#101309) — [Issue](https://github.com/anthropics/claude-code/issues/101309). PreCompact/PostCompact events exist to implement this. — [Hooks reference](https://code.claude.com/docs/en/hooks)
- Memory: "Field notes after a year of home-grown memory on Claude Code" (#91473) — [Issue](https://github.com/anthropics/claude-code/issues/91473).
- Cost/limits: per-session spend cap for interactive sessions (#95964) — [Issue](https://github.com/anthropics/claude-code/issues/95964); hook when tokens run out with reset time (#55945) — [Issue](https://github.com/anthropics/claude-code/issues/55945); StopFailure event now exists for API-error turn ends. — [Hooks reference](https://code.claude.com/docs/en/hooks)
- PostToolUseFailure replacing the error output the model sees (#97278) is still requested; only PostToolUse can rewrite output today. — [Issue](https://github.com/anthropics/claude-code/issues/97278)

### Inferences (opportunity levers)
- **Affected-test runner**: PostToolBatch hook collects edited paths, runs only impacted tests, injects pass/fail as `additionalContext` (direct answer to #101251).
- **Harness-written turn receipt**: Stop hook diffs the turn (files touched, commands run, test exit codes from a PostToolUse ledger) and blocks Stop if claims and evidence diverge (#101247).
- **Commit gate**: PreToolUse on `Bash(git commit*)` running a deterministic check or `agent` hook reviewer (#90887).
- **Cross-session edit lock/log**: shared file under `${CLAUDE_PLUGIN_DATA}` written by PostToolUse, read by PreToolUse to warn on files another session touched (#104352, #76727).
- **Compaction continuity**: PreCompact snapshot of goals/decisions, PostCompact re-injects them (#101309).
- **Instruction drift checks**: InstructionsLoaded + FileChanged to detect stale/contradicting CLAUDE.md rules.
- **Output shaping**: PostToolUse `updatedToolOutput` to trim noisy tool output (logs, test runners) before it hits context, a direct context-cost reducer.
- **Budget guard**: Stop/UserPromptSubmit hooks tracking usage against a user cap (#95964).

### Gaps
- No usage data on how many published plugins use the newer events; "under-used" is inferred from the issues, not measured.

## What drives adoption of popular plugins/skills, and what are common failure modes?

### Takeaway
The breakout hits are tiny, dependency-free, opinionated behaviour encodings (Karpathy guidelines: one file, 210k+ stars) and coherent methodology packs (Superpowers, Matt Pocock, Addy Osmani lifecycle pack), plus one-skill aesthetic fixes (frontend-design, 277K+ installs). Failure modes are mis-triggering/budget drop-off, plugins with hidden hooks users cannot partially disable, and an active malicious-skill supply-chain problem.

### Cited Findings
- Karpathy-guidelines repo: a single CLAUDE.md with four rules, "zero runtime dependencies", 144k stars in weeks, now 210k+. — [Firecrawl blog](https://www.firecrawl.dev/blog/best-claude-code-skills)
- Frontend Design skill: 277K+ installs early 2026, "most-used design skill". — [Composio](https://composio.dev/content/top-claude-skills)
- anthropics/skills ~141.8k stars; obra/superpowers among top-ranked. — [rabinarayanpatra.com](https://www.rabinarayanpatra.com/blogs/best-claude-skills-for-developers-2026)
- Reddit users cite Superpowers as default driver for feature development. — [r/ClaudeCode](https://www.reddit.com/r/ClaudeCode/comments/1shlte1/what_are_your_favourite_pluginsskills_for_claude/)
- Curated lists group winners as methodology packs (Superpowers, Addy Osmani lifecycle, Matt Pocock "skills for real engineers"). — [agnt.gg](https://agnt.gg/articles/agents/100-best-claude-code-skills)
- Reviewer found broken marketplace files and argues "working" is hard to judge until run on real work. — [BuildToLaunch](https://buildtolaunch.substack.com/p/best-claude-code-plugins-tested-review)
- Lists converge on the same few skills, newcomers struggle for visibility; novel capabilities (e.g. audio understanding) are pitched as gap-fillers. — [Medium, Oct 2026](https://divadsanders.medium.com/the-best-claude-code-skills-for-2026-complete-install-guide-d5685482c4b5)

**Failure modes**
- Mis-triggering and listing truncation/drop-off — [Skills docs](https://code.claude.com/docs/en/skills)
- Hook control too coarse: users want per-plugin hook disable; disabled plugins' SessionStart/Stop hooks still fire (#19893, #36456, #39307). — [Issue #57877](https://github.com/anthropics/claude-code/issues/57877)
- Trust on update: "Marketplace plugin updates load newly-pulled executable code under initial-install trust, with no re-consent or diff" (#73914). — [Issue](https://github.com/anthropics/claude-code/issues/73914)
- "Plugin-attached context is hidden from the user by contract" (#102030); request for `claude plugin inspect` showing all hooks/skills/commands (#28528). — [#102030](https://github.com/anthropics/claude-code/issues/102030), [#28528](https://github.com/anthropics/claude-code/issues/28528)
- Plugin MCP servers duplicating connectors users already have (#105932). — [Issue](https://github.com/anthropics/claude-code/issues/105932)
- Version pinning on install requested (#63986). — [Issue](https://github.com/anthropics/claude-code/issues/63986)
- Malicious skills: Snyk found prompt injection in 36% of scanned skills and 1,467 malicious ones on ClawHub. — [Snyk](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/); Datadog shows dynamic-context abuse where Claude Code executed a malicious skill without acknowledging it. — [Datadog Security Labs](https://securitylabs.datadoghq.com/articles/malicious-skills-supply-chain-risks-in-coding-agents-with-dynamic-context/); OWASP Agentic Skills Top 10 lists AST01 Malicious Skills. — [Fortinet](https://community.fortinet.com/blogs-103/the-ai-agent-supply-chain-has-a-security-problem-introducing-skills-scanning-in-forticnapp-code-security-228185)
- Hooks did not fire in the VS Code extension (#21736); Desktop parity requested (#45514). — [#21736](https://github.com/anthropics/claude-code/issues/21736), [#45514](https://github.com/anthropics/claude-code/issues/45514)
- Windows Python hooks corrupt non-ASCII stdin unless decoded as UTF-8 (#96285). — [Issue](https://github.com/anthropics/claude-code/issues/96285)

### Inferences (design constraints)
- Zero-dep, readable, small: popularity correlates with "I can read the whole thing in a minute" — also the best answer to supply-chain fear.
- Declare every hook in the README and keep hooks optional via `userConfig` toggles, since users cannot disable one plugin's hooks.
- Avoid `bin/` and heavy MCP servers for cross-surface reach; pin `version`.
- Few skills, front-loaded "Use when..." descriptions; use `paths` and `disable-model-invocation` to cut mis-triggers.
- Hooks must be fast, cross-platform (explicit UTF-8), and fail open.

### Gaps
- No install-count data per marketplace plugin (only stars and one install figure).
- BuildToLaunch scorecard is paywalled.

## Signals of unmet demand (GitHub issues a plugin could fill)

### Takeaway
The highest-engagement open plugin/hook issues concern extensibility (Mods #91870, 277 comments), user-interrupt hooks, cross-session coordination, notifications, session naming, spend caps, and harness-side verification. Several are now partly buildable with existing events.

### Cited Findings (open, sorted by comments, area:hooks/plugins + enhancement)
- #91870 Mods - make Claude 10x more extensible (277 comments) — [Issue](https://github.com/anthropics/claude-code/issues/91870)
- #9516 User Interrupt Hook (30) — [Issue](https://github.com/anthropics/claude-code/issues/9516)
- #76727 Cross-session coordination (25) — [Issue](https://github.com/anthropics/claude-code/issues/76727)
- #55945 Hook when tokens run out, expose reset time (15) — [Issue](https://github.com/anthropics/claude-code/issues/55945)
- #73384 distinct notification sounds "needs input" vs "done" (11) — [Issue](https://github.com/anthropics/claude-code/issues/73384)
- #40346 programmatic session renaming via hooks (10); partly addressed by UserPromptSubmit `sessionTitle` — [Issue](https://github.com/anthropics/claude-code/issues/40346), [Hooks reference](https://code.claude.com/docs/en/hooks)
- #95964 per-session spend cap (8); #94620 list running sessions (8); #43326 auto-select model/effort by task complexity (8); #16592 expose pasted image data to hooks (8) — [#95964](https://github.com/anthropics/claude-code/issues/95964), [#94620](https://github.com/anthropics/claude-code/issues/94620), [#43326](https://github.com/anthropics/claude-code/issues/43326), [#16592](https://github.com/anthropics/claude-code/issues/16592)
- #48986 plugin lifecycle hooks (install/update/uninstall) — [Issue](https://github.com/anthropics/claude-code/issues/48986)
- #45132 Scala (Metals) LSP plugin (15 comments) — [Issue](https://github.com/anthropics/claude-code/issues/45132)
- #15936 hook exit code for user-visible message without context — [Issue](https://github.com/anthropics/claude-code/issues/15936)

### Inferences
- Buildable now as plugins: notification-sound router (Notification + Stop), model/effort router (UserPromptSubmit + PreModelSwitch), session dashboard/registry (SessionStart/SessionEnd writing to shared state), spend tracker, missing-language LSP plugins (Scala etc.), plugin inspector/auditor (lists every hook/skill a plugin registers; answers #28528/#102030/#73914 trust concerns).
- Not buildable yet (platform gaps): true user-interrupt hook, PostToolUseFailure output rewrite, plugin install/update events.

### Gaps
- Reaction counts were not returned, so ranking is by comments only.
- Issue search covered open area:plugins and area:hooks enhancement issues (top 25 each); closed or unlabeled issues were not reviewed.
