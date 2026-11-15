#!/usr/bin/env python3
"""Stop hook: while a feature-flow checklist is in progress, do not let the turn
end with code changed and README.md unchanged.

Armed only by a `.claude/features/*.md` file at the repo root containing the
line `status: in-progress`. Fails open: any error, no git, or a repeat stop
(`stop_hook_active`) lets the turn end.
"""
import glob
import json
import os
import re
import subprocess
import sys

ACTIVE = re.compile(r"^status:\s*in-progress\s*$", re.M)


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True,
                          text=True, timeout=5).stdout


def active_checklists(root):
    out = []
    for path in glob.glob(os.path.join(root, ".claude", "features", "*.md")):
        try:
            with open(path, encoding="utf-8") as f:
                if ACTIVE.search(f.read()):
                    out.append(os.path.relpath(path, root))
        except OSError:
            pass
    return out


def changed_files(root):
    """Paths changed vs HEAD plus untracked files, repo-relative."""
    files = set()
    for line in git(root, "status", "--porcelain", "--untracked-files=all").splitlines():
        path = line[3:].split(" -> ")[-1].strip('"')
        files.add(path)
    return files


def verdict(root):
    """Block reason, or None to let the turn end."""
    active = active_checklists(root)
    if not active:
        return None
    changed = changed_files(root)
    code = [f for f in changed if not f.startswith(".claude/")
            and os.path.basename(f).lower() != "readme.md"]
    if not code or "README.md" in changed:
        return None
    return ("feature-flow: %s is in progress and code changed (%d files) but README.md "
            "did not. Run the checklist's README step (feature-builder), or, if the "
            "feature is finished or dropped, set `status: done` or `status: abandoned` "
            "in that file." % (", ".join(sorted(active)), len(code)))


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return  # already blocked once this turn; never loop
    root = git(data.get("cwd") or os.getcwd(), "rev-parse", "--show-toplevel").strip()
    reason = root and verdict(root)
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # fail open: a broken gate must not trap the session
        pass
