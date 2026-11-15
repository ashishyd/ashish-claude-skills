#!/usr/bin/env python3
"""UserPromptSubmit hook: suggest a Claude model and effort level for this prompt.

Reads the hook JSON on stdin. Classifies the prompt with cheap keyword rules,
reads the current model and effort from the end of the session transcript (the
hook input carries neither), and prints a one-line additionalContext only when
the current setting does not fit and the suggestion differs from the last one in
this session. Suggests only; never switches. Never blocks or fails.
"""
import json
import os
import re
import sys
import tempfile

MODELS = {  # tier -> (family, display, id, effort)
    "haiku": ("haiku", "Haiku 5.5", "claude-haiku-5-5", "low"),
    "sonnet": ("sonnet", "Sonnet 5.5", "claude-sonnet-5-5", "medium"),
    "opus": ("opus", "Opus 5.5", "claude-opus-5-5", "high"),
}
OPUS = re.compile(
    r"architect|system design|design (the|a|an) (system|service|schema|api)|trade-?offs?"
    r"|security|vulnerab|threat model|\bauth[nz]?\b|authori[sz]|authenticat|crypto"
    r"|race condition|deadlock|memory leak|flaky|intermittent|heisenbug|root cause"
    r"|segfault|corrupt|production (bug|issue|incident)|\bincident\b|regression"
    r"|why (does|is|did|do) .{0,60}(fail|crash|hang|break|leak|slow)"
    r"|large refactor|refactor (the )?(whole|entire|all|every|across)|rewrite"
    r"|migrat(e|ion)|concurrency|distributed|scal(e|ing|ability)", re.I)
CODE = re.compile(
    r"\b(add|implement|fix|write|update|change|create|build|refactor|test|rename|edit"
    r"|move|delete|remove|bump|wire|hook up|convert|port|replace)\b"
    r"|```|\.(py|ts|tsx|js|go|rs|java|rb|sql|css)\b", re.I)
QUESTION = re.compile(
    r"^(what|which|where|when|who|how (do|does|can|to)|is|are|does|do|can|should"
    r"|define|explain|list|show)\b", re.I)
ACK = re.compile(r"^((y(es|ep)?|no|ok(ay)?|sure|go( ahead)?|continue|thanks?( you)?"
                 r"|do it|lgtm|done|next|please)[.,! ]*)+$", re.I)
TAIL_BYTES = 256 * 1024


def classify(prompt):
    """Return (tier, reason) or (None, "") when the prompt says too little."""
    p = prompt.strip()
    if not p or p.startswith("/") or ACK.match(p) or len(p.split()) < 3:
        return None, ""
    if OPUS.search(p):
        return "opus", "architecture, security, hard debugging or a large refactor"
    if CODE.search(p) or len(p) > 1500:
        return "sonnet", "a routine code change"
    if QUESTION.match(p) and len(p) <= 200:
        return "haiku", "a quick question or lookup"
    return "sonnet", "general work"


def current_setting(data):
    """(model_id, effort) from the hook input if present, else the transcript tail."""
    model, effort = data.get("model"), data.get("effort")
    if isinstance(model, dict):
        model = model.get("id")
    path = data.get("transcript_path") or ""
    if (not model or not effort) and os.path.isfile(path):
        try:
            with open(path, "rb") as f:
                f.seek(max(0, os.path.getsize(path) - TAIL_BYTES))
                tail = f.read().decode("utf-8", "replace")
            models = re.findall(r'"model"\s*:\s*"(claude-[\w.-]+)"', tail)
            efforts = re.findall(r'"effort"\s*:\s*"(\w+)"', tail)
            model = model or (models[-1] if models else None)
            effort = effort or (efforts[-1] if efforts else None)
        except OSError:
            pass
    return model, effort


def fits(tier, model, effort):
    family, _, _, want = MODELS[tier]
    return bool(model) and family in model and effort in (None, want)


def hint(tier, reason, model, effort):
    family, name, mid, eff = MODELS[tier]
    now = " You are on %s%s." % (model, ", effort " + effort if effort else "") if model else ""
    why = "a better result" if tier == "opus" else "fewer tokens"
    switch = "`/effort %s`" % eff
    if not (model and family in model):
        switch = "`/model %s` and %s, or the model picker" % (family, switch)
    return ("switchboard: this looks like %s; %s (`%s`) at effort %s fits for %s.%s "
            "To switch: %s. Suggestion only; mention it to the user in one line "
            "and carry on." % (reason, name, mid, eff, why, now, switch))


def main():
    data = json.load(sys.stdin)
    tier, reason = classify(str(data.get("prompt", "")))
    if not tier:
        return
    model, effort = current_setting(data)
    if fits(tier, model, effort):
        return
    session = re.sub(r"\W", "", str(data.get("session_id", "")))
    state = os.path.join(tempfile.gettempdir(), "switchboard-" + session)
    try:
        with open(state) as f:
            if f.read().strip() == tier:
                return  # same advice as last prompt: do not nag
    except OSError:
        pass
    with open(state, "w") as f:
        f.write(tier)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": hint(tier, reason, model, effort)}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hint hook must never fail or block a prompt
        pass
