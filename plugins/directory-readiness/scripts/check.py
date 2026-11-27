#!/usr/bin/env python3
"""Local pre-check of a Claude plugin folder against the Claude directory pre-submission checklist.

Usage: python3 check.py <plugin-or-marketplace-dir> [...]   (exit 1 if any BLOCK)

Levels mirror the directory validator: BLOCK (cannot submit), HOLD (a reviewer must clear it),
WARN (can submit), NOTE (info). Sources: claude.com/docs/plugins/pre-submission-checklist,
claude.com/docs/plugins/platform-support, and the Agent Skills spec for SKILL.md fields ("spec").
shortcut: portal-only checks (name taken, brand look-alikes, security scan) cannot run locally.
"""
import json
import os
import re
import struct
import sys

RESERVED = {"claude", "anthropic", "official", "plugin", "mcp", "test"}
RESERVED_PREFIXES = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")
RESERVED_EXACT = {"anthropics", "claude-code", "claude-mods"}
NEGATION_RE = re.compile(r"(?i)\b(no|not|never|don't|do not|must not|without)\b")
NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
JUNK = {".DS_Store", "Thumbs.db", "desktop.ini", "__MACOSX"}
WIN_DEVICES = {"con", "prn", "aux", "nul"} | {f"com{i}" for i in range(1, 10)} | {f"lpt{i}" for i in range(1, 10)}
MEDIA_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".woff", ".woff2", ".ttf", ".otf"}
REGISTRY_CFG = {".npmrc", "bunfig.toml", "uv.toml"}
LOCKFILES = {"package-lock.json", "npm-shrinkwrap.json", "bun.lock", "bun.lockb"}
LAUNCHERS = ("npx", "bunx", "uvx", "pipx", "uv", "pnpm", "yarn")
SHELL_INTERP = {"sh", "bash", "zsh"}
COMPONENT_KEYS = {"commands", "agents", "skills", "hooks", "mcpServers", "outputStyles", "lspServers"}
SECRET_RE = re.compile(
    r"(sk-ant-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk_live_[A-Za-z0-9]{20,})")
HIDDEN_RE = re.compile("[​‌‍⁠﻿‪-‮⁦-⁩]")
B64_RE = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")
KIB, MIB = 1024, 1024 * 1024


class Report:
    def __init__(self, root):
        self.root, self.rows = root, []

    def add(self, level, title, path, detail=""):
        rel = os.path.relpath(path, self.root) if os.path.isabs(path) else path
        self.rows.append((level, title, rel, detail))


