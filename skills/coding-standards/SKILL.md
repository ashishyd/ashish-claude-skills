---
name: "coding-standards"
description: "Use when writing or changing code in any programming language, when starting work in an unfamiliar language or framework, or when unsure which style, idiom or convention applies to a file."
---

# Coding Standards

The standard for a file is set by the repo first and the language second. Good code in the wrong house style is still a defect.

## Order of authority

When two sources disagree, the higher one wins:

1. The project's instruction file (CLAUDE.md, AGENTS.md) and enforced config: formatter, linter, compiler settings, `.editorconfig`.
2. The surrounding code in the same module.
3. The language's community standard (table below).
4. The universal rules below.

When the repo's convention conflicts with the language's best practice, follow the repo and say so once in your report.

## Before writing

1. Identify the language, framework and versions from the manifest and lockfile.
2. Read the formatter, linter and compiler config.
3. Read one neighbouring file that does something similar.
4. State the standard in one line, for example: "TypeScript strict, ESLint flat config, Prettier 100 columns, copying the pattern in `posts.service.ts`."

## Universal rules

**Names**
- A name says what the thing is. Put the unit in the name: `timeoutMs`, `priceCents`.
- Booleans start with `is`, `has`, `can` or `should`.
- Use only abbreviations the repo already uses.

**Functions**
- One job per function. Return early instead of nesting.
- More than three parameters become an options object or struct.
- A boolean parameter that switches behaviour becomes two functions.

**Errors**
- Never swallow an error. Catch only what you can handle at that point.
- Add context when rethrowing: what was being attempted, with which identifier.
- Validate at every boundary (HTTP, queue, file, environment) and trust the data inside.
- Use typed or structured errors. Never branch on an error message string.

**Types and data**
- Model states so that invalid combinations cannot be built.
- No untyped values (`any`, bare `dict`, `Object`) across a module boundary.
- Immutable by default. Return an empty collection, not null.

**Side effects**
- Keep I/O at the edges and pure logic in the middle.
- Do no work at import or module-load time.
- Wrap time, randomness and environment access so tests can control them.

**Concurrency and resources**
- Every async call is awaited, or deliberately detached with an error handler.
- Every network call has a timeout. Every retry is safe to repeat.
- Whatever is opened is closed by the language's scoped construct.

**Security**
- Parameterised queries only. No string-built SQL or shell commands.
- No secrets in code, logs, error messages or tests.
- Authorisation is checked on the server for every request.

**Dependencies**
- Use the standard library and existing dependencies first. A new dependency needs a stated reason.

**Tests**
- New logic gets a test at the lowest level that proves it.
- Test behaviour, not implementation. One reason to fail per test.
- No real network, clock or sleep in unit tests.

**Comments and logs**
- Comments explain why. Public APIs use the language's doc format.
- No commented-out code.
- Logs are structured, at the right level, and free of personal data.

**Diff discipline**
- Make the smallest complete change. Do not reformat or rename what you were not asked to touch.

## Language cards

| Language | Standard | Tools | Rules models most often break |
|---|---|---|---|
| TypeScript, JavaScript | `strict` mode, typescript-eslint recommended | Prettier or Biome, ESLint, `tsc --noEmit` | `unknown` plus narrowing instead of `any`; no `!` assertion without a reason; `import type` for types; discriminated unions instead of optional flags; exhaustive `switch` with `never`; no floating promises; `===` |
| React, Next.js | Rules of Hooks, framework docs for the installed version | eslint-plugin-react-hooks | Derive values instead of syncing state in `useEffect`; stable keys; keep `'use client'` to the smallest component; real `<button>` and `<a>` elements; fetch through the repo's data layer |
| React Native | Same as React, plus platform guidelines | ESLint | Virtualised lists for long data; no new style objects inside list rows; respect safe areas |
| Python | PEP 8, PEP 257, type hints | ruff, ruff format or black, mypy or pyright | Type hints on every signature; dataclass or pydantic for structured data; `pathlib`; context managers; no mutable default arguments; no bare `except`; `logging` not `print` |
| FastAPI | Framework docs | Same as Python | Pydantic models for input and output; `Depends` for auth; `HTTPException` for user errors; no blocking call inside `async def` |
| Node services (Express, NestJS) | Framework docs | ESLint | Schema validation on every input; one central error handler; no sync filesystem calls in handlers; graceful shutdown |
| SQL, Postgres | Team migration rules | Migration linter if present | Named columns, no `SELECT *`; idempotent migrations; an index for every foreign key and filter; `timestamptz`; constraints in the database; row-level security on exposed tables |
| Go | Effective Go, Go Code Review Comments | gofmt, go vet, staticcheck | Check every error and wrap with `%w`; `context.Context` first; small interfaces defined by the consumer; no panic in library code; table-driven tests |
| Rust | Rust API Guidelines | rustfmt, clippy | `Result` and `?`; no `unwrap` outside tests; borrow before cloning |
| Java, Kotlin | Google Java Style, Kotlin coding conventions | Checkstyle or ktlint, detekt | Immutable fields; no null returns; try-with-resources; constructor injection |
| C# | .NET coding conventions | dotnet format, analyzers | Nullable reference types on; async all the way; `using` for disposables |
| Swift | Swift API Design Guidelines | SwiftLint, swift-format | Value types first; `guard` for early exit; no force unwrap |
| Shell | Google Shell Style Guide | shellcheck, shfmt | `set -euo pipefail`; quote every variable; `[[ ]]` for tests |

**Any other language:** find its official style guide and its standard formatter and linter, and name them in your one-line statement. Write the language's own idioms. Do not transliterate a pattern from another language; look the idiom up when unsure.

## After writing

1. Run the formatter, the linter and the type checker on the files you changed, using the project's own commands.
2. Fix what they report.
3. Report in this shape:

```
Standard: <the one-line statement>
Tools run: <command> -> <result>
Deviations: <where you followed the repo over the language standard, or "none">
Not run: <what you could not run and why>
```

4. For anything beyond a trivial change, run the `standards-review` skill on the diff before calling the work done.