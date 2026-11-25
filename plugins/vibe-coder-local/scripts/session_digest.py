#!/usr/bin/env python3
"""Digest of friction moments in past Claude Code sessions for one project.

Reads ~/.claude/projects/<project-slug>/*.jsonl (read-only) and prints only the
moments worth learning from, so the model never has to read whole transcripts:
  - correction:  a user turn that pushes back ("no", "don't", "I said", "revert"...)
  - rejected:    the user denied a tool call
  - interrupted: the user stopped Claude mid-turn
  - tool-error:  a tool call that failed; repeats of the same error are counted
Each moment carries the end of Claude's previous message, for context.

Usage: session_digest.py [--project PATH] [--since ISO] [--max-sessions N]
                         [--include-latest] [--json]
The newest session is skipped by default: it is usually the one running this.
"""
import argparse
import glob
import json
import os
import re
import sys

CORRECTION = re.compile(
    # "don't" mid-message is usually a fresh instruction, not pushback, so only count it as the opener
    r"^\s*(no|nope|stop|wait|wrong|don'?t|do not)\b"
    r"|\b(didn'?t (i|you)|not what i|that'?s not|instead of|revert|undo|roll ?back"
    r"|why did you|why are you|i (said|asked|told you)|you (forgot|missed|ignored|broke)"
    r"|again\?|still (broken|failing|wrong|not))\b",
    re.I)
WRAPPER = re.compile(r"<(system-reminder|task-notification|command-[a-z]+|local-command-[a-z]+|pasted_content)\b[^>]*>.*?</\1>", re.S)
REJECTED = "doesn't want to proceed with this tool use"
INTERRUPTED = "[Request interrupted by user"


def slug(path):
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def result_text(block):
    c = block.get("content")
    return c if isinstance(c, str) else text_of(c)


def clip(s, n):
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n] + "..."


def moments(path, since=None):
    """Yield friction moments from one transcript, oldest first."""
    last_assistant, tool_names, errors, opened = "", {}, {}, False
    try:
        f = open(path, encoding="utf-8")
    except OSError:
        return
    with f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("isSidechain") or e.get("isMeta"):
                continue
            ts = e.get("timestamp") or ""
            msg = e.get("message") if isinstance(e.get("message"), dict) else {}
            content = msg.get("content")
            if e.get("type") == "assistant":
                t = text_of(content)
                if t.strip():
                    last_assistant = t
                for b in content if isinstance(content, list) else []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        tool_names[b.get("id")] = (b.get("name"), clip(json.dumps(b.get("input")), 160))
                continue
            if e.get("type") != "user":
                continue
            said = WRAPPER.sub("", text_of(content)).strip()
            first, opened = said and not opened, opened or bool(said)  # the opening request is never pushback
            if since and ts <= since:
                continue
            ctx = clip(last_assistant[-400:], 300)
            for b in content if isinstance(content, list) else []:
                if not (isinstance(b, dict) and b.get("type") == "tool_result"):
                    continue
                name, args = tool_names.get(b.get("tool_use_id"), ("?", ""))
                body = result_text(b)
                if REJECTED in body:
                    yield {"kind": "rejected", "ts": ts, "tool": name, "input": args, "said": clip(body.split(REJECTED, 1)[1], 300), "context": ctx}
                elif b.get("is_error"):
                    key = (name, clip(body, 120))
                    if key in errors:
                        errors[key]["count"] += 1
                        continue
                    errors[key] = {"kind": "tool-error", "ts": ts, "tool": name, "input": args, "error": clip(body, 300), "count": 1}
                    yield errors[key]  # same dict: later repeats raise its count before output
            if not said:
                continue
            if said.startswith(INTERRUPTED):
                yield {"kind": "interrupted", "ts": ts, "context": ctx}
            elif not first and CORRECTION.search(said):
                yield {"kind": "correction", "ts": ts, "said": clip(said, 400), "context": ctx}


def sessions(project, since=None, max_sessions=10, include_latest=False):
    paths = sorted(glob.glob(os.path.join(project, "*.jsonl")), key=os.path.getmtime, reverse=True)
    if not include_latest:
        paths = paths[1:]
    if since:
        paths = [p for p in paths if _iso_mtime(p) > since]
    return paths[:max_sessions], max(0, len(paths) - max_sessions)


def _iso_mtime(p):
    import datetime
    return datetime.datetime.fromtimestamp(os.path.getmtime(p), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=os.getcwd(), help="project path (default: cwd)")
    ap.add_argument("--since", help="ISO time; only moments after it (use the last run's 'Scanned through')")
    ap.add_argument("--max-sessions", type=int, default=10)
    ap.add_argument("--include-latest", action="store_true", help="also scan the newest session")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    folder = os.path.join(os.path.expanduser("~/.claude/projects"), slug(a.project))
    if not os.path.isdir(folder):
        sys.exit(f"no transcripts for {a.project} (looked in {folder})")
    paths, skipped = sessions(folder, a.since, a.max_sessions, a.include_latest)
    out, newest = [], a.since or ""
    for p in paths:
        ms = list(moments(p, a.since))
        if ms:
            newest = max([newest] + [m["ts"] for m in ms])
            out.append({"session": os.path.basename(p)[:-6], "moments": ms})
    if a.json:
        print(json.dumps({"sessions": out, "scanned": len(paths), "skipped": skipped, "scanned_through": newest}, indent=1))
        return
    for s in out:
        print(f"## session {s['session']}")
        for m in s["moments"]:
            head = f"- [{m['kind']}] {m['ts'][:16]}"
            if m["kind"] == "correction":
                print(f"{head} user: {m['said']}")
            elif m["kind"] == "rejected":
                print(f"{head} denied {m['tool']} {m['input']} {m['said']}".rstrip())
            elif m["kind"] == "tool-error":
                print(f"{head} {m['tool']} x{m['count']} {m['input']} -> {m['error']}")
            else:
                print(head)
            if m.get("context"):
                print(f"  claude before: {m['context']}")
    total = sum(len(s["moments"]) for s in out)
    print(f"\nScanned {len(paths)} sessions ({skipped} older not scanned), {total} moments. Scanned through: {newest or 'n/a'}")


if __name__ == "__main__":
    main()