def read_text(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None
    if b"\0" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def load_json(path, r, title):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        r.add("BLOCK", title, path, str(e))
        return None


def front_matter(text):
    """Return (fields, error). Minimal YAML subset: top-level `key: value` scalars."""
    if not text.startswith("---"):
        return None, None
    lines = text.splitlines()
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, "front matter has no closing ---"
    fields, key = {}, None
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line[: len(line) - len(line.lstrip())]:
            return fields, "tab used for indentation"
        m = re.match(r"^([A-Za-z0-9_-]+):(?:\s+(.*)|\s*)$", line)
        if m:
            key, val = m.group(1), (m.group(2) or "").strip()
            if val and val[0] not in "\"'|>" and ": " in val:
                return fields, f"unquoted ': ' in `{key}` (quote the value)"
            if val and val[0] in "@`%":
                return fields, f"`{key}` starts with reserved character {val[0]!r}"
            if val[:1] in "\"'":
                val = val.strip("\"'")
            fields[key] = val
        elif line.startswith((" ", "-")) and key:
            if line.lstrip().startswith("- ") and fields.get(key) == "":
                fields[key] = ["list"]
            elif isinstance(fields[key], str):
                fields[key] = (fields[key] + " " + line.strip()).strip()
        else:
            return fields, f"line does not parse: {line.strip()[:60]}"
    return fields, None


def check_name_value(r, value, path, label):
    if not value:
        return
    if any(ord(c) > 127 for c in value):
        r.add("BLOCK", "Non-ASCII identifier", path, f"{label}={value!r}")
    elif value in RESERVED:
        r.add("BLOCK", "Reserved name", path, f"{label}={value!r} is reserved: {sorted(RESERVED)}")
    elif label == "name" and (value.startswith(RESERVED_PREFIXES) or value in RESERVED_EXACT
                              or ("official" in value.split("-") and {"claude", "anthropic"} & set(value.split("-")))):
        # from `claude plugin validate`: names that pass as Anthropic's own are an error
        r.add("BLOCK", "Name is reserved for Anthropic", path,
              f"{value!r}: cannot start with {', '.join(RESERVED_PREFIXES)}; name it for what it does")
        return
    elif not NAME_RE.match(value):
        r.add("WARN", "Name breaks the pattern", path, f"{label}={value!r}: lowercase, digits, hyphens, <=64, alnum at both ends")
    parts = value.split("-")
    if label == "name" and value not in RESERVED:
        if all(p in RESERVED for p in parts):
            r.add("HOLD", "Name may be confused with an existing listing", path, f"{value!r} is generic, like `test-plugin`")
        elif {"claude", "anthropic"} & set(parts):
            r.add("HOLD", "Name matches a known brand", path,
                  f"{value!r} contains claude/anthropic; a reviewer will likely hold it (inferred from the brand rule)")


def check_command(r, cmd, args, path, where):
    """Hook / MCP command rules: plain file under ${CLAUDE_PLUGIN_ROOT}, no shell tricks."""
    full = " ".join([cmd] + [str(a) for a in (args or [])])
    if "$(" in full or "`" in full or re.search(r"[*?]", full):
        r.add("BLOCK", "Command path can't be followed", path, f"{where}: command substitution or wildcard: {full[:80]}")
        return
    other_vars = [v for v in re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)", full)
                  if v not in ("CLAUDE_PLUGIN_ROOT",) and not v.startswith("user_config")]
    if other_vars:
        r.add("BLOCK", "Command path can't be followed", path, f"{where}: uses ${other_vars[0]}; write paths from ${{CLAUDE_PLUGIN_ROOT}}")
    tokens = [t.strip("\"'") for t in full.split()]
    if not tokens:
        return
    exe = os.path.basename(tokens[0])
    if re.search(r"(^|\s)-c(\s|$)|(^|\s)-e(\s|$)", full) and exe in ("python", "python3", "node", "bash", "sh", "ruby", "perl"):
        r.add("BLOCK", "Command path can't be followed", path, f"{where}: inline program ({exe} -c/-e)")
        return
    if ".." in full.replace("${CLAUDE_PLUGIN_ROOT}", ""):
        r.add("BLOCK", "Command reaches above the plugin folder", path, f"{where}: {full[:80]}")
    if exe in LAUNCHERS:
        check_launcher(r, tokens, path, where)
    elif exe in ("npm",) and "run" in tokens:
        r.add("HOLD", "MCP server command wasn't read", path, f"{where}: started through `npm run`")
    elif exe not in SHELL_INTERP and any(t.startswith("${CLAUDE_PLUGIN_ROOT}") for t in tokens[1:]):
        r.add("HOLD", "Scripts the validator couldn't follow", path,
              f"{where}: runs a non-shell file via {exe}; only plain shell scripts are followed (always held)")
    elif exe in SHELL_INTERP or tokens[0].endswith(".sh"):
        script = next((t for t in tokens if t.endswith(".sh")), None)
        if script and script.startswith("${CLAUDE_PLUGIN_ROOT}"):
            check_shell_script(r, os.path.join(r.root, script.replace("${CLAUDE_PLUGIN_ROOT}/", "")), where)


