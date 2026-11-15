#!/usr/bin/env python3
"""PostToolUse hook: name the skill that fits the file just edited, once per session.

Reads the hook JSON on stdin. Prints a one-line hint as additionalContext the
first time a skill becomes relevant in a session, and nothing otherwise.
"""
import json
import os
import re
import sys
import tempfile

P = "quality-gates:"
UI = r"\.(tsx|jsx|vue|svelte|css|scss|html)$"

# Test files get only their test skill; the first match wins.
TEST_RULES = [
    ("playwright-tests", r"(^|/)(e2e|playwright)/|\.e2e\.|playwright\.config\."),
    ("vitest-tests", r"\.(test|spec)\.[cm]?[jt]sx?$|vitest\.config\."),
]
# shortcut: security files are picked by path words, so a sensitive file with a
# plain name is missed; upgrade to content matching if that proves common.
CODE_RULES = [
    ("typescript-types", r"\.[cm]?tsx?$"),
    ("security-code-audit",
     r"auth|login|session|token|passw|crypt|secret|webhook|upload|payment"
     r"|middleware|(^|/)api/|(^|/)route\.|\.sql$"),
    ("design-audit", UI),
    ("ux-audit", UI),
    # shortcut: any source edit counts as "may change business logic"; the skill
    # itself decides whether CLAUDE.md needs a line. Add extensions as needed.
    ("claude-md-sync",
     r"\.([cm]?[jt]sx?|py|go|rb|java|kt|rs|swift|cs|php|vue|svelte|sql|prisma)$"),
]
HINTS = {
    "typescript-types": "load `{0}typescript-types` before more TypeScript edits",
    "vitest-tests": "load `{0}vitest-tests` before more test edits "
                    "(a Playwright spec? use `{0}playwright-tests`)",
    "playwright-tests": "load `{0}playwright-tests` before more e2e edits",
    "security-code-audit": "before calling this work done, run "
                           "`{0}security-code-audit` on the diff",
    "design-audit": "before calling this UI work done, run `{0}design-audit`",
    "ux-audit": "and `{0}ux-audit`",
    "claude-md-sync": "if this changes business logic, data model, API, "
                      "architecture or commands, run `{0}claude-md-sync` "
                      "before calling it done",
}


def skills_for(path):
    p = path.replace("\\", "/").lower()
    for skill, pattern in TEST_RULES:
        if re.search(pattern, p):
            return [skill]
    return [skill for skill, pattern in CODE_RULES if re.search(pattern, p)]


def main():
    data = json.load(sys.stdin)
    path = (data.get("tool_input") or {}).get("file_path") or ""
    skills = skills_for(path)
    if not skills:
        return
    session = re.sub(r"\W", "", str(data.get("session_id", "")))
    state = os.path.join(tempfile.gettempdir(), "quality-gates-" + session)
    try:
        with open(state) as f:
            seen = set(f.read().split())
    except OSError:
        seen = set()
    new = [s for s in skills if s not in seen]
    if not new:
        return
    with open(state, "a") as f:
        f.write("\n".join(new) + "\n")
    hint = "quality-gates (%s): %s." % (
        os.path.basename(path), "; ".join(HINTS[s].format(P) for s in new))
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse", "additionalContext": hint}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hint hook must never fail or block an edit
        pass
