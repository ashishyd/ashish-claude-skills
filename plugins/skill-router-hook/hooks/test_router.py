"""Self-check: router.sh prints router.md, and every skill the index names exists in this repo.
Run: python3 plugins/skill-router-hook/hooks/test_router.py"""
import os
import re
import subprocess

here = os.path.dirname(os.path.abspath(__file__))
plugin = os.path.dirname(here)
repo = os.path.dirname(os.path.dirname(plugin))

out = subprocess.run(["sh", os.path.join(here, "router.sh")], capture_output=True, text=True,
                     env={**os.environ, "CLAUDE_PLUGIN_ROOT": plugin}, check=True).stdout
index = open(os.path.join(here, "router.md"), encoding="utf-8").read()
assert out == index, "router.sh output differs from router.md"

names = set()
for line in index.splitlines():
    if line.startswith("| ") and not line.startswith("| Moment") and not line.startswith("|---"):
        names |= {n.strip() for n in line.rsplit("|", 2)[1].replace(", then ", ",").split(",")}
assert len(names) > 20, names
for name in names:
    if ":" in name:
        p, s = name.split(":")
        path = os.path.join(repo, "plugins", p, "skills", s, "SKILL.md")
    else:
        path = os.path.join(repo, "skills", name, "SKILL.md")
    assert re.fullmatch(r"[a-z0-9:-]+", name) and os.path.isfile(path), f"index names a missing skill: {name}"
print("ok", len(names), "skills")