def check_launcher(r, tokens, path, where):
    exe = os.path.basename(tokens[0])
    pkgs = [t for t in tokens[1:] if not t.startswith("-") and t not in ("run", "dlx", "x")]
    pkg = pkgs[0] if pkgs else ""
    if exe == "uv":
        if "--locked" not in tokens and "--frozen" not in tokens:
            r.add("BLOCK", "Unpinned uv run", path, f"{where}: add --locked or --frozen")
        return
    pinned = (re.search(r"@\d+\.\d+\.\d+$", pkg) is not None) if exe != "uvx" and exe != "pipx" \
        else re.search(r"==\d+\.\d+\.\d+$", pkg) is not None
    if not pinned:
        r.add("BLOCK", f"Unpinned {exe} launcher", path, f"{where}: pin exactly, e.g. pkg@1.2.3 / pkg==1.2.3 (got {pkg!r})")
    else:
        r.add("HOLD", f"Runs a pinned {exe} package", path, f"{where}: {pkg} (always held for a reviewer)")


def check_shell_script(r, script, where):
    text = read_text(script)
    if text is None:
        return
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("#") or not s:
            continue
        if "$(" in s or "`" in s or re.search(r"\b(npx|uvx|bunx|pip install|npm install)\b", s) \
                or re.search(r"\$\{?(?!CLAUDE_PLUGIN_ROOT)[A-Za-z_]", s):
            r.add("HOLD", "Scripts the validator couldn't follow", script, f"line {i} ({where}): {s[:70]}")
            return


def check_icon(r, root, m):
    """Rule from `claude plugin validate`: square PNG/JPEG, 512-2048 px, under 2 MB; no SVG/WebP."""
    cands = [m["icon"]] if isinstance(m.get("icon"), str) else \
        [".claude-plugin/icon.png", ".claude-plugin/icon.svg", "assets/icon.png", "assets/icon.svg", "icon.png"]
    path = next((os.path.join(root, c) for c in cands if os.path.isfile(os.path.join(root, c))), None)
    if not path:
        r.add("WARN", "No icon", root, "add a square PNG at .claude-plugin/icon.png, 512-2048 px, <2 MB (set once, on first save)")
        return
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg"):
        r.add("WARN", "Icon format not accepted", path, "PNG or JPEG only; SVG and WebP are not accepted")
        return
    if os.path.getsize(path) >= 2 * MIB:
        r.add("WARN", "Icon over 2 MB", path)
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", head[16:24])
        if w != h or not 512 <= w <= 2048:
            r.add("WARN", "Icon size", path, f"{w}x{h}; needs square, 512-2048 px")


def check_manifest(r, root):
    mpath = os.path.join(root, ".claude-plugin", "plugin.json")
    if not os.path.isfile(mpath):
        r.add("BLOCK", "No plugin.json", root, "needs .claude-plugin/plugin.json")
        return {}
    m = load_json(mpath, r, "plugin.json can't be parsed")
    if not isinstance(m, dict):
        return {}
    if "name" not in m:
        r.add("BLOCK", "plugin.json has no name", mpath)
    check_name_value(r, m.get("name", ""), mpath, "name")
    for label in ("displayName",):
        if label in m and (any(ord(c) > 127 for c in m[label]) or HIDDEN_RE.search(m[label])):
            r.add("BLOCK", "Mixed scripts or invisible characters", mpath, label)
    author = m.get("author") or {}
    aname = author.get("name", "") if isinstance(author, dict) else str(author)
    if HIDDEN_RE.search(aname):
        r.add("BLOCK", "Mixed scripts or invisible characters", mpath, "author.name")
    for field in ("description", "author", "version"):
        if not m.get(field):
            r.add("WARN", f"`{field}` missing", mpath)
    if m.get("version") and not re.match(r"^\d+\.\d+\.\d+", str(m["version"])):
        r.add("NOTE", "Version is not semver", mpath, f"{m['version']!r}; raise it with every release")
    exp = m.get("experimental") if isinstance(m.get("experimental"), dict) else {}
    for k in exp:
        if k in COMPONENT_KEYS:
            r.add("BLOCK", "Component key inside `experimental`", mpath, k)
    for k in m:
        if k not in COMPONENT_KEYS and k.lower() in {c.lower() for c in COMPONENT_KEYS} | {"hook", "mcpserver", "mcp_servers", "mcp-servers"}:
            r.add("BLOCK", "Misspelled component key", mpath, k)
    for k in COMPONENT_KEYS:
        vals = m.get(k)
        vals = vals if isinstance(vals, list) else [vals] if isinstance(vals, str) else []
        for v in vals:
            if ".." in v.split("/") or os.path.isabs(v):
                r.add("BLOCK", "Path climbs out of the plugin", mpath, f"{k}: {v}")
            if k == "hooks" and os.path.normpath(v) in ("hooks/hooks.json",):
                r.add("WARN", "hooks/hooks.json listed in plugin.json", mpath, "Claude Code loads it automatically; remove")
    if isinstance(m.get("mcpServers"), dict):
        check_mcp(r, {"mcpServers": m["mcpServers"]}, mpath)
    check_icon(r, root, m)
    if "lspServers" in m or "outputStyles" in m or "settings" in m:
        r.add("NOTE", "Claude Code only", mpath, "LSP servers, output styles and settings are ignored in Chat and Cowork")
    return m


