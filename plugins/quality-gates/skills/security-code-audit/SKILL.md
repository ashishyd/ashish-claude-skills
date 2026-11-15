---
name: security-code-audit
description: Use when code touching auth, sessions, tokens, permissions, user input, database queries, file uploads, webhooks, payments, secrets or a new API route has just been written or changed, or when the user asks for a security review of a diff, a file or a feature.
---

# Security Code Audit

Audit the change, not the whole repository. Follow each piece of untrusted input from where it enters to where it is used. A finding needs a concrete attacker, action and gain; without one it is hardening advice.

For a whole-codebase audit or pen test, use a full audit skill (`security-audit`) if one is installed.

## Steps

1. **Scope.** The diff (`git diff` plus staged) or the files named, and the code they call.
2. **Map.** List each entry point touched (route, action, job, webhook, CLI) with who can call it and what they control.
3. **Trace.** Follow every controlled value to its sinks: query, shell, filesystem, HTML, redirect, outbound request, log, model prompt.
4. **Check** against the table.
5. **Tools.** Run what the repo already has (`npm audit`, `pnpm audit`, `pip-audit`, semgrep, gitleaks). Do not install tools.
6. **Report.**

## Checklist

| Area | Ask |
|---|---|
| Authorisation | Does every query filter by the caller's own id or tenant? Can changing an id in the request reach another user's row? Is the check on the server, on every route, including the new one? |
| Authentication | Is the token verified (signature, algorithm, expiry, audience)? Session fixed on login, cleared on logout? Reset and invite tokens single-use and expiring? |
| Injection | Any query, shell command, path, template or regex built by joining strings with input? Object merge that allows `__proto__`? |
| Input | Schema validation at the boundary, with size limits? Does the handler accept fields the user must not set (role, owner id, price)? |
| Output | Raw HTML (`dangerouslySetInnerHTML`, `v-html`, `innerHTML`)? `href` or redirect target taken from input? |
| Server-side requests | Does the server fetch a URL the user supplies? Are internal addresses blocked? |
| Secrets | Hard-coded, logged, returned in an error, or shipped to the browser (`NEXT_PUBLIC_`, `VITE_`)? |
| Crypto | `Math.random` for tokens? Fast hash for passwords? `===` on secrets instead of a constant-time compare? Home-made schemes? |
| Browser | Cookie flags (`HttpOnly`, `Secure`, `SameSite`)? CSRF on state-changing cookie-auth routes? CORS reflecting any origin with credentials? |
| Files | Upload type, size and name checked on the server? Stored outside the web root? Path built from input? |
| Webhooks | Signature verified on the raw body? Replay window? |
| Abuse | Rate limit on login, reset, signup and costly endpoints? |
| Database | Row-level security on tables exposed to clients? Service-role key used where a user key should be? |
| Dependencies | New package: known advisories, a look-alike name, an install script? |
| AI features | Can untrusted text reach a model that holds tools or secrets? Is model output used as HTML, SQL or a command? |

## Severity

- **Critical:** unauthenticated access to data or code execution.
- **High:** an authenticated user reaches another user's data or raises their privilege.
- **Medium:** needs an unlikely precondition, or limited impact.
- **Low:** weak defence in depth.

## Every finding

```
<file>:<line> [SEVERITY] <weakness>
Path: <entry point> -> <sink>
Exploit: <who> does <what> and gains <what>
Fix: <the change, at most 10 lines>
```

## Output

```markdown
## Verdict: PASS | FIX BEFORE MERGE | BLOCK
Scope: <files and entry points reviewed>
Tools: `<command>` -> <result>

### Findings
### Hardening (no exploit shown)
### Not checked
```

## Rules

- Read-only unless asked to fix. Never open `.env` or key files; never test against a live system.
- Read the code at each line cited. No finding from memory or from a pattern match alone.
- Findings only: no praise and no summary of what the code does.
- When nothing is wrong, write "No findings" and list what was traced.
