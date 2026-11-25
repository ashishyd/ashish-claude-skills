#!/usr/bin/env python3
"""UserPromptSubmit hook: when the prompt asks for a new feature, point Claude at
the feature-flow `new-feature` skill. Prints nothing for any other prompt. Never
blocks or fails.
"""
import json
import re
import sys

VERB = r"(plan|add|build|create|implement|develop|make|introduce|ship|support|need|want)"
# shortcut: keyword rules miss features asked for without these words ("let users
# export CSV"); widen FEATURE or add a phrase list if that proves common.
FEATURE = re.compile(
    r"\bnew feature\b|\bfeature request\b"
    r"|\b%s\b.{0,40}\bfeature\b" % VERB
    + r"|\b%s\b (a |an )?new \w+" % VERB, re.I)
NOT_FEATURE = re.compile(
    r"\b(fix|bug|debug|why|explain|review|remove|delete|rename|revert"
    r"|feature[- ]?flags?)\b", re.I)

HINT = ("feature-flow: this is a new-feature request. Load `feature-flow:new-feature` "
        "and follow it: Opus planner -> checklist in .claude/features/ -> Sonnet "
        "(medium effort) builder subagents -> README.md update. If superpowers is "
        "installed: superpowers:brainstorming may run first for design, then hand "
        "off to feature-flow:new-feature instead of superpowers:writing-plans; do "
        "not run writing-plans, executing-plans or subagent-driven-development.")


def is_feature(prompt):
    p = prompt.strip()
    if not p or p.startswith("/") or len(p.split()) < 3:
        return False
    return bool(FEATURE.search(p)) and not NOT_FEATURE.search(p)


def main():
    data = json.load(sys.stdin)
    if is_feature(str(data.get("prompt", ""))):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit", "additionalContext": HINT}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hint hook must never fail or block a prompt
        pass
