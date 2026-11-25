"""Self-check for recheck.py. Run: python3 plugins/design-gate/hooks/test_recheck.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from recheck import gaps_naming, hint_for  # noqa: E402

REPORT = """# Design gap report: home
## Gaps
- [ ] G01 [MISSING-FEATURE] [P0] Export button
  Where: src/pages/Reports.tsx:42
- [x] G02 [DIFFERS] [P2] Radius
  Where: src/components/Card.tsx:8
- [ ] G03 [DIFFERS] [P1] Header copy
  Where: src/pages/Reports.tsx:10
"""
assert gaps_naming(REPORT, "src/pages/Reports.tsx") == ["G01", "G03"]
assert gaps_naming(REPORT, "src/components/Card.tsx") == ["G02"]
assert gaps_naming(REPORT, "src/other.tsx") == []

repo = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(repo, ".git"))
    os.makedirs(os.path.join(repo, "src", "pages"))
    reports = os.path.join(repo, ".claude", "design-gate")

    # No reports yet: silent.
    assert hint_for(os.path.join(repo, "src/pages/Reports.tsx"), set()) == (None, [])

    os.makedirs(reports)
    with open(os.path.join(reports, "home.md"), "w") as f:
        f.write(REPORT)

    hint, keys = hint_for(os.path.join(repo, "src/pages/Reports.tsx"), set())
    assert "home.md (G01, G03)" in hint and keys == ["home.md|src/pages/Reports.tsx"], hint
    # Same file again in the same session: silent; an unnamed UI file gets the generic hint once.
    assert hint_for(os.path.join(repo, "src/pages/Reports.tsx"), set(keys))[0] is None
    hint, keys2 = hint_for(os.path.join(repo, "src/pages/Other.tsx"), set(keys))
    assert hint.startswith("design-gate: reports exist (home.md)") and keys2 == ["*generic*"]
    assert hint_for(os.path.join(repo, "src/pages/Other.tsx"), {"*generic*"})[0] is None
    # Non-UI files and the reports themselves never hint.
    assert hint_for(os.path.join(repo, "src/lib/api.ts"), set()) == (None, [])
    assert hint_for(os.path.join(reports, "home.md"), set()) == (None, [])

    # End to end through stdin: hint once, then silent; bad input never fails.
    sid = "selfcheck%d" % os.getpid()
    edit = json.dumps({"session_id": sid,
                       "tool_input": {"file_path": os.path.join(repo, "src/pages/Reports.tsx")}})
    run = lambda p: subprocess.run([sys.executable, os.path.join(HERE, "recheck.py")],
                                   input=p, capture_output=True, text=True)
    first = run(edit)
    assert first.returncode == 0 and "G01, G03" in json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"]
    assert run(edit).stdout == ""
    assert run("not json").returncode == 0
finally:
    shutil.rmtree(repo)
    try:
        os.remove(os.path.join(tempfile.gettempdir(), "design-gate-selfcheck%d" % os.getpid()))
    except OSError:
        pass
print("recheck ok")