def check_readme_license(r, root, manifest):
    readme = next((os.path.join(root, n) for n in ("README.md", "README", "README.txt", "readme.md") if os.path.isfile(os.path.join(root, n))), None)
    if not readme:
        r.add("BLOCK", "README missing", root, "add README.md in the plugin folder (it becomes the listing description)")
    else:
        text = read_text(readme) or ""
        prose = re.sub(r"```.*?```", " ", text, flags=re.S)
        words = len(re.findall(r"[A-Za-z0-9][\w'-]*", prose))
        if words < 40:
            r.add("BLOCK", "README too short", readme, f"{words} words outside code blocks; need 40+")
        if not re.search(r"privacy", text, re.I) and manifest.get("_sends_data"):
            r.add("WARN", "No privacy policy link", readme, "policy 3.A: needed when the plugin collects data or connects to a remote service")
    if not any(os.path.isfile(os.path.join(root, n)) for n in ("LICENSE", "LICENSE.md", "LICENSE.txt")) and not manifest.get("license"):
        r.add("BLOCK", "License missing", root, "add LICENSE or `license` in plugin.json")


def check_mcp(r, data, path):
    servers = data.get("mcpServers", data) if isinstance(data, dict) else None
    if not isinstance(servers, dict):
        r.add("BLOCK", ".mcp.json can't be parsed", path, "expected an object of servers")
        return
    for name, s in servers.items():
        if not isinstance(s, dict):
            r.add("BLOCK", ".mcp.json can't be parsed", path, f"{name}: not an object")
            continue
        where = f"mcp:{name}"
        for hk, hv in (s.get("headers") or {}).items():
            if isinstance(hv, str) and "${user_config" not in hv and (SECRET_RE.search(hv) or re.match(r"(?i)bearer\s+[A-Za-z0-9._-]{16,}", hv)):
                r.add("BLOCK", "Secret in MCP headers", path, f"{where}: {hk}")
        if "url" in s:
            url, typ = s.get("url", ""), s.get("type")
            if typ not in ("http", "sse", "ws"):
                r.add("BLOCK", "Remote MCP server type", path, f"{where}: type must be http, sse or ws (got {typ!r})")
            if url and not (url.startswith(("https://", "wss://")) or url.startswith("${user_config.")):
                r.add("BLOCK", "MCP server URL is not https", path, f"{where}: {url}")
            if "${user_config" in url:
                r.add("NOTE", "MCP URL uses user_config", path, f"{where}: ignored in Chat; ignored in Cowork without a default")
            if typ == "sse":
                r.add("NOTE", "SSE transport", path, f"{where}: allowed now, will be deprecated; prefer Streamable HTTP")
        elif "command" in s:
            cmd = s["command"]
            if str(cmd).endswith((".mcpb", ".dxt")) or any(str(a).endswith((".mcpb", ".dxt")) for a in s.get("args", [])):
                level = "BLOCK" if re.search(r"https?://", " ".join(map(str, s.get("args", [])))) else "HOLD"
                r.add(level, "Bundled MCP server not inspected", path, where)
            check_command(r, str(cmd), s.get("args"), path, where)
            r.add("NOTE", "Local MCP server", path, f"{where}: ignored in Chat; loads in Cowork only when running on the user's computer")
        for v in json.dumps(s.get("env", {})).split('"'):
            if SECRET_RE.search(v):
                r.add("BLOCK", "Real credential in MCP env", path, f"{where}: use userConfig with sensitive: true")


def check_hooks(r, root):
    path = os.path.join(root, "hooks", "hooks.json")
    if not os.path.isfile(path):
        return False
    data = load_json(path, r, "hooks.json is invalid")
    if not isinstance(data, dict):
        return True
    if "hooks" not in data and "modules" not in data:
        r.add("BLOCK", "hooks.json is invalid", path, "needs a top-level `hooks` object or `modules` array")
    for event, groups in (data.get("hooks") or {}).items():
        for g in groups if isinstance(groups, list) else []:
            for h in g.get("hooks", []) if isinstance(g, dict) else []:
                where = f"hook:{event}"
                if h.get("type") == "http":
                    if not str(h.get("url", "")).startswith("https://"):
                        r.add("BLOCK", "HTTP hook needs https", path, where)
                    if re.search(r"\$\{?[A-Z_]*(TOKEN|KEY|SECRET)", json.dumps(h)):
                        r.add("BLOCK", "HTTP hook sends a local credential", path, where)
                elif h.get("type") == "command":
                    check_command(r, h.get("command", ""), None, path, where)
    r.add("NOTE", "Hooks", path, "ignored in Chat; load in Cowork and Claude Code")
    return True


def check_markdown_component(r, path, kind, folder_name=None):
    text = read_text(path)
    if text is None:
        return
    fields, err = front_matter(text)
    if err:
        r.add("BLOCK", "Front matter doesn't parse", path, err)
    if fields is None:
        r.add("WARN", "No front matter", path, f"{kind} needs --- name/description ---")
        fields = {}
    desc = fields.get("description")
    if isinstance(desc, list):
        r.add("BLOCK", "description is not a single text value", path)
    elif not desc:
        r.add("WARN", "No description", path)
    elif kind == "skill":
        if len(desc) > 1024:
            r.add("WARN", "Description over 1024 chars", path, f"{len(desc)} chars (spec)")
        if re.search(r"<[a-zA-Z/][^>]*>", desc):
            r.add("WARN", "XML tag in description", path, "spec forbids XML tags")
        if not re.search(r"(?i)\b(use|when|for|if)\b", desc):
            r.add("WARN", "Description doesn't say when to use it", path, "policy 2.A: say what it does and when to invoke")
    name = fields.get("name")
    if kind == "skill":
        if name and isinstance(name, str):
            check_name_value(r, name, path, "skill name")
            if folder_name and name != folder_name:
                r.add("WARN", "Skill name differs from its folder", path, f"name={name!r}, folder={folder_name!r} (spec)")
        lines = text.count("\n")
        if lines > 500:
            r.add("WARN", "SKILL.md over 500 lines", path, f"{lines} lines; move detail to reference files (spec)")
    for i, line in enumerate(text.splitlines(), 1):
        if re.match(r"^\s*!`", line):
            r.add("HOLD", "Unreadable program", path, f"line {i}: !`...` runs a command when loaded")
    if HIDDEN_RE.search(text):
        r.add("HOLD", "Hidden characters in instructions", path, "zero-width or bidi characters (policy 2.G)")
    if B64_RE.search(text):
        r.add("HOLD", "Encoded blob in instructions", path, "long base64-like run (policy 2.G)")
    for i, line in enumerate(text.splitlines(), 1):
        # shortcut: a negation on the line is taken as a rule against it, not an instruction; misses split sentences
        if re.search(r"(?i)(fetch|download|curl|retrieve)[^\n]{0,60}(instructions|prompt)[^\n]{0,40}(follow|execute|obey)", line) \
                and not NEGATION_RE.search(line):
            r.add("HOLD", "Pulls instructions from an external source", path, f"line {i}: policy 2.F")
            break


