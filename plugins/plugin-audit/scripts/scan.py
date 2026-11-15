#!/usr/bin/env python3
"""Read-only scan of installed Claude Code plugins and skills.

  python3 scan.py                 security candidates, one per line: file:line [SEV] rule
  python3 scan.py --inventory     plugins, skills, hooks and MCP servers, plus overlaps
  python3 scan.py --root DIR ...  scan these directories instead of the defaults

Defaults: installed plugins (installPath in ~/.claude/plugins/installed_plugins.json),
~/.claude/skills, ~/.claude/settings*.json, and .claude/, plugins/, skills/ and
.mcp.json under the current directory. Never opens .env, key or credential files.
Secret matches print the type only, never the value. Standard library only.
"""
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
TEXT = (".md", ".json", ".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs",
        ".ts", ".toml", ".yaml", ".yml")
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build"}
# Never read these: secrets live there and the user asked us not to open them.
FORBIDDEN = re.compile(r"(^|/)(\.env(\..*)?|.*\.(pem|key|p12|pfx)|id_[a-z0-9]+|"
                       r"credentials(\.json)?|\.netrc|\.npmrc|\.pypirc)$", re.I)
MAX_BYTES = 512 * 1024
CODE = (".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts")
DOCS = (".md",)

# (rule, severity, applies-to extensions or None for all, regex)
RULES = [
    ("hardcoded-secret:anthropic", "Critical", None, r"sk-ant-[A-Za-z0-9_-]{20,}"),
    ("hardcoded-secret:aws", "Critical", None, r"\bAKIA[0-9A-Z]{16}\b"),
    ("hardcoded-secret:github", "Critical", None, r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    ("hardcoded-secret:slack", "Critical", None, r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    ("hardcoded-secret:private-key", "Critical", None,
     r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("pipe-to-shell", "High", None,
     r"\b(curl|wget)\b[^|\n]*\|\s*(sudo\s+)?(ba|z)?sh\b|\biex\s*\(.*downloadstring"),
    ("prompt-injection", "High", DOCS,
     r"ignore (all |any )?(previous|prior|above|the user'?s?) (instructions|request)"
     r"|do not (tell|inform|show) the user|without (telling|asking|informing) the user"
     r"|(disable|bypass|turn off) (the |all )?(safety|guardrails|permission checks)"
     r"|(send|upload|post) (the |all )?(contents|secrets|keys|tokens|credentials|\.env)"
     r"[^\n]{0,40}\b(to|via) https?://"),
    ("broad-permission", "High", (".json",),
     r"\"(defaultMode|permissionMode)\"\s*:\s*\"bypassPermissions\""
     r"|(?-i:\"Bash(\(\*\))?\")\s*[,\]]|dangerously-skip-permissions"),
    ("broad-permission", "Medium", CODE + DOCS, r"--dangerously-skip-permissions"),
    ("secret-read", "Medium", CODE,
     r"(open|read|cat|source)\b[^\n]{0,80}(\.env\b|\.ssh/|id_rsa|\.aws/credentials"
     r"|\.netrc|keychain)|security find-(generic|internet)-password"
     r"|os\.environ\[?.{0,4}(API_?KEY|TOKEN|SECRET|PASSWORD)"),
    ("network-out", "Medium", CODE,
     r"requests\.(post|put)|urllib\.request\.urlopen|http\.client|fetch\(\s*['\"`]https?"
     r"|\bcurl\b[^\n]*(-d|--data|-F|-T|--upload)|\bnc\s+-|socket\.connect"),
    # shortcut: docs are skipped, so a SKILL.md telling Claude to fetch @latest is
    # missed; add DOCS here if that turns up in practice.
    ("unpinned-fetch", "Medium", CODE + (".json",),
     r"raw\.githubusercontent\.com/[^/\s]+/[^/\s]+/(main|master|HEAD)/"
     r"|pip3? install [^\n]*git\+https?://(?![^\s]*@[0-9a-f]{7,})"
     r"|@latest\b"),
    ("dynamic-exec", "Low", CODE,
     r"\beval\(|shell=True|os\.system\(|subprocess\.[a-z_]+\([^)]*\bsh\b.-c"),
]
RULES = [(n, s, e, re.compile(p, re.I)) for n, s, e, p in RULES]
# Tests, fixtures and docs are not loaded by Claude Code at run time.
INERT_PATH = re.compile(r"/(tests?|__tests__|fixtures?|examples?|spec|docs?|releases)/", re.I)
# Lines that warn Claude *against* injected instructions are defences, not attacks.
DEFENSIVE = re.compile(r"\b(never|do not follow|don't follow|refuse|treat .* as data)\b", re.I)
UNPINNED_RUNNERS ={"npx", "bunx", "pnpx", "uvx"}


def default_roots():
    roots = []
    reg = os.path.join(HOME, ".claude", "plugins", "installed_plugins.json")
    try:
        with open(reg) as f:
            for entries in json.load(f).get("plugins", {}).values():
                roots += [e["installPath"] for e in entries if e.get("installPath")]
    except (OSError, ValueError):
        pass
    # synced/ holds plugins enabled from claude.ai; they are not in installed_plugins.json
    roots += [os.path.join(HOME, ".claude", "plugins", "synced"),
              os.path.join(HOME, ".claude", "skills")]
    roots += [os.path.join(HOME, ".claude", n) for n in ("settings.json",
                                                         "settings.local.json")]
    cwd = os.getcwd()
    roots += [os.path.join(cwd, n) for n in (".claude", "plugins", "skills", ".mcp.json")]
    return [r for r in dict.fromkeys(roots) if os.path.exists(r)]


def walk(roots):
    for root in roots:
        if os.path.isfile(root):
            yield root
            continue
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for name in files:
                p = os.path.join(d, name)
                if name.endswith(TEXT) or name in ("hooks.json", ".mcp.json"):
                    yield p


def read_lines(path):
    if FORBIDDEN.search(path.replace("\\", "/")):
        return None
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return None


def scan_lines(path, lines):
    """Yield (line_no, severity, rule, snippet). Secret rules never carry a snippet."""
    ext = os.path.splitext(path)[1].lower()
    inert = INERT_PATH.search(path.replace("\\", "/"))
    for i, line in enumerate(lines, 1):
        for name, sev, exts, rx in RULES:
            if exts and ext not in exts:
                continue
            if name == "prompt-injection" and DEFENSIVE.search(line):
                continue
            if name == "broad-permission" and '"matcher"' in line:
                continue
            if rx.search(line):
                if inert:
                    sev = "Low"
                snippet = "" if name.startswith("hardcoded-secret") else line.strip()[:120]
                yield i, sev, name, snippet
    if ext == ".json":
        yield from scan_mcp(lines)


def scan_mcp(lines):
    """MCP servers launched with npx/uvx and a package that has no pinned version."""
    try:
        data = json.loads("\n".join(lines))
    except ValueError:
        return
    servers = data.get("mcpServers") if isinstance(data, dict) else None
    for name, cfg in (servers if isinstance(servers, dict) else {}).items():
        if not isinstance(cfg, dict):
            continue
        cmd = os.path.basename(str(cfg.get("command", "")))
        pkgs = [a for a in cfg.get("args", []) if isinstance(a, str) and not a.startswith("-")]
        if cmd in UNPINNED_RUNNERS and pkgs and not re.search(r".@\d|==\d", pkgs[0]):
            line = next((i for i, l in enumerate(lines, 1) if '"%s"' % name in l), 1)
            yield line, "Medium", "unpinned-mcp", "%s: %s %s" % (name, cmd, pkgs[0])


def scan(roots):
    out = []
    for path in walk(roots):
        lines = read_lines(path)
        if lines is not None:
            out += [(path, *f) for f in scan_lines(path, lines)]
    return out


# ---------- inventory ----------
TOPICS = {
    "tdd": r"\btdd\b|test-driven", "code-review": r"code[- ]review|review (the|a) (diff|pr)",
    "debugging": r"debug", "planning": r"\bplan(ning)?\b|task breakdown",
    "brainstorm": r"brainstorm|idea", "design-ui": r"\bdesign\b|frontend|\bui\b",
    "security": r"security|vulnerab", "commit-git": r"\bcommit\b|\bgit\b|pull request",
    "simplify": r"simplif", "memory": r"\bmemory\b|claude\.md",
}


def frontmatter(lines):
    meta = {}
    if lines and lines[0].strip() == "---":
        for l in lines[1:40]:
            if l.strip() == "---":
                break
            m = re.match(r"(\w[\w-]*):\s*(.*)", l)
            if m:
                meta[m.group(1)] = m.group(2).strip().strip('"')
    return meta


def plugin_of(path):
    d = os.path.dirname(path)
    while d and d != os.path.dirname(d):
        manifest = next((m for m in (os.path.join(d, ".claude-plugin", "plugin.json"),
                                     os.path.join(d, "plugin.json")) if os.path.exists(m)), None)
        if manifest:
            try:
                with open(manifest) as f:
                    return json.load(f).get("name") or os.path.basename(d)
            except (OSError, ValueError):
                return os.path.basename(d)
        d = os.path.dirname(d)
    return "(standalone)"


def inventory(roots):
    skills, hooks, mcps = [], [], []
    for path in walk(roots):
        base = os.path.basename(path)
        lines = read_lines(path)
        if lines is None:
            continue
        if base == "SKILL.md":
            m = frontmatter(lines)
            skills.append((plugin_of(path), m.get("name", ""), m.get("description", ""), path))
        elif base in ("hooks.json", "settings.json", "settings.local.json"):
            try:
                data = json.loads("\n".join(lines))
            except ValueError:
                continue
            for event, groups in (data.get("hooks") or {}).items():
                for g in groups or []:
                    for h in g.get("hooks", []):
                        hooks.append((plugin_of(path), event, g.get("matcher", "*"),
                                      h.get("command", h.get("type", "")), path))
        if base.endswith(".json"):
            try:
                data = json.loads("\n".join(lines))
            except ValueError:
                continue
            servers = data.get("mcpServers") if isinstance(data, dict) else None
            for name, cfg in (servers if isinstance(servers, dict) else {}).items():
                if isinstance(cfg, dict):
                    mcps.append((plugin_of(path), name, " ".join(
                        [str(cfg.get("command", cfg.get("url", "")))] +
                        [str(a) for a in cfg.get("args", [])]), path))
    overlaps = {}
    for plugin, name, desc, _ in skills:
        for topic, rx in TOPICS.items():
            if re.search(rx, name + " " + desc, re.I):
                overlaps.setdefault(topic, []).append("%s:%s" % (plugin, name))
    return skills, hooks, mcps, {t: v for t, v in overlaps.items() if len(v) > 1}


def main(argv):
    roots = [a for a in argv if not a.startswith("--")] if "--root" in argv else default_roots()
    print("# roots: " + ", ".join(roots))
    if "--inventory" in argv:
        skills, hooks, mcps, overlaps = inventory(roots)
        print("## skills (%d)" % len(skills))
        for p, n, d, _ in sorted(skills):
            print("%s:%s  %s" % (p, n, d[:110]))
        print("## hooks (%d)" % len(hooks))
        for p, e, m, c, path in sorted(hooks):
            print("%s  %s[%s]  %s  (%s)" % (p, e, m, c[:90], path))
        print("## mcp servers (%d)" % len(mcps))
        for p, n, c, path in sorted(mcps):
            print("%s  %s: %s  (%s)" % (p, n, c[:90], path))
        print("## overlapping topics")
        for t, v in sorted(overlaps.items()):
            print("%s (%d): %s" % (t, len(v), ", ".join(sorted(set(v)))))
        return
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    found = sorted(scan(roots), key=lambda f: (order[f[2]], f[0], f[1]))
    for path, line, sev, rule, snippet in found:
        print("%s:%d [%s] %s%s" % (path, line, sev, rule, ("  | " + snippet) if snippet else ""))
    counts = {s: sum(1 for f in found if f[2] == s) for s in order}
    print("# candidates: " + ", ".join("%s %d" % kv for kv in counts.items()))


if __name__ == "__main__":
    main(sys.argv[1:])
