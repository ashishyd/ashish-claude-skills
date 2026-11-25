"""Self-check for session_digest.py. Run: python3 plugins/vibe-coder/scripts/test_session_digest.py"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from session_digest import moments, slug  # noqa: E402


def user(content, ts, **kw):
    return json.dumps({"type": "user", "timestamp": ts, "message": {"role": "user", "content": content}, **kw})


def asst(blocks, ts):
    return json.dumps({"type": "assistant", "timestamp": ts, "message": {"role": "assistant", "content": blocks}})


def err(tid, text, ts):
    return user([{"type": "tool_result", "tool_use_id": tid, "is_error": True, "content": text}], ts)


lines = [
    user("Don't use jQuery; add a login page", "2026-11-01T00:00:01Z"),  # opening request: not a correction
    asst([{"type": "text", "text": "I'll refactor the auth module first."},
          {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "npm test"}}], "2026-11-01T00:00:02Z"),
    err("t1", "Exit code 1: jest not found", "2026-11-01T00:00:03Z"),
    asst([{"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "npm test"}}], "2026-11-01T00:00:04Z"),
    err("t2", "Exit code 1: jest not found", "2026-11-01T00:00:05Z"),
    asst([{"type": "tool_use", "id": "t3", "name": "Edit", "input": {"file_path": "a.ts"}}], "2026-11-01T00:00:06Z"),
    user([{"type": "tool_result", "tool_use_id": "t3", "content":
           "The user doesn't want to proceed with this tool use. The tool use was rejected. Don't touch auth."}],
         "2026-11-01T00:00:07Z"),
    user("No, I said don't refactor, just add the page", "2026-11-01T00:00:08Z"),
    user("<system-reminder>don't do X</system-reminder>", "2026-11-01T00:00:09Z"),  # wrapper only: ignored
    user("don't", "2026-11-01T00:00:10Z", isMeta=True),  # meta: ignored
    user("[Request interrupted by user]", "2026-11-01T00:00:11Z"),
    user("looks good, thanks", "2026-11-01T00:00:12Z"),  # not a correction
    user("add a skill: do not design for rare cases", "2026-11-01T00:00:13Z"),  # instruction, not pushback
    user("<task-notification><status>completed</status><note>no, stop</note></task-notification>", "2026-11-01T00:00:14Z"),
    "not json",
]
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "s.jsonl")
    with open(p, "w") as f:
        f.write("\n".join(lines) + "\n")
    ms = list(moments(p))
    kinds = [m["kind"] for m in ms]
    assert kinds == ["tool-error", "rejected", "correction", "interrupted"], kinds
    assert ms[0]["count"] == 2 and ms[0]["tool"] == "Bash", ms[0]
    assert "Don't touch auth" in ms[1]["said"] and ms[1]["tool"] == "Edit"
    assert "refactor the auth" in ms[2]["context"]
    assert [m["kind"] for m in moments(p, since="2026-11-01T00:00:07Z")] == ["correction", "interrupted"]
assert slug("/Users/a/my_repo.v2") == "-Users-a-my-repo-v2"
print("ok")
