---
name: vitest-tests
description: Use when writing, generating or fixing unit or component tests with Vitest (*.test.ts, *.spec.tsx), adding tests for new or untested code, mocking a module, timer, env var or network call, or when a Vitest test is flaky or passes for the wrong reason.
---

# Vitest Tests

A test is worth keeping when it fails if the behaviour breaks and passes for every refactor that keeps the behaviour. Generate cases from the behaviour, not from the lines of the implementation.

## Before writing

1. Read the Vitest config: `environment`, `globals`, `setupFiles`, aliases, `restoreMocks`.
2. Read one neighbouring test and copy its location, naming, imports and helpers.
3. Repo uses Jest instead: the same rules apply with `jest.*`.

## Choose the cases

For each public function, hook or component, list before writing:

- the normal case;
- boundaries: empty, zero, one, many, maximum, duplicate;
- invalid input and what is thrown or returned;
- each branch the code adds;
- for async code: rejection, and timeout where one exists.

Cover them with `it.each` when only the data differs.

## Shape

- `describe` names the unit. `it` names the behaviour: `returns 0 for an empty cart`.
- Arrange, act, assert. One reason to fail per test.
- No `if`, loop or `try/catch` inside a test.
- Assert the specific value: `toBe` for primitives, `toStrictEqual` for objects, `toThrow(ErrorClass)` or a message for errors. `toBeTruthy` and `toBeDefined` rarely prove anything.
- Snapshots only for small, stable output, as `toMatchInlineSnapshot`.

## Mocks

Mock only the boundary: network, clock, randomness, filesystem, env. Never mock the unit under test or its pure helpers.

| Need | Use |
|---|---|
| Replace one method | `vi.spyOn(obj, 'method')` |
| Replace a module | `vi.mock('./mod')`. It is hoisted above imports: values it needs go in `vi.hoisted(() => ...)` |
| Typed access to a mock | `vi.mocked(fn)` |
| Time | `vi.useFakeTimers()`, `vi.setSystemTime(date)`, `await vi.advanceTimersByTimeAsync(ms)`; `vi.useRealTimers()` in `afterEach` |
| Env and globals | `vi.stubEnv`, `vi.stubGlobal` |
| HTTP | The repo's MSW handlers if present, else mock the client module |

Restore in `afterEach` unless the config already does.

## Async

- `await expect(promise).rejects.toThrow(...)`. Without `await` the test passes whatever happens.
- Wait on a condition with `vi.waitFor` or `expect.poll`. Never sleep.

## Components

Query the way a user finds things (`getByRole`, `getByLabelText`), act with `userEvent`, assert on what is rendered. Do not assert on state, props or class names.

## Proof

1. Run the one file: `npx vitest run <path>` (or the project's script).
2. See each new test fail once: break the code or the expected value, run, restore. A test never seen failing proves nothing.
3. Report:

```
Cases: <count> covering <the list above, briefly>
Run: <command> -> <passed/failed>
Seen failing: <yes, how | no, why>
Mocked: <boundaries mocked>
Not covered: <cases left out and why>
```

## Never

- Weaken an assertion, or add `.skip`, to get to green.
- Change production code to make a test pass without saying so.
- Leave `.only` in the file.

## Opus advisor

Key decisions in this skill: the test boundary (unit vs integration, what to mock), a change to production code for testability, and tests that pin money, auth or a business rule.

Before acting on one, get a second opinion: call the `Agent` tool with `model: "opus"` (`subagent_type` `Plan`, read-only). Give it the decision, each option in one line, the evidence (`file:line`, measurements, the diff) and the constraints. Ask for a pick, the main risk of that pick, and what would change its mind. Do not send secrets or `.env` contents.

- One call per decision, not per finding. Skip it for routine choices the steps above already settle.
- If the advisor disagrees with you, show both views to the user in one line each and let them choose. Do not pick silently on architecture, auth, data model or money.
- In the report, list each advised decision: `Advisor: <decision> -> <pick> (<agreed | overruled because ...>)`.
