"""Self-check for route.py. Run: python3 plugins/quality-gates/hooks/test_route.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from route import skills_for  # noqa: E402

CASES = {
    "src/lib/money.ts": ["typescript-types"],
    "src/lib/money.test.ts": ["vitest-tests"],
    "e2e/checkout.spec.ts": ["playwright-tests"],
    "playwright.config.ts": ["playwright-tests"],
    "src/components/Button.tsx": ["typescript-types", "design-audit", "ux-audit"],
    "src/app/api/users/route.ts": ["typescript-types", "security-code-audit"],
    "src/auth/session.py": ["security-code-audit"],
    "db/001_init.sql": ["security-code-audit"],
    "styles/app.css": ["design-audit", "ux-audit"],
    "README.md": [],
    "main.go": [],
    "": [],
}
for path, want in CASES.items():
    got = skills_for(path)
    assert got == want, (path, got, want)


def run(payload):
    out = subprocess.run([sys.executable, os.path.join(HERE, "route.py")],
                         input=payload, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout


sid = "selfcheck%d" % os.getpid()
state = os.path.join(tempfile.gettempdir(), "quality-gates-" + sid)
edit = json.dumps({"session_id": sid, "tool_input": {"file_path": "/x/a.tsx"}})
try:
    first = json.loads(run(edit))["hookSpecificOutput"]
    assert first["hookEventName"] == "PostToolUse"
    assert "quality-gates:typescript-types" in first["additionalContext"]
    assert "quality-gates:ux-audit" in first["additionalContext"]
    assert run(edit) == "", "second edit in a session must be silent"
    assert run("not json") == "", "bad input must be silent"
finally:
    if os.path.exists(state):
        os.remove(state)
print("ok: %d path cases, once-per-session, bad input" % len(CASES))
