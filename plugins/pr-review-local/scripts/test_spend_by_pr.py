"""Self-check for spend_by_pr.py. Run: python3 plugins/pr-review/scripts/test_spend_by_pr.py"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spend_by_pr import aggregate, skill_calls, skill_table, usage_rows  # noqa: E402


def entry(mid, branch, model="m1", cwd="/r/app", ts="2026-11-10T00:00:00Z", out=10):
    return json.dumps({"cwd": cwd, "gitBranch": branch, "sessionId": "s-" + branch, "timestamp": ts,
                       "message": {"id": mid, "model": model, "usage": {
                           "input_tokens": 100, "output_tokens": out,
                           "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 5000}}})


with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "a.jsonl")
    with open(p, "w") as f:
        f.write("\n".join([entry("1", "feat"), entry("1", "feat"),  # duplicate logged twice
                           entry("2", "feat", model="m2"), entry("3", "main", ts="2026-10-01T00:00:00Z"),
                           entry("4", "feat", cwd="/other"), "not json",
                           json.dumps({"type": "user", "message": {"content": "usage"}})]) + "\n")
    rows = list(usage_rows([p]))
    assert len(rows) == 4, rows
    assert len(list(usage_rows([p], repo="/r/app"))) == 3
    assert len(list(usage_rows([p], since="2026-11-01"))) == 3
    rates = {"m1": {"input": 1, "output": 10, "cache_write": 2, "cache_read": 0.1}}
    g = aggregate(usage_rows([p], repo="/r/app"), rates, root=lambda c: c)
    feat = g[("/r/app", "feat")]
    assert feat["messages"] == 2 and feat["output"] == 20 and feat["cache_read"] == 10000
    # only m1 is priced: (100*1 + 10*10 + 1000*2 + 5000*0.1) / 1e6
    assert abs(feat["usd"] - 2700 / 1e6) < 1e-12, feat["usd"]
    assert feat["unpriced"] == {"m2"}
    assert g[("/r/app", "main")]["messages"] == 1

    def skill_use(tid, skill, cwd="/r/app", ts="2026-11-10T00:00:00Z"):
        return json.dumps({"type": "assistant", "cwd": cwd, "sessionId": "s1", "timestamp": ts, "message": {
            "content": [{"type": "text", "text": "x"},
                        {"type": "tool_use", "id": tid, "name": "Skill", "input": {"skill": skill}},
                        {"type": "tool_use", "id": tid + "b", "name": "Read", "input": {}}]}})

    def typed(uid, cmd, ts="2026-11-12T00:00:00Z"):
        return json.dumps({"type": "user", "uuid": uid, "cwd": "/r/app", "sessionId": "s2", "timestamp": ts,
                           "message": {"content": "<command-name>/%s</command-name>" % cmd}})

    s = os.path.join(d, "s.jsonl")
    with open(s, "w") as f:
        f.write("\n".join([skill_use("t1", "design-gate:design-match"), skill_use("t1", "design-gate:design-match"),
                           skill_use("t2", "design-gate:design-match", ts="2026-10-01T00:00:00Z"),
                           skill_use("t3", "four-hats", cwd="/other"), typed("u1", "design-gate:design-match"),
                           typed("u2", "model"), "not json",
                           json.dumps({"type": "api-request-blob", "message": {
                               "content": [{"text": "<command-name>/model</command-name>"}]}})]) + "\n")
    calls = list(skill_calls([s]))
    assert len(calls) == 5, calls  # duplicate t1 and the blob copy of /model are not counted
    t = {r["skill"]: r for r in skill_table(skill_calls([s], repo="/r/app"))}
    assert set(t) == {"design-gate:design-match", "model"}, t
    dm = t["design-gate:design-match"]
    assert (dm["auto"], dm["typed"], dm["sessions"], dm["last"]) == (2, 1, 2, "2026-11-12"), dm
    assert skill_table(skill_calls([s], since="2026-11-01"))[0]["auto"] == 1
print("ok")
