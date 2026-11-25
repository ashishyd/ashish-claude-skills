#!/usr/bin/env python3
"""Claude Code token usage per git branch / PR, from local session transcripts.

Reads ~/.claude/projects/*/*.jsonl (read-only). Each assistant entry carries
cwd, gitBranch and message.usage; entries are de-duplicated by message id
(one response can be logged more than once). Groups by repo + branch, and maps
branches to PRs with `gh pr list` when --gh is given.

Dollars are shown only with --rates FILE, a JSON map of model id to USD per
million tokens: {"claude-opus-5-5": {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}}.
This script never assumes a price.

Usage: spend_by_pr.py [--repo PATH] [--since YYYY-MM-DD] [--gh] [--rates FILE] [--json]
"""
import argparse
import glob
import json
import os
import subprocess
import sys
from collections import defaultdict

FIELDS = ("input", "output", "cache_write", "cache_read")


def usage_rows(paths, repo=None, since=None):
    """Yield (repo, branch, session, model, tokens dict) once per unique message."""
    seen = set()
    for path in paths:
        try:
            f = open(path, encoding="utf-8")
        except OSError:
            continue
        with f:
            for line in f:
                if '"usage"' not in line:
                    continue
                try:
                    e = json.loads(line)
                    msg = e["message"]
                    u = msg["usage"]
                except (ValueError, KeyError, TypeError):
                    continue
                key = msg.get("id") or e.get("requestId") or e.get("uuid")
                if key in seen:
                    continue
                seen.add(key)
                cwd = e.get("cwd") or "?"
                if repo and not (cwd == repo or cwd.startswith(repo.rstrip("/") + "/")):
                    continue
                if since and (e.get("timestamp") or "") < since:
                    continue
                yield (cwd, e.get("gitBranch") or "(no branch)", e.get("sessionId"),
                       msg.get("model") or "?", {
                           "input": u.get("input_tokens") or 0,
                           "output": u.get("output_tokens") or 0,
                           "cache_write": u.get("cache_creation_input_tokens") or 0,
                           "cache_read": u.get("cache_read_input_tokens") or 0})


def toplevel(cwd, cache={}):
    if cwd not in cache:
        try:
            cache[cwd] = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                                        capture_output=True, text=True, timeout=5).stdout.strip() or cwd
        except (OSError, subprocess.SubprocessError):
            cache[cwd] = cwd
    return cache[cwd]


def aggregate(rows, rates=None, root=toplevel):
    groups = defaultdict(lambda: {"sessions": set(), "messages": 0, "usd": 0.0,
                                  "unpriced": set(), **{k: 0 for k in FIELDS}})
    for cwd, branch, session, model, tok in rows:
        g = groups[(root(cwd), branch)]
        g["sessions"].add(session)
        g["messages"] += 1
        for k in FIELDS:
            g[k] += tok[k]
        if rates is not None:
            r = rates.get(model)
            if r:
                g["usd"] += sum(tok[k] * r.get(k, 0) for k in FIELDS) / 1e6
            elif model != "<synthetic>":
                g["unpriced"].add(model)
    return groups


def prs_for(repo):
    try:
        out = subprocess.run(["gh", "pr", "list", "--state", "all", "--limit", "500",
                              "--json", "number,headRefName,title,state"],
                             cwd=repo, capture_output=True, text=True, timeout=30)
        return {p["headRefName"]: p for p in json.loads(out.stdout or "[]")}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="only sessions run inside this path")
    ap.add_argument("--since", help="ISO date, e.g. 2026-11-01")
    ap.add_argument("--gh", action="store_true", help="map branches to PRs with gh")
    ap.add_argument("--rates", help="JSON file of USD per million tokens by model")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--projects", default=os.path.expanduser("~/.claude/projects"))
    a = ap.parse_args(argv)
    rates = json.load(open(a.rates)) if a.rates else None
    repo = os.path.realpath(a.repo) if a.repo else None
    paths = glob.glob(os.path.join(a.projects, "*", "*.jsonl"))
    groups = aggregate(usage_rows(paths, repo, a.since), rates)
    pr_maps = {}
    rows = []
    for (root, branch), g in groups.items():
        if a.gh and root not in pr_maps:
            pr_maps[root] = prs_for(root) if os.path.isdir(root) else {}
        pr = pr_maps.get(root, {}).get(branch)
        rows.append({"repo": root, "branch": branch,
                     "pr": "#%d %s" % (pr["number"], pr["state"].lower()) if pr else "",
                     "sessions": len(g["sessions"]), "messages": g["messages"],
                     **{k: g[k] for k in FIELDS},
                     "usd": round(g["usd"], 2) if rates is not None else None,
                     "unpriced_models": sorted(g["unpriced"])})
    rows.sort(key=lambda r: -(r["usd"] if r["usd"] is not None else
                              r["input"] + r["output"] + r["cache_write"] + r["cache_read"]))
    if a.json:
        json.dump(rows, sys.stdout, indent=1)
        return
    head = ["repo", "branch", "pr", "sessions", "input", "output", "cache_write", "cache_read"]
    if rates is not None:
        head.append("usd")
    print("| " + " | ".join(head) + " |\n|" + "---|" * len(head))
    for r in rows:
        r = dict(r, repo=os.path.basename(r["repo"]))
        print("| " + " | ".join(str(r[h]) for h in head) + " |")
    missing = sorted({m for r in rows for m in r["unpriced_models"]})
    if missing:
        print("\nNo rate given for: " + ", ".join(missing) + " (their tokens are not in usd).")


if __name__ == "__main__":
    main()
