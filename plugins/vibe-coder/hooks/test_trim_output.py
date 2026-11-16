"""Self-check for trim_output.py. Run: python3 plugins/vibe-coder/hooks/test_trim_output.py"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trim_output import trim, wrap  # noqa: E402

for c in ["npm install", "pnpm run test", "pytest -q tests/", "cargo build", "docker build .", "make"]:
    assert wrap(c), c
for c in ["ls -la", "git status", "npm install | tail", "pytest > out.txt", "make && make test",
          "npm install # no-trim", "cat package.json", "echo $(npm test)"]:
    assert wrap(c) is None, c

lines = ["line %d\n" % i for i in range(500)]
lines[250] = "ERROR: boom\n"
out = trim(lines)
assert out[0] == "line 0\n" and out[-1] == "line 499\n"
assert "ERROR: boom\n" in out and len(out) < 130, len(out)
assert trim(["x\n"] * 50) == ["x\n", "  [previous line repeated 49 more times]\n"]
assert trim(["a\n"] * 3 + ["b\n"]) == ["a\n", "  [previous line repeated 2 more times]\n", "b\n"]
short = ["l%d\n" % i for i in range(20)]
assert trim(short) == short

# end to end: exit code survives the pipe, output is trimmed
cmd = wrap("make")
assert cmd
real = cmd.replace("{ make ;", "{ python3 -c 'import sys;[print(i) for i in range(400)];sys.exit(3)' ;")
r = subprocess.run(["bash", "-c", real], capture_output=True, text=True)
assert r.returncode == 3, r.returncode
assert "trim_output: dropped" in r.stdout and r.stdout.count("\n") < 130
r = subprocess.run(["zsh", "-c", real], capture_output=True, text=True)
assert r.returncode == 3, ("zsh", r.returncode)

def hook(payload):
    return subprocess.run([sys.executable, os.path.join(HERE, "trim_output.py")],
                          input=payload, capture_output=True, text=True)
r = hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "npm ci", "description": "x"}}))
out = json.loads(r.stdout)["hookSpecificOutput"]
assert out["hookEventName"] == "PreToolUse" and "permissionDecision" not in out
assert out["updatedInput"]["description"] == "x" and "--filter" in out["updatedInput"]["command"]
assert hook(json.dumps({"tool_input": {"command": "ls"}})).stdout == ""
assert hook("not json").returncode == 0
print("ok")
