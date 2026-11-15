"""Self-check for the feature-flow hooks. Run: python3 plugins/feature-flow/hooks/test_hooks.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from detect_feature import is_feature  # noqa: E402
from readme_gate import verdict  # noqa: E402

CASES = {
    "add a new feature to export invoices as CSV": True,
    "I want a feature that emails weekly reports": True,
    "build a new settings page for notifications": True,
    "implement the dark mode feature": True,
    "feature request: bulk delete for admins": False,  # "delete" reads as removal
    "new feature: bulk archive for admins": True,
    "fix the bug in the export feature": False,
    "why does the login feature fail?": False,
    "add a feature flag for checkout": False,
    "rename the feature folder": False,
    "what does this function do?": False,
    "/new-feature": False, "yes": False, "": False,
}
for prompt, want in CASES.items():
    assert is_feature(prompt) == want, (prompt, want)


def run(script, payload):
    out = subprocess.run([sys.executable, os.path.join(HERE, script)],
                         input=json.dumps(payload), capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout


out = json.loads(run("detect_feature.py", {"prompt": "add a new feature for CSV export"}))
assert "feature-flow:new-feature" in out["hookSpecificOutput"]["additionalContext"]
assert run("detect_feature.py", {"prompt": "fix the typo"}) == ""
assert run("detect_feature.py", {}) == ""  # bad input: silent, exit 0


def sh(cwd, *cmd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


with tempfile.TemporaryDirectory() as root:
    root = os.path.realpath(root)
    sh(root, "git", "init", "-q")
    sh(root, "git", "-c", "user.email=t@t", "-c", "user.name=t", "commit",
       "-q", "--allow-empty", "-m", "init")
    write(root, "app.py", "x = 1\n")
    assert verdict(root) is None, "no checklist: gate off"

    write(root, ".claude/features/csv.md", "# Feature: csv\nstatus: in-progress\n")
    assert "README.md" in verdict(root), "code changed, README not: block"

    stop = {"cwd": root, "stop_hook_active": False}
    assert json.loads(run("readme_gate.py", stop))["decision"] == "block"
    assert run("readme_gate.py", dict(stop, stop_hook_active=True)) == ""

    write(root, "README.md", "# app\n")
    assert verdict(root) is None, "README changed: allow"

    os.remove(os.path.join(root, "README.md"))
    write(root, ".claude/features/csv.md", "# Feature: csv\nstatus: done\n")
    assert verdict(root) is None, "checklist done: gate off"

    os.remove(os.path.join(root, "app.py"))
    write(root, ".claude/features/csv.md", "# Feature: csv\nstatus: in-progress\n")
    assert verdict(root) is None, "only the checklist changed: nothing to document"

assert run("readme_gate.py", {"cwd": "/"}) == ""  # not a repo: fail open
print("ok")
