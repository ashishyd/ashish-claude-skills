---
name: typescript-types
description: Use when writing or changing TypeScript (.ts, .tsx), fixing a type error, typing an API response, form, props or generic function, or when tempted to write `any`, `as`, `!` or `@ts-ignore`.
---

# TypeScript Types

A type is correct when it is derived from the source of truth and checked by the compiler. A type that is asserted (`as`, `!`, `any`) is a claim nobody checked.

## Before writing

1. Read `tsconfig.json`: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`, and the TypeScript version in the lockfile.
2. Find where the data's shape is already defined: a schema (zod, valibot), generated types (Prisma, Supabase, OpenAPI, GraphQL codegen), or an existing type. Import it. Do not re-declare it.

## Rules

| Situation | Do | Not |
|---|---|---|
| Data from outside (HTTP, `JSON.parse`, storage, env, `catch`) | Type it `unknown`, parse with the repo's schema library, use the inferred type (`z.infer`). No library: write a type guard | `as User`, `any` |
| Checking a value fits a type | `satisfies` (keeps the literal type) | `as` |
| Value may be null or undefined | Narrow with a check or early return | `!` |
| A type that follows another | `typeof`, `keyof`, `T['key']`, `ReturnType`, `Parameters`, `Awaited`, `Pick`, `Omit` | A second hand-written copy |
| A value with several states | Discriminated union on one literal field | Optional fields and boolean flags |
| `switch` over a union | `default:` assigns the value to `never` | A silent default |
| Fixed set of strings | Union of literals or an `as const` object, whichever the repo uses | A new `enum` in a repo that has none |
| Exported function | Explicit return type | Inferred return leaking internals |
| Generic | A type parameter that links two positions, with `extends` | A parameter used once |
| Array or object parameter you do not change | `readonly T[]`, `Readonly<T>` | Mutable by default |
| Suppressing an error is truly needed | `@ts-expect-error` with the reason on the same line | `@ts-ignore` |

`as const` and `as` directly after a runtime check are the only casts that need no comment.

## Places the compiler lies

- `JSON.parse`, `response.json()` and `any`-typed library results return `any`. Assign them to `unknown` at once.
- `obj[key]` on a `Record<string, T>` or array is typed `T`, not `T | undefined`, unless `noUncheckedIndexedAccess` is on. Check before use.
- `Object.keys(x)` is `string[]`, not `(keyof T)[]`. Do not cast it; iterate a known key list.
- `.filter(Boolean)` narrows only on TypeScript 5.5 or newer. Older: write a type predicate.
- `catch (e)` is `unknown`. Narrow with `instanceof Error`.
- An optional property and a property that may be `undefined` are different under `exactOptionalPropertyTypes`.

## Fixing a type error

1. Read the whole error; the last line names the mismatch.
2. Fix it where the wrong type enters, not where it is used.
3. Never widen a type, add `any`, or cast to make the error go away. If the types say the code is wrong, the code may be wrong.

## Proof

Run the project's type check (its script, else `tsc --noEmit`) and the linter on the files changed. For type-level logic, add an `expectTypeOf` or `@ts-expect-error` test. Report:

```
Types from: <schema or generated source used>
Check: <command> -> <result>
Casts added: <file:line and the runtime check that justifies each, or "none">
```

## Opus advisor

Key decisions in this skill: a new shared type, generic or discriminated union that shapes a module's public API, a schema at a trust boundary, and any cast or `any` you cannot avoid.

Before acting on one, get a second opinion: call the `Agent` tool with `model: "opus"` (`subagent_type` `Plan`, read-only). Give it the decision, each option in one line, the evidence (`file:line`, measurements, the diff) and the constraints. Ask for a pick, the main risk of that pick, and what would change its mind. Do not send secrets or `.env` contents.

- One call per decision, not per finding. Skip it for routine choices the steps above already settle.
- If the advisor disagrees with you, show both views to the user in one line each and let them choose. Do not pick silently on architecture, auth, data model or money.
- In the report, list each advised decision: `Advisor: <decision> -> <pick> (<agreed | overruled because ...>)`.
