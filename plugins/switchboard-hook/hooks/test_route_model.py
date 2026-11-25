"""Self-check for route_model.py. Run: python3 plugins/switchboard/hooks/test_route_model.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from route_model import classify, fits, worth_routing, context_tokens, artifact_urls  # noqa: E402

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

CODE, GEN, LOOK = "a routine code change", "general work", "a quick question or lookup"
assert worth_routing("opus", "x", "claude-sonnet-5-5", "medium"), "step up model: route"
assert worth_routing("opus", "x", "claude-opus-5-5", "low"), "step up effort: route"
assert not worth_routing("opus", "x", "claude-opus-5-5", "max"), "effort step-down: inline"
assert worth_routing("sonnet", CODE, "claude-opus-5-5", "high"), "code work down: route"
assert not worth_routing("sonnet", GEN, "claude-opus-5-5", "high"), "chat down: inline"
assert not worth_routing("haiku", LOOK, "claude-opus-5-5", "high"), "lookup down: inline"
assert not worth_routing("haiku", LOOK, None, None), "lookup, unknown model: inline"
assert worth_routing("sonnet", CODE, None, None), "unknown model: route with skip clause"
assert not worth_routing("opus", "x", "claude-fable-5-2", "high"), "never down from Fable for hard work"


def run(payload):
    out = subprocess.run([sys.executable, os.path.join(HERE, "route_model.py")],
                         input=payload, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout


with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as t:
    t.write(json.dumps({"message": {"model": "claude-opus-5-5"}, "effort": "high"}) + "\n")
try:
    ask = lambda p: json.dumps({"session_id": "selfcheck", "prompt": p, "transcript_path": t.name})
    ctx_of = lambda p: (json.loads(run(ask(p)) or "{}").get("hookSpecificOutput") or {}).get(
        "additionalContext", "")
    assert run(ask("what does HEAD~2 mean in git?")) == "", "lookup on Opus: answer inline"
    out = json.loads(run(ask("add a test for the parser in parse.py")))["hookSpecificOutput"]
    assert out["hookEventName"] == "UserPromptSubmit"
    ctx = out["additionalContext"]
    assert 'model "sonnet"' in ctx and 'effort "medium"' in ctx and "Agent tool" in ctx, ctx
    assert "claude-opus-5-5" in ctx, "must name the current setting"
    assert len(ctx) < 600, "context must stay short"
    assert 'model "sonnet"' in ctx_of(("fix the typo in the README heading")), \
        "every prompt worth routing must be routed, not just the first"
    assert run(ask("design the system for audit logs with trade-offs")) == "", \
        "already on Opus high: must be silent"
    with open(t.name, "a") as f:
        f.write(json.dumps({"effort": "low"}) + "\n")
    up = ctx_of(("find the root cause of the deadlock in the job queue"))
    assert 'model "opus"' in up and 'effort "high"' in up and "better result" in up, up
    assert run("not json") == "", "bad input must be silent"
    assert run(json.dumps({"prompt": 42})) == "", "odd input must be silent"
finally:
    os.remove(t.name)
usage = lambda n: json.dumps({"message": {"model": "claude-opus-5-5", "usage": {
    "input_tokens": 4, "cache_creation_input_tokens": 1000, "cache_read_input_tokens": n,
    "output_tokens": 9}}, "effort": "high"}) + "\n"
with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as t:
    msg = lambda *c: json.dumps({"message": {"content": list(c)}}) + "\n"
    t.write(usage(10))
    t.write(msg({"type": "text", "text": "pasted https://claude.ai/artifact/Pasted9 is not ours"}))
    t.write(msg({"type": "tool_use", "id": "t1", "name": "Artifact", "input": {"file_path": "a.html"}}))
    t.write(msg({"type": "tool_result", "tool_use_id": "t1",
                 "content": "Published https://claude.ai/artifact/AbC123"}))
    t.write(msg({"type": "tool_use", "id": "t2", "name": "Artifact",
                 "input": {"url": "https://claude.ai/code/artifact/0f-9e"}}))
    t.write(msg({"type": "tool_use", "id": "t3", "name": "Artifact",
                 "input": {"url": "https://claude.ai/artifact/AbC123"}}))
    t.write(msg({"type": "tool_use", "id": "t4", "name": "Bash", "input": {"command": "x"}}))
    t.write(msg({"type": "tool_result", "tool_use_id": "t4",
                 "content": "grep hit https://claude.ai/artifact/Grep7"}))
    t.write(usage(130_000))
try:
    assert context_tokens(t.name) == 131_004, "last turn's usage, all three input fields"
    assert artifact_urls(t.name) == ["https://claude.ai/artifact/AbC123",
                                     "https://claude.ai/code/artifact/0f-9e"], "Artifact calls only, deduped, in order"
    assert context_tokens("/no/such/file") == 0 and artifact_urls("/no/such/file") == []
    sid = "ctxcheck%d" % os.getpid()
    ask = lambda p: json.dumps({"session_id": sid, "prompt": p, "transcript_path": t.name})
    out = run(ask("design the system for audit logs with trade-offs"))
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "~131k tokens" in ctx and "AbC123" in ctx and "session-fit" in ctx, ctx
    assert "Agent tool" not in ctx, "on Opus high: context hint only, no routing"
    assert run(ask("design the system for audit logs with trade-offs")) == "", "once per +100k"
    with open(t.name, "a") as f:
        f.write(usage(210_000))
    assert "~211k" in run(ask("design the queue retry policy with trade-offs")), "next step speaks"
    assert run(ask("ok go ahead")) == "", "acks stay silent"
finally:
    os.remove(t.name)
    state = os.path.join(tempfile.gettempdir(), "switchboard-ctx-" + sid)
    if os.path.exists(state):
        os.remove(state)
print("ok: %d prompt cases, fit check, cost gate, transcript model, routing, context size, artifacts, bad input" % len(CASES))
