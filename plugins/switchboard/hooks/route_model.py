#!/usr/bin/env python3
"""UserPromptSubmit hook: route this prompt to the Claude model and effort that fit it.

Reads the hook JSON on stdin. Classifies the prompt with cheap keyword rules,
reads the current model and effort from the end of the session transcript (the
hook input carries neither), and when the current setting does not fit, prints a
short additionalContext telling the main agent to run the prompt in an Agent
subagent with the chosen model and effort. A hook cannot spawn the subagent
itself, so the main agent does. Never blocks or fails.
"""
import json
import os
import re
import sys

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
RANK = {"haiku": 0, "sonnet": 1, "opus": 2, "fable": 3}
EFFORTS = ["low", "medium", "high", "xhigh", "max"]
CODE_REASON = "a routine code change"


def classify(prompt):
    """Return (tier, reason) or (None, "") when the prompt says too little."""
    p = prompt.strip()
    if not p or p.startswith("/") or ACK.match(p) or len(p.split()) < 3:
        return None, ""
    if OPUS.search(p):
        return "opus", "architecture, security, hard debugging or a large refactor"
    if CODE.search(p) or len(p) > 1500:
        return "sonnet", CODE_REASON
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


def worth_routing(tier, reason, model, effort):
    """Route up always (quality); route down only when the saving beats a cold subagent."""
    if not model:
        return tier != "haiku"  # unknown setting: the hint tells the agent to skip if it fits
    have = next((RANK[f] for f in RANK if f in model), None)
    want = RANK[tier]
    if have is None or want > have:
        return True
    if want == have:  # same model: only an effort step-up is worth a spawn
        return effort in EFFORTS and EFFORTS.index(MODELS[tier][3]) > EFFORTS.index(effort)
    # shortcut: step-down guessed from the prompt type, not measured tokens; tune if spawns cost more
    return reason == CODE_REASON


def hint(tier, reason, model, effort):
    family, name, _, eff = MODELS[tier]
    now = " You are on %s%s." % (model, ", effort " + effort if effort else "") if model else ""
    why = "a better result" if tier == "opus" else "fewer tokens"
    return ("switchboard: this looks like %s; %s at effort %s fits for %s.%s "
            "Route it: call the Agent tool with model \"%s\", effort \"%s\", "
            "subagent_type \"general-purpose\" and a complete brief (this prompt plus "
            "the context from this conversation it needs; ask before commit, push, "
            "delete or deploy). Relay its result; do not redo the work. Skip routing if "
            "you are already on %s at effort %s, or the prompt only needs this "
            "conversation." % (reason, name, eff, why, now, family, eff, name, eff))


def main():
    data = json.load(sys.stdin)
    tier, reason = classify(str(data.get("prompt", "")))
    if not tier:
        return
    model, effort = current_setting(data)
    if fits(tier, model, effort) or not worth_routing(tier, reason, model, effort):
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": hint(tier, reason, model, effort)}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hint hook must never fail or block a prompt
        pass
