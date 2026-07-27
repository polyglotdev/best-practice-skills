<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 33. Testing

## 33.1 Use Vitest for application code and `node:test` for
dependency-light libraries; avoid mixing test runners in one project.

```js
// good — vitest
import { describe, expect, it } from 'vitest'
import { formatCurrency } from './format-currency.js'

describe('formatCurrency', () => {
  it('formats a whole dollar amount', () => {
    expect(formatCurrency(1000)).toBe('$1,000.00')
  })
})
```

```js
// good — node:test, zero extra dependencies
import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { formatCurrency } from './format-currency.js'

describe('formatCurrency', () => {
  it('formats a whole dollar amount', () => {
    assert.equal(formatCurrency(1000), '$1,000.00')
  })
})
```

## 33.2 Write sentence-style test names that describe observable
behavior, not implementation.

```js
// bad
it('test1', () => {
  // ...
})

// good
it('returns an empty array when the input list is empty', () => {
  // ...
})
```

## 33.3 Use fake timers for anything that depends on `Date`,
`setTimeout`, or `setInterval`; never use a real `sleep` in a test.

```js
// bad — makes the suite slow and flaky
it('retries after a delay', async () => {
  const attempt = startRetryingOperation()
  await new Promise((resolve) => setTimeout(resolve, 5000))
  expect(attempt.hasRetried).toBe(true)
})

// good
import { afterEach, beforeEach, expect, it, vi } from 'vitest'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

it('retries after a delay', () => {
  const attempt = startRetryingOperation()
  vi.advanceTimersByTime(5000)
  expect(attempt.hasRetried).toBe(true)
})
```

## 33.4 Test behavior through the public API; don't assert on
private implementation details.

> Why? A test coupled to internals breaks on every refactor even when
> the observable behavior hasn't changed, which trains people to distrust
> or delete tests instead of fixing real regressions.

```js
// bad — reaches into a private field
it('increments the internal counter', () => {
  const counter = new Counter()
  counter.increment()
  expect(counter._count).toBe(1)
})

// good — asserts on the public contract
it('reports 1 after a single increment', () => {
  const counter = new Counter()
  counter.increment()
  expect(counter.value).toBe(1)
})
```

## 33.5 Keep unit tests isolated from real network, filesystem, and
clock; use dependency injection or module mocks at the boundary.

```js
// good — the HTTP client is injected, so the test never hits a real network
async function fetchUserName(userId, httpClient = fetch) {
  const response = await httpClient(`/api/users/${userId}`)
  const user = await response.json()
  return user.name
}
```

---
