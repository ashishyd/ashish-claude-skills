#!/usr/bin/env python3
"""Trim noisy Bash output before it reaches Claude's context.

As a PreToolUse hook (JSON on stdin): when the command is a known noisy one
(installs, builds, test runs, docker builds, long logs) and has no pipe or
redirect of its own, rewrites it to pipe through this script with pipefail, so
the exit code is the command's. Leaves every other command alone, and never
sets a permission decision, so normal permission prompts still apply.

As a filter (`trim_output.py --filter`): keeps the first HEAD and last TAIL
lines, every line that looks like an error or warning in between (capped),
collapses repeated lines, and says how many lines it dropped.
Opt out per command by adding `# no-trim`, or for a session with CLAUDE_NO_TRIM=1.
"""
import json
import os
import re
import shlex
import sys

HEAD, TAIL, KEEP_MAX, MIN_LINES = 30, 80, 60, 150
NOISY = re.compile(
    r"^\s*(?:(?:npm|pnpm|yarn|bun)\s+(?:i|install|ci|add|run\s+(?:build|test|lint)|build|test)\b"
    r"|npx\s+(?:vitest|jest|playwright|tsc|next\s+build|eslint)\b"
    r"|(?:pip|pip3|uv\s+pip|poetry|uv)\s+(?:install|sync|add)\b"
    r"|pytest\b|python3?\s+-m\s+pytest\b|go\s+(?:build|test|mod\s+download)\b"
    r"|cargo\s+(?:build|test|check)\b|mvn\b|gradle\b|\./gradlew\b|make\b"
    r"|docker\s+(?:build|compose\s+(?:build|up))\b|bundle\s+install\b|composer\s+install\b)")
SIGNAL = re.compile(r"error|fail|panic|exception|traceback|warn|✗|✕|×|FAILED|^\s+at\s", re.I)


def wrap(command):
    """Return the rewritten command, or None to leave it alone."""
    if os.environ.get("CLAUDE_NO_TRIM") or "no-trim" in command or "\n" in command:
        return None
    if re.search(r"[|>]|&&|;|\|\||`|\$\(", command) or not NOISY.search(command):
        return None
    me = shlex.quote(os.path.abspath(__file__))
    return "set -o pipefail; { %s ; } 2>&1 | python3 %s --filter" % (command, me)


def trim(lines):
    out, last, repeats = [], None, 0
    for line in lines:  # collapse runs of identical lines (progress bars, retries)
        if line == last:
            repeats += 1
            continue
        if repeats:
            out.append("  [previous line repeated %d more times]\n" % repeats)
        out.append(line)
        last, repeats = line, 0
    if repeats:
        out.append("  [previous line repeated %d more times]\n" % repeats)
    if len(out) < MIN_LINES:
        return out
    middle = out[HEAD:-TAIL]
    kept = [l for l in middle if SIGNAL.search(l)][:KEEP_MAX]
    note = "  [trim_output: dropped %d of %d lines; kept %d error/warning lines. Re-run with '# no-trim' for everything]\n" % (
        len(middle) - len(kept), len(out), len(kept))
    return out[:HEAD] + [note] + kept + out[-TAIL:]


def main():
    if "--filter" in sys.argv:
        sys.stdout.writelines(trim(sys.stdin))
        return
    try:
        data = json.load(sys.stdin)
        cmd = data["tool_input"]["command"]
        new = wrap(cmd) if isinstance(cmd, str) else None
    except Exception:
        return  # never block a tool call
    if new:
        tool_input = dict(data["tool_input"], command=new)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "updatedInput": tool_input}}))


if __name__ == "__main__":
    main()
