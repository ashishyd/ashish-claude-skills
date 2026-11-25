#!/usr/bin/env python3
"""PostToolUse hook: after a UI edit in a repo with design-gate reports, remind once to re-check.

Reads the hook JSON on stdin. If the edited file is named in a report's `Where:`
line, it names those gap IDs once per session for each report and file. Any other UI edit
gets one generic reminder per session. It prints nothing when no report exists.
"""
import glob
import json
import os
import re
import sys
import tempfile

UI = re.compile(r"\.(tsx|jsx|vue|svelte|astro|html|css|scss)$", re.I)
GAP = re.compile(r"^\s*- \[[ x!~]\] (G\d+)\b")


def find_root(path):
    d = os.path.dirname(os.path.abspath(path))
    while True:
        if os.path.isdir(os.path.join(d, ".claude", "design-gate")):
            return d
        if os.path.isdir(os.path.join(d, ".git")) or os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def gaps_naming(report_text, rel):
    """Gap IDs whose Where: line names rel (repo-relative path)."""
    ids, current = [], None
    for line in report_text.splitlines():
        m = GAP.match(line)
        if m:
            current = m.group(1)
        elif current and line.strip().startswith("Where:") and rel in line:
            if current not in ids:
                ids.append(current)
    return ids


def hint_for(path, seen):
    """Return (hint, new_keys) or (None, [])."""
    norm = path.replace("\\", "/")
    if not UI.search(norm) or "/.claude/" in norm:
        return None, []
    root = find_root(path)
    if not root:
        return None, []
    reports = sorted(glob.glob(os.path.join(root, ".claude", "design-gate", "*.md")))
    if not reports:
        return None, []
    rel = os.path.relpath(os.path.abspath(path), root).replace("\\", "/")
    named, keys, any_named = [], [], False
    for r in reports:
        try:
            with open(r, encoding="utf-8") as f:
                ids = gaps_naming(f.read(), rel)
        except OSError:
            continue
        any_named = any_named or bool(ids)
        key = "%s|%s" % (os.path.basename(r), rel)
        if ids and key not in seen:
            named.append("%s (%s)" % (os.path.basename(r), ", ".join(ids)))
            keys.append(key)
    if named:
        return ("design-gate (%s): this file is named in %s. Before calling this done, "
                "re-check those gaps' Accept lines in the browser, and run `design-gate:design-match` "
                "on the screens it renders." % (rel, "; ".join(named)), keys)
    if any_named or "*generic*" in seen:  # already reminded about this file's gaps
        return None, []
    names = ", ".join(os.path.basename(r) for r in reports)
    return ("design-gate: reports exist (%s). UI edits can break screens that matched; "
            "before calling this done, run `design-gate:design-match` on the screens you touched "
            "and `design-gate:slop-check` on the diff." % names, ["*generic*"])


def main():
    data = json.load(sys.stdin)
    path = (data.get("tool_input") or {}).get("file_path") or ""
    if not path:
        return
    session = re.sub(r"\W", "", str(data.get("session_id", "")))
    state = os.path.join(tempfile.gettempdir(), "design-gate-" + session)
    try:
        with open(state) as f:
            seen = set(f.read().splitlines())
    except OSError:
        seen = set()
    hint, keys = hint_for(path, seen)
    if not hint:
        return
    with open(state, "a") as f:
        f.write("\n".join(keys) + "\n")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse", "additionalContext": hint}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hint hook must never fail or block an edit
        pass
