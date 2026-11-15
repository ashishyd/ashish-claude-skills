"""Self-check for route_model.py. Run: python3 plugins/switchboard/hooks/test_route_model.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from route_model import classify, fits  # noqa: E402

CASES = {
    "what does git rebase --onto do?": "haiku",
    "where is the config for vitest?": "haiku",
    "add a loading spinner to the Save button in Settings.tsx": "sonnet",
    "fix the typo in the README heading": "sonnet",
    "rename getUser to fetchUser across the api folder": "sonnet",
    "design the system for multi-tenant billing and weigh the trade-offs": "opus",
    "review the auth middleware for security holes": "opus",
    "the checkout test is flaky and fails intermittently in CI, find the root cause": "opus",
    "refactor the whole payments module to use the new ledger": "opus",
    "why does the worker hang after 10 minutes in production?": "opus",
    "summarise our discussion so far please": "sonnet",
    "yes": None, "ok go ahead": None, "/model opus": None, "": None,
}
for prompt, want in CASES.items():
    got = classify(prompt)[0]
    assert got == want, (prompt, got, want)

assert fits("opus", "claude-opus-5-5", "high")
assert fits("opus", "claude-opus-5-5", None)
assert not fits("opus", "claude-opus-5-5", "low")
assert not fits("haiku", "claude-opus-5-5", "high")
assert not fits("sonnet", None, None)


def run(payload):
    out = subprocess.run([sys.executable, os.path.join(HERE, "route_model.py")],
                         input=payload, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout


sid = "selfcheck%d" % os.getpid()
state = os.path.join(tempfile.gettempdir(), "switchboard-" + sid)
with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as t:
    t.write(json.dumps({"message": {"model": "claude-opus-5-5"}, "effort": "high"}) + "\n")
try:
    ask = lambda p: json.dumps({"session_id": sid, "prompt": p, "transcript_path": t.name})
    out = json.loads(run(ask("what does HEAD~2 mean in git?")))["hookSpecificOutput"]
    assert out["hookEventName"] == "UserPromptSubmit"
    ctx = out["additionalContext"]
    assert "claude-haiku-5-5" in ctx and "/effort low" in ctx and "claude-opus-5-5" in ctx, ctx
    assert len(ctx) < 400, "context must stay short"
    assert run(ask("where is HEAD stored in git?")) == "", "same advice twice must be silent"
    assert run(ask("design the system for audit logs with trade-offs")) == "", \
        "already on Opus high: must be silent"
    assert "Sonnet" in run(ask("add a test for the parser in parse.py"))
    with open(t.name, "a") as f:
        f.write(json.dumps({"effort": "low"}) + "\n")
    up = run(ask("find the root cause of the deadlock in the job queue"))
    assert "/effort high" in up and "/model" not in up and "better result" in up, up
    assert run("not json") == "", "bad input must be silent"
    assert run(json.dumps({"prompt": 42})) == "", "odd input must be silent"
finally:
    os.remove(t.name)
    if os.path.exists(state):
        os.remove(state)
print("ok: %d prompt cases, fit check, transcript model, dedupe, bad input" % len(CASES))
