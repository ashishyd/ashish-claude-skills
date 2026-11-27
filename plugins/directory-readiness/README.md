# directory-readiness

Tells you whether a Claude plugin, and the skills inside it, will get through the Claude directory submission at claude.ai/directory/manage. It checks the plugin against the published pre-submission checklist and the Anthropic Software Directory Policy. You get the same four levels the portal uses: **Block** (cannot submit), **Hold** (a reviewer must clear it), **Warning** and **Note**. Every finding comes with a fix.

## Skills

- `plugin-readiness`: the whole bundle. Checks the manifest and name rules, README and license, file layout and sizes, hooks and MCP command rules, launchers and lockfiles, credentials, and what each Claude app (Chat, Cowork, Claude Code) will load. Then it reviews disclosure and data handling, and drafts the answers for the portal form.
- `skill-readiness`: one or more SKILL.md files. Checks that the front matter parses, the name and description rules, and policy rules for instructional software: a narrow and accurate description, no hidden or encoded instructions, and no pulling instructions from outside sources.

## Install

```bash
/plugin install directory-readiness --marketplace ashishyd/ashish-claude-skills
```

## What it runs

`scripts/check.py` is a read-only Python 3 standard-library script. It reads files in the folder you point it at and prints a report. It sends nothing over the network, writes no files, and changes nothing. `scripts/test_check.py` is its self-test.

```bash
python3 scripts/check.py path/to/plugin-or-marketplace
```

## Limits

This is a local pre-check. It cannot see the portal-side checks: name availability, brand look-alikes across other listings, the security scan, or reviewer judgment. Run `claude plugin validate` and the portal's **Validate** step as well. Rules were taken from the Claude docs on 2026-11-26. Re-check the docs if they have changed since.

## Privacy

This plugin collects no data and connects to no remote service.
