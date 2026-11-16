# Claude Code / Agent-Skill / MCP Plugin Landscape (as of mid-November 2026)

Scope note: research done 2026-11-15 with about 15 search/fetch calls. Popularity numbers are point-in-time snapshots from the cited pages. Where a source is an aggregator rather than the primary repo, that is stated.

User's existing work (treated as already built, not counted as gaps): plugins quality-gates, feature-flow, plugin-audit (plugin security scan), switchboard (model routing), confluence-diagrams; skills dependency-cycles, dependency-versions, coding-standards, repo-agent-guide, task-brief, dev-loop.

## What are the major public marketplaces and directories?

### Takeaway
Distribution has consolidated around a few channels: Anthropic's two Claude Code marketplaces (official, about 317 plugins; community, reviewed), the cross-agent skills.sh registry (Vercel's `npx skills`, about 1.42M all-time installs counted on its board), a handful of mega-collections with six-figure star counts (superpowers, everything-claude-code), and MCP registries now in the 26k to 121k-server range. Copilot and Cursor now consume the same SKILL.md format, so a skill written once reaches most agents.

### Cited Findings
**Anthropic channels**
- Anthropic runs `claude-plugins-official` (curated, registered automatically) and `claude-plugins-community` (third-party plugins that passed review, added with `/plugin marketplace add anthropics/claude-plugins-community`) — [The AI Career Lab](https://theaicareerlab.com/blog/claude-plugins-explained-marketplace-2026), citing [Claude Code docs](https://code.claude.com/docs/en/plugins)
- On 2026-11-09 the official marketplace listed 317 plugins; 263 point to external sources, 262 of them pinned to a commit SHA — [NeuralTrust](https://neuraltrust.ai/blog/claude-code-plugins), citing [marketplace.json](https://github.com/anthropics/claude-plugins-official/blob/main/.claude-plugin/marketplace.json)
- claude.com/marketplace is the browse site for plugins, connectors, partner products and service partners. Any repo with `.claude-plugin/marketplace.json` is a marketplace — [Claude Code docs: Plugins overview](https://code.claude.com/docs/en/plugins/overview)
- Anthropic also ships domain marketplaces such as `anthropics/knowledge-work-plugins` and `anthropics/financial-services-plugins` — [claudecowork.im](https://claudecowork.im/plugins)

**Cross-agent skills registries**
- skills.sh: "All Time (1,423,642)" counter on the leaderboard. It lists support for Claude Code, Cursor, Codex, Copilot, Windsurf, Gemini, Cline, Amp, Goose, Kiro, OpenCode, Roo, Zed and others — [skills.sh](https://www.skills.sh/) (scraped 2026-11-15)
- The leaderboard ranks skills by downloads through Vercel's `npx skills` installer. An HN commenter notes this favours Vercel's own skills — [Show HN: Agent Skills Leaderboard](https://news.ycombinator.com/item?id=46697908)
- Independent ranking alternative: [skillleaderboard.com](https://www.skillleaderboard.com/) (ranks open GitHub skills daily)
- buildwithclaude.com is a community plugin marketplace with builder stories. One recent story covers packaging 79 skills as one marketplace for Claude Code, Cursor and Codex — [Build with Claude](https://buildwithclaude.com/)

**Mega-collections and awesome lists (stars)**
- obra/superpowers: about 314k to 317k stars, global rank #14 on star-history — [star-history](https://www.star-history.com/obra/superpowers). A Medium post earlier cited 150k, so it is growing fast — [Medium](https://medium.com/@anilmathewm/i-gave-claude-code-a-brain-its-called-superpowers-and-it-has-150-000-github-stars-for-a-reason-16c4074a9209)
- affaan-m/everything-claude-code 141k; hesreallyhim/awesome-claude-code 36.8k; shanraisshan/claude-code-best-practice 32.3k; VoltAgent/awesome-design-md 18.3k; VoltAgent/awesome-agent-skills 14.4k (1,000+ skills); plus quemsah/awesome-claude-plugins (auto-tracks plugin adoption), ComposioHQ/awesome-claude-skills, wong2 and punkpeye awesome-mcp-servers — [claudefa.st, 2026-11-10](https://claudefa.st/blog/tools/resources/awesome-claude-code). Conflict: skillsllm.com shows awesome-claude-code at 57.9k — [skillsllm](https://skillsllm.com/skill/hesreallyhim-awesome-claude-code)
- awesome-claude-code is still active: its README was updated 2026-10-22 and it has a CI gate on resource maturity — [GitHub](https://github.com/hesreallyhim/awesome-claude-code)
- yeachan-heo/oh-my-claudecode: 40.8K stars (shown on skills.sh) — [skills.sh](https://www.skills.sh/yeachan-heo/oh-my-claudecode/omc-doctor)

**Other agents' ecosystems**
- github/awesome-copilot has agents, skills and a plugin marketplace (`copilot plugin marketplace add github/awesome-copilot`) — [GitHub](https://github.com/github/awesome-copilot), [site](https://awesome-copilot.github.com/)
- GitHub analysed more than 2,500 public `agents.md` files. Effective ones are specialists with a persona, commands and boundaries — [GitHub Blog](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
- Cursor users ask to reuse `.github/copilot-instructions.md` and `.github/skills/`, which shows the formats are converging — [Cursor forum](https://forum.cursor.com/t/using-github-copilot-instructions-md-for-ai-rules/154879)

**MCP registries**
- Glama: 121,515 servers on its page (mcpfinder recorded 120,509 on 2026-11-13) — [Glama](https://glama.ai/mcp/servers), [mcpfinder](https://mcpfinder.dev/mcp-server-directories/)
- Smithery: 26,000+ servers, part of Arcade.dev since August 2026 — [Scalekit](https://www.scalekit.com/blog/mcp-registry-vs-managed-mcp-integrations)
- The Official MCP Registry describes "84k tools", including Agent Skills and Claude Code plugins — [registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io/)

### Inferences
- Writing to the SKILL.md standard and publishing to skills.sh plus a Claude marketplace is the cheapest way to reach the most agents. Plugins are needed only when hooks, agents or MCP are involved.
- Install counts on skills.sh are inflated by duplicate copies under many owners (for example "superpowers/ai-image-generation" appears under at least 5 owners) and favour vendor skills. Use them for relative ranking only.

### Gaps
- Could not get per-plugin install counts for the Anthropic official marketplace. None appear to be published.
- Did not find a star count for awesome-cursorrules or the size of the Cursor directory (cursor.directory) in this pass.

## Which categories are saturated?

### Takeaway
Planning/brainstorming, "grill me"/interview, TDD, code review, frontend design/taste, framework best-practices (React, Vercel, Azure, Expo), commit/PR, and generic security review are heavily saturated. Several are bundled in the mega-frameworks (superpowers, mattpocock/skills, agent-skills, everything-claude-code). Media generation (video, image) and vendor-platform skills dominate the top of skills.sh.

### Cited Findings
skills.sh all-time top entries (2026-11-15) — [skills.sh](https://www.skills.sh/):
- find-skills (vercel-labs) 4.4M
- Planning, interview and architecture (mattpocock/skills): grill-me 1.6M, grill-with-docs 1.3M, improve-codebase-architecture 1.3M, grilling 1.1M, prototype 1.1M, triage 1.1M, domain-modeling 983K, code-review 896K, implement 868K, wayfinder 814K, wizard 637K, to-questionnaire 582K
- Frontend and design: anthropics/frontend-design 1.1M, uizze ui-taste 1.1M, design-mobile-apps 1.4M, vercel web-design-guidelines 866K, vercel-react-best-practices 902K, leonxlnx design-taste-frontend 782K
- Browser automation: vercel-labs agent-browser 1.5M
- Video and media: heygen hyperframes family (about 10 skills, 0.6 to 1.6M each), remotion-best-practices 831K, multiple ai-image-generation and ai-video-generation clones
- Cloud vendor: microsoft/azure-skills (foundry 717K, compute 660K, cloud-migrate 652K, quotas 608K, upgrade 601K), google agents-cli (about 574K each)
- Productivity suites: Feishu/Lark skills (doc, minutes, vc, okr, about 0.7 to 0.9M each)
- Token-saving style: juliusbrussee/caveman 629K

Methodology frameworks:
- superpowers covers brainstorming, plans, TDD, systematic debugging, code review request/receive, worktrees and verification in one plugin — [GitHub](https://github.com/obra/superpowers), [Reddit](https://www.reddit.com/r/vibecoding/comments/1x7gl7k/superpowers_the_single_best_skill_ive_ever_found/)
- The awesome-claude-code table of contents leads with Agent Orchestration (for example "Ralph Wiggum" loops), which shows orchestration is crowded too — [GitHub](https://github.com/hesreallyhim/awesome-claude-code)

Cost tracking (also largely covered):
- ccusage: 19.4k stars, covers about 18 agents (Claude Code, Codex, OpenCode, Amp, Copilot, Gemini and others), with daily, session and 5-hour-block reports and a statusline — [GitHub](https://github.com/ccusage/ccusage), [ccusage.com](https://ccusage.com/)
- Claude Code natively exports OpenTelemetry token and cost metrics. Team platforms exist. PointFive says the gap is attribution beyond "what did this tool cost" — [PointFive](https://www.pointfive.co/blog/how-to-track-coding-agent-spend-across-your-team), [Claude Code docs: costs](https://code.claude.com/docs/en/costs)

### Inferences
- Saturated, avoid: planning/spec, interview/grill, TDD, generic code review, frontend taste/design, commit/PR, generic security review, framework best practices, browser automation, personal token or cost dashboards.
- The user's quality-gates, feature-flow and task-brief overlap these crowded categories. Their value would be in being opinionated and integrated, not novel.

### Gaps
- No reliable install data for commit/PR or docs-writing skills specifically. Their saturation is inferred from presence in every framework (superpowers, agent-skills, mattpocock) rather than measured.

## Which developer workflow areas have few or low-quality offerings?

### Takeaway
Most "gap" areas are not empty. Instead they are covered (a) by vendor skills tied to one SaaS (Datadog, Develocity, LaunchDarkly, PostHog, Vercel Flags) or (b) by generic checklist-style SKILL.md files with no scripts and negligible installs. Tool-agnostic, evidence-driven skills that run real commands across these areas are rare. These are the real openings.

### Cited Findings
**Flaky test triage and CI log diagnosis: vendor-locked or generic**
- Datadog `dd-triage-flaky-test`: history, category, then fix, quarantine or escalate. Requires Datadog CI Visibility — [GitHub datadog/pup](https://github.com/datadog/pup/blob/bb7e81a026dc313246af283ce45a03acf077a1e7/skills/dd-triage-flaky-test/SKILL.md)
- Develocity Failure Handler skill (needs Develocity cross-build data; Gradle/Maven) — [Develocity docs](https://docs.develocity.ai/2026.3/integrations/agentic-ai/skills/develocity-failure-handler/)
- TestDino "flaky or broken" verdicts from run history (Playwright, needs TestDino) — [GitHub](https://github.com/testdino-hq/playwright-skill/blob/27b3ed58126bf875cb8cf0a5a39561c7824b65fc/e2e-testdino/flaky-or-broken.md)
- Generic GitHub CI triage skill (superset-sh): "do not launder a flake into a pass", first-error-not-last — [GitHub](https://github.com/superset-sh/superset/blob/7ae3dc9b162181506a61fe0dc896836f408e5ccd/plugins/github/skills/ci-triage/SKILL.md)
- Playwright-specific flaky guides embedded in repos (sanity, mercur, alirezarezvani playwright-pro) — [sanity](https://github.com/sanity-io/sanity/blob/44866f5cd5bc033d3c31e999d2138cf1e3b5a692/.agents/skills/playwright-best-practices/debugging/flaky-tests.md), [alirezarezvani](https://github.com/alirezarezvani/claude-skills/blob/08cd8a9fc86cc370e2c0d448e8171fbcfdbc5a30/engineering-team/playwright-pro/skills/fix/SKILL.md)

**DB migration safety: many checklists, little tooling**
- Mostly static checklists: cc-polymath postgres-migrations, wshobson/agents database-migration (on skills.sh), oakoss db-enforcer, claude-dev-suite migrations — [cc-polymath](https://github.com/rand/cc-polymath/blob/baa2df114416570f5e0e2961143d20e3716a2fc8/skills/database/postgres-migrations.md), [skills.sh wshobson](https://www.skills.sh/wshobson/agents/database-migration), [oakoss](https://github.com/oakoss/agent-skills/blob/85e3a3919d9e0ec7f7302a5143ec4b3e66f5f6ad/skills/db-enforcer/references/migration-safety.md)
- midudev/autoskills review-migration has a HARD-GATE table on lock and rewrite risk (Rails/PG/MySQL) — [GitHub](https://github.com/midudev/autoskills/blob/0cc23ef1dd7f08449b9c7c16ac799232ca8ccc77/packages/autoskills/skills-registry/review-migration/SKILL.md)

**Feature-flag cleanup: covered per vendor**
- LaunchDarkly flag-cleanup skill (needs the LD MCP; 4.2K installs) — [skills.sh](https://www.skills.sh/launchdarkly/ai-tooling/launchdarkly-flag-cleanup)
- PostHog cleaning-up-stale-feature-flags (notes "This skill does not archive a flag, and no skill does yet") — [GitHub](https://github.com/posthog/posthog/blob/f1221e34627ac5968bb1d5ac245c92e18d0fa8e6/products/feature_flags/skills/cleaning-up-stale-feature-flags/SKILL.md)
- Vercel Flags cleanup reference; Sentry internal remove-option-or-flag; alirezarezvani feature-flags-architect with a `flag_debt_scanner.py` — [vercel/flags](https://github.com/vercel/flags/blob/7baf8fc46845f3c5bd5bcad750c367e8db5595a1/skills/vercel-flags/references/cleanup.md), [Sentry](https://github.com/getsentry/sentry/blob/fe43ef0ee658bbd47b61e5e73cdd10923e85345e/.agents/skills/remove-option-or-flag/SPEC.md), [alirezarezvani](https://github.com/alirezarezvani/claude-skills/blob/08cd8a9fc86cc370e2c0d448e8171fbcfdbc5a30/engineering/skills/feature-flags-architect/SKILL.md)

**API contract drift: spec-diff exists, code-to-consumer drift is thin**
- Many spec-vs-spec skills wrap oasdiff, Optic or Spectral (a5c-ai/babysitter library, alirezarezvani api-design-reviewer) — [babysitter api-diff-analyzer](https://github.com/a5c-ai/babysitter/blob/feb68abe397acc14f32b34984975c48fedba2b33/library/specializations/sdk-platform-development/skills/api-diff-analyzer/SKILL.md)
- awesome-copilot `api-breaking-change-detector` cross-references C# controllers and DTOs against TS consumers. It is stack-specific (.NET to TS) — [GitHub](https://github.com/github/awesome-copilot/blob/8ecd5b17f02fe5fbebf35eccd1867265eded811f/skills/api-breaking-change-detector/SKILL.md)

**Local environment doctor: mostly product-specific "doctor" skills**
- Product doctors: omc-doctor (905 installs), oh-my-codex doctor, spec-kitty setup-doctor, dotnet-maui-doctor (4.4K installs) — [skills.sh omc-doctor](https://www.skills.sh/yeachan-heo/oh-my-claudecode/omc-doctor), [skills.sh maui](https://www.skills.sh/dotnet/skills/dotnet-maui-doctor)
- Generic: oaustegard check-tools lists installed tool versions but does not read a repo's declared requirements — [GitHub](https://github.com/oaustegard/claude-skills/blob/62bff7897710d205094a790be55e726ed5832c29/check-tools/SKILL.md)

**Agent cost: individual view solved, attribution not**
- ccusage and native OTel cover per-user or per-session spend. PointFive identifies team, task and PR attribution as the gap — [PointFive](https://www.pointfive.co/blog/how-to-track-coding-agent-spend-across-your-team)

### Inferences
Opportunity ranking (my judgement from the evidence above; not measured):
1. **Vendor-neutral CI failure and flaky triage** that reads `gh run view --log-failed` or GitLab logs, classifies flake vs regression vs infra, and checks recurrence across recent runs. Today you need Datadog or Develocity, or you get a generic checklist.
2. **Migration safety gate with a linter behind it.** Wrap squawk, strong_migrations or Atlas lint per ORM and block on lock or rewrite risk. Existing skills are prose checklists.
3. **Code-level API contract drift**: server routes vs client call sites for TS, Python or Go, not only spec-vs-spec. Only a .NET-to-TS example exists.
4. **Generic repo env doctor**: read `.tool-versions`, `.nvmrc`, `engines`, `pyproject` and docker-compose, then diff them against the machine. Existing doctors are per product.
5. **Vendor-neutral feature-flag cleanup** for home-grown flags or OpenFeature. Vendors cover their own SDKs only.
6. **Agent spend attributed to PR or task** (join OTel or ccusage data to git branches). Skip personal dashboards.
- Adjacent to the user's existing dependency-versions skill: a **framework upgrade/migration assistant** is partly covered by vendors (Azure upgrade 601K installs, Vercel next-upgrade, expo-upgrade) and is crowded for big frameworks. A generic codemod-driven one is a weaker bet.

### Gaps
- Not searched this pass, so no evidence either way: incident/log triage (beyond vendor MCPs such as Sentry/Datadog), perf regression, monorepo CODEOWNERS/ownership, i18n, accessibility (note: the user has ux-audit and design:accessibility-review installed already), license compliance, secrets hygiene. Treat these as unverified, not as confirmed gaps.
- Install counts for most gap-area skills are not shown (GitHub-only). Low visibility is inferred from their absence from the skills.sh top 60, not measured directly.
- No HN or Reddit launch-post analysis of user demand ("I wish there were a skill for X") was done.