def walk(r, root):
    files, names_by_dir = [], {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for n in dirnames + filenames:
            p = os.path.join(dirpath, n)
            names_by_dir.setdefault(dirpath, []).append(n)
            base = os.path.splitext(n)[0].lower()
            if n in JUNK:
                r.add("BLOCK", "OS junk file", p)
            if ":" in n or n.endswith((".", " ")) or base in WIN_DEVICES:
                r.add("BLOCK", "Couldn't validate that repository", p, "name invalid on Windows or macOS")
            if os.path.islink(p):
                r.add("BLOCK", "Symbolic link", p, "Block where loaded, Warning elsewhere")
        for n in filenames:
            files.append(os.path.join(dirpath, n))
        if os.path.isfile(os.path.join(dirpath, ".git")) and dirpath != root:
            r.add("BLOCK", "Git submodule", dirpath)
    for d, names in names_by_dir.items():
        lowered = [n.lower() for n in names]
        for n in names:
            if lowered.count(n.lower()) > 1:
                r.add("BLOCK", "Couldn't validate that repository", os.path.join(d, n), "names differ only by case")
                break
    if len(files) > 512:
        r.add("HOLD", "More than 512 files", root, str(len(files)))
    total = 0
    for p in files:
        if os.path.islink(p):
            continue
        size, ext, n = os.path.getsize(p), os.path.splitext(p)[1].lower(), os.path.basename(p)
        total += size
        if size > 5 * MIB:
            r.add("BLOCK", "Repository too large to validate", p, f"{size // MIB} MiB > 5 MiB per file")
        text = None if ext in MEDIA_EXT else read_text(p)
        if ext not in MEDIA_EXT and text is None:
            r.add("HOLD", "Files or downloads the validator couldn't inspect", p, "binary that isn't an image or font")
        elif ext not in MEDIA_EXT and size > 256 * KIB:
            r.add("HOLD", "Large file", p, f"{size // KIB} KiB > 256 KiB")
        if text and SECRET_RE.search(text):
            r.add("BLOCK", "Real credential in a file", p, "use userConfig with sensitive: true and ${user_config.KEY}")
        if text and text.startswith("version https://git-lfs"):
            r.add("BLOCK", "Git LFS pointer file", p)
        if n in REGISTRY_CFG:
            r.add("HOLD", "Install may use a custom registry or package source", p, "Blocks when a launcher is also used")
        if n == ".gitattributes" and text and re.search(r"export-ignore|export-subst|\bfilter=", text):
            r.add("BLOCK", "Couldn't validate that repository", p, "export-ignore/export-subst/filter in .gitattributes")
        if text and ext in (".js", ".mjs", ".cjs") and max((len(l) for l in text.splitlines()), default=0) > 1000:
            r.add("HOLD", "Minified or packed code", p, "commit readable source")
    if os.path.isfile(os.path.join(root, "package.json")) and any(os.path.isfile(os.path.join(root, l)) for l in LOCKFILES):
        r.add("HOLD", "Dependencies install from a lockfile", root)
    if os.path.isdir(os.path.join(root, "bin")):
        r.add("WARN", "Top-level bin/", os.path.join(root, "bin"), "Chat and Cowork refuse the whole plugin; Claude Code only")
    if total > 256 * MIB:
        r.add("BLOCK", "Repository too large to validate", root, f"{total // MIB} MiB unpacked")


def check_ancestor_gitattributes(r, root):
    d = os.path.dirname(os.path.abspath(root))
    while True:
        ga = os.path.join(d, ".gitattributes")
        text = read_text(ga) if os.path.isfile(ga) else None
        if text and re.search(r"export-ignore|export-subst|\bfilter=", text):
            r.add("BLOCK", "Couldn't validate that repository", ga, "export-ignore/export-subst/filter above the plugin")
        if os.path.exists(os.path.join(d, ".git")) or os.path.dirname(d) == d:
            return
        d = os.path.dirname(d)


def check_plugin(root):
    root = os.path.abspath(root)
    r = Report(root)
    manifest = check_manifest(r, root)
    walk(r, root)
    check_ancestor_gitattributes(r, root)
    mcp_path = os.path.join(root, ".mcp.json")
    if os.path.isfile(mcp_path):
        data = load_json(mcp_path, r, ".mcp.json can't be parsed")
        if data is not None:
            check_mcp(r, data, mcp_path)
    check_hooks(r, root)
    for sub in sorted(os.listdir(root)):
        if sub.lower() in ("skills", "commands", "agents", "hooks") and sub != sub.lower():
            r.add("BLOCK", "Component folder capitalization", os.path.join(root, sub), f"must be `{sub.lower()}/`")
    skills = os.path.join(root, "skills")
    if os.path.isdir(skills):
        for s in sorted(os.listdir(skills)):
            d = os.path.join(skills, s)
            if not os.path.isdir(d):
                continue
            if os.path.isfile(os.path.join(d, "SKILL.md")):
                check_markdown_component(r, os.path.join(d, "SKILL.md"), "skill", s)
            elif any(n.lower() == "skill.md" for n in os.listdir(d)):
                r.add("BLOCK", "SKILL.md capitalization", d, "file must be named SKILL.md")
            else:
                r.add("WARN", "Skill folder without SKILL.md", d)
    for kind in ("commands", "agents"):
        d = os.path.join(root, kind)
        if os.path.isdir(d):
            for n in sorted(os.listdir(d)):
                if n.endswith(".md"):
                    check_markdown_component(r, os.path.join(d, n), kind[:-1])
            if kind == "agents":
                r.add("NOTE", "Agents", d, "ignored in Chat; load in Cowork and Claude Code")
    hooks_text = read_text(os.path.join(root, "hooks", "hooks.json")) or ""
    manifest["_sends_data"] = os.path.isfile(mcp_path) or "mcpServers" in manifest \
        or re.search(r'"type"\s*:\s*"http"', hooks_text) is not None
    check_readme_license(r, root, manifest)
    return r


def plugin_roots(path):
    path = os.path.abspath(path)
    if os.path.isfile(os.path.join(path, ".claude-plugin", "plugin.json")):
        return [path]
    mk = os.path.join(path, ".claude-plugin", "marketplace.json")
    if os.path.isfile(mk):
        with open(mk, encoding="utf-8") as f:
            data = json.load(f)
        out = []
        for p in data.get("plugins", []):
            src = p.get("source")
            if isinstance(src, str) and src.startswith("./"):
                out.append(os.path.normpath(os.path.join(path, src)))
        return out
    return [path]


ORDER = {"BLOCK": 0, "HOLD": 1, "WARN": 2, "NOTE": 3}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    blocked = False
    for arg in argv:
        for root in plugin_roots(arg):
            r = check_plugin(root)
            counts = {k: sum(1 for x in r.rows if x[0] == k) for k in ORDER}
            verdict = "NOT READY" if counts["BLOCK"] else "HELD FOR REVIEW" if counts["HOLD"] else "READY"
            print(f"## {os.path.basename(root)}: {verdict}  "
                  + "  ".join(f"{k}={v}" for k, v in counts.items()))
            for level, title, rel, detail in sorted(set(r.rows), key=lambda x: (ORDER[x[0]], x[2], x[1])):
                print(f"{level:5}  {title}  [{rel}]" + (f"  {detail}" if detail else ""))
            print()
            blocked |= counts["BLOCK"] > 0
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
