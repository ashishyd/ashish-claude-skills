---
name: "dependency-versions"
description: "Use when adding, upgrading, pinning or removing a package or library; when an install fails on a version conflict or peer-dependency error; or when asked to bump, audit or clean up dependencies."
---

# Dependency Versions

A version change is a code change you did not write. Treat it like one: decide the range on purpose, change one thing at a time, and show a check that passes after.

## Before you touch anything

1. Find the manager and the lockfile (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `uv.lock`, `poetry.lock`, `Cargo.lock`, `go.sum`). Use that manager. Never mix two in one repo.
2. Run the project's check on the untouched tree and keep the result. Without a green baseline you cannot tell what the upgrade broke.
3. Read the repo's instruction file for rules on pinning, allowed licences and registries.

## Choose the range

| Situation | Range |
|---|---|
| Application | Lockfile committed; manifest uses compatible ranges (`^1.4.0`, `~=1.4`). The lockfile is what ships. |
| Library others install | Widest range you have tested. No upper cap unless a known break exists; say which one. |
| Tool that breaks across minors (build tools, compilers, linters, codegen) | Exact pin. |
| Security fix in a transitive dependency | Override or resolution entry with a comment naming the advisory and when to remove it. |
| `latest`, `*`, or a git branch | Never. |

## One change at a time

1. Change one package, or one tightly linked group (a framework and its plugins). Do not mix upgrades with feature work.
2. Read the changelog between the old and the new version. List breaking changes that touch code in this repo (grep for the APIs named).
3. Install with the manager's own command so the lockfile updates. Do not hand-edit a lockfile.
4. Run the baseline check again. Add the command and its output to the report.
5. Major bump: also build, and run the app or an end-to-end path that uses the package.

## Conflicts

- Read the full resolver message. Name the two packages that disagree and the range each demands.
- Order of fixes: upgrade the older package, then allow the newer one through the range, then override with a comment. Never delete the lockfile and reinstall to "make it go away"; that changes every version at once.
- Peer-dependency flags (`--force`, `--legacy-peer-deps`, `--no-deps`) are a last resort. Tell the user which conflict you overrode and why it is safe.
- Two copies of one package in the tree (`npm ls <pkg>`, `pnpm why <pkg>`, `uv pip tree`, `cargo tree -d`) is a bug for anything holding state or identity: React, ORMs, schema libraries.

## Audit and clean up

- Outdated: `npm outdated`, `pnpm outdated`, `uv pip list --outdated`, `cargo outdated`, `go list -u -m all`.
- Vulnerabilities: `npm audit`, `pip-audit`, `cargo audit`, `govulncheck`. Report severity and whether the vulnerable code path is reachable here.
- Unused: `knip` or `depcheck` (JS), `deptry` (Python). Confirm by grep before removing; dynamic imports and config files hide uses.
- Bulk "update everything" is not one change. Group by risk: patch and minor first, each major on its own.

## Stop and tell the user when

- A package must move more than one major version, or its changelog lists a data or config migration.
- The only fix is an override, a fork, or a version with a different licence.
- The same install or resolve error persists after two attempts.
- The change needs a private registry, a token, or a paid service.
- A new package is unmaintained (no release in two years) or has one maintainer, and the task could be done in a few lines.

## Report

```markdown
**Changed:** <package: old -> new, range chosen and why>
**Breaking changes checked:** <list, or "none in changelog">
**Evidence:** `<command>` -> <result>
**Not verified:** <what was not run>
**You need to:** <commit lockfile, rebuild image, redeploy; or "nothing">
```

Related: when an upgrade or a new package introduces an import loop, use the `dependency-cycles` skill.
