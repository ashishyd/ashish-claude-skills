---
name: playwright-tests
description: Use when writing, generating or fixing Playwright end-to-end tests, covering a user journey in a real browser, choosing locators, handling login state or test data, or when an e2e test is flaky, slow or times out.
---

# Playwright Tests

An end-to-end test follows one user journey through the real app and asserts what the user would see. Every wait is a wait for an outcome, never for time.

## Before writing

1. Read `playwright.config`: `baseURL`, `webServer`, `testDir`, `projects`, any setup project and `storageState`.
2. Read the existing fixtures or page objects and one spec. Reuse them.
3. Get real roles and names from the running page: use a browser tool to read the accessibility tree, or `npx playwright codegen <url>`. Do not guess selectors from source.

## What to cover

The journeys whose failure costs money or trust: sign in, the core create-edit-delete flow, checkout, permissions. One journey per test. Edge cases of logic belong in unit tests.

## Locators, in this order

1. `getByRole('button', { name: 'Save' })`
2. `getByLabel`, `getByPlaceholder`, `getByText`
3. `getByTestId`, when nothing user-visible is stable

Scope by chaining or `filter({ hasText })`. No CSS or XPath chains, no `nth()` on unscoped lists. A control that cannot be found by role is often an accessibility bug: report it.

## Waiting and asserting

| Do | Not |
|---|---|
| `await expect(locator).toBeVisible()` (retries) | `expect(await locator.isVisible()).toBe(true)` |
| `await expect(page).toHaveURL(...)` after navigation | `waitForTimeout`, `networkidle` |
| Start `page.waitForResponse(...)` before the click, await it after | Sleeping until the request is probably done |
| `await expect(async () => {...}).toPass()` for real polling | Raising the timeout |

## Isolation

- **Auth:** sign in once in a setup project, save `storageState`, reuse it. No UI login in each test.
- **Data:** create what the test needs through the API (`request` fixture) with a unique id, and delete it after. Tests run in parallel and in any order.
- **Network:** `page.route` for third parties and for forcing error states. Do not mock your own backend in a journey test.

## Shape

- Test title states the journey: `user can reset a password`.
- `test.step` for the stages of a long journey.
- Assert the end state the user cares about, plus the one side effect that proves it persisted (reload, then check).

## Flaky tests

Turn on `trace: 'on-first-retry'`, open the trace, and find what the test did not wait for. Adding retries, timeouts or sleeps hides the bug; it is either a missing wait in the test or a race in the app.

## Proof

1. `npx playwright test <path> --project=chromium`
2. `npx playwright test <path> --repeat-each=5` to show it is stable.
3. Report:

```
Journey: <one line each>
Run: <command> -> <result>
Repeat x5: <result>
Data: <how created and cleaned up>
Not covered: <browsers, journeys or states left out>
```
