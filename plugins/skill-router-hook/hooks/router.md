ashish-claude-skills router (from the skill-router-hook plugin).

Before you act on a request, check whether one of these skills fits the moment and, if it does, invoke it with the Skill tool first. Use only skills that are in your available-skills list; skip any row whose skill is not installed. The user's instructions win over this list.

| Moment | Skill |
|---|---|
| Vague or large request, or work about to go to a subagent | task-brief |
| Deciding whether or how to build something | four-hats |
| New feature, page, endpoint, command or screen | feature-flow:new-feature |
| Any multi-file coding task | dev-loop |
| Writing or changing code | coding-standards |
| Code changed, about to be called done | standards-review |
| Adding, upgrading or removing a package | dependency-versions |
| Adding imports or moving code between modules | dependency-cycles |
| A bug or review finding: fix now or later? | vibe-coder:bug-triager |
| Project will not install, build or start | repo-health:env-doctor |
| Frontend and backend calls disagree | repo-health:api-drift |
| Feature flags to retire | repo-health:flag-cleanup |
| TypeScript, Vitest or Playwright work | quality-gates:typescript-types, quality-gates:vitest-tests, quality-gates:playwright-tests |
| Auth, input, secrets, sign-in or personal data in the code | quality-gates:security-code-audit, quality-gates:login-and-access, quality-gates:personal-data |
| New entry point, launch, or deploy/CI change | quality-gates:threat-model |
| UI built or changed | quality-gates:design-audit, quality-gates:ux-audit |
| UI built from a mock | design-gate:design-match, then design-gate:close-gaps |
| Site about to go live | vibe-coder:launch-ready, vibe-coder:launch-safe |
| Change ready for review, or too big to review | pr-review:reviewer-brief, pr-review:pr-splitter |
| Which model or effort, or a long session | switchboard:model-routing, switchboard:session-fit |
| Repo has no or a stale CLAUDE.md | repo-agent-guide |

When a skill reaches a decision with options you can name, ask with AskUserQuestion: 2-4 options, your pick first and marked (Recommended). When a skill finishes, offer its next step the same way. Do not ask about process steps you can decide yourself.
