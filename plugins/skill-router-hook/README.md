# skill-router-hook

At the start of each session (and after `/clear` or a compact), this hook adds a short index to Claude's context. The index maps each moment in the work to the skill from this marketplace that fits it, for example "UI built from a mock: design-match, then close-gaps". With it, Claude checks for a skill before acting instead of waiting for you to name one. It also asks Claude to put decisions to you as option buttons (`AskUserQuestion`) and to offer each skill's next step.

Claude is told to use only the skills you have installed. Rows for plugins you don't have are skipped.

## Install

```bash
/plugin install skill-router-hook --marketplace ashishyd/ashish-claude-skills
```

## What it runs

`hooks/router.sh` prints `hooks/router.md`. That is all it does. The index costs about 600 tokens per session. To change the routing, edit `hooks/router.md`.

## Privacy

This plugin collects no data and connects to no remote service.
