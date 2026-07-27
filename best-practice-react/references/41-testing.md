<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 41. Testing

## 41.1 Use `vitest` with `@testing-library/react`, `@testing-library/user-event`, and `@testing-library/jest-dom` for unit/integration tests; use Playwright for end-to-end tests.

> Why? This is the current standard, actively-maintained stack for React
> testing — `vitest` shares configuration with a Vite-based build, and
> Testing Library's philosophy (query like a user, not like an
> implementation) keeps tests resilient to internal refactors.

```tsx
// good
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

describe('LikeButton', () => {
  it('increments the like count on click', async () => {
    render(<LikeButton initialLikes={3} />)
    await userEvent.click(screen.getByRole('button', { name: /like/i }))
    expect(screen.getByText('4')).toBeInTheDocument()
  })
})
```

## 41.2 Query elements by role (`getByRole('button', { name: /save/i })`) as the default; reach for `getByTestId` only when no accessible query works.

> Why? Role-based queries fail exactly when the app becomes less
> accessible, turning tests into an accessibility safety net; test ids
> catch neither accessibility regressions nor DOM-structure regressions.

```tsx
// bad — test id, tells you nothing about whether the button is usable by a real user
screen.getByTestId('save-button')
```

```tsx
// good
screen.getByRole('button', { name: /save/i })
```

## 41.3 Simulate interactions with `userEvent`, not `fireEvent`.

> Why? `userEvent` fires the full sequence of real browser events a user
> interaction would produce (focus, pointer events, keyboard events) in
> the right order; `fireEvent` dispatches one bare synthetic event,
> missing side effects real interaction would trigger.

```tsx
// bad — fires one raw change event, skips focus/blur and other real browser behavior
fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } })
```

```tsx
// good
await userEvent.type(screen.getByLabelText(/email/i), 'a@b.com')
```

## 41.4 Assert on what the user sees and can do — rendered text, roles, and enabled/disabled state — not on component internals like state variables or instance methods.

> Why? A test coupled to internal state breaks every time you refactor
> the implementation, even when the user-visible behavior didn't change,
> which is precisely the coupling Testing Library's philosophy exists to
> avoid.

```tsx
// bad — reaches into component internals via a ref
const ref = createRef()
render(<Counter ref={ref} />)
expect(ref.current.state.count).toBe(0)
```

```tsx
// good — asserts what's actually rendered
render(<Counter />)
expect(screen.getByText('0')).toBeInTheDocument()
```

## 41.5 Do not write tests that assert on framework internals (the router's internal state, a library's private cache structure).

> Why? Framework internals are not your code's contract with users and
> can change between minor versions of a dependency, breaking tests that
> have nothing to do with your actual feature.

```tsx
// bad — asserts on react-query's internal cache map
expect(queryClient.getQueryCache().getAll().length).toBe(1)
```

```tsx
// good — asserts on what the user sees after the query resolves
render(<ProductPage />)
expect(await screen.findByText('Wireless Mouse')).toBeInTheDocument()
```

## 41.6 Prefer integration tests that render a component together with its real children over isolated unit tests that mock every child.

> Why? A component's actual behavior emerges from how it composes with
> its children; mocking every child tests a version of the component that
> doesn't correspond to what ships.

```tsx
// bad — every child mocked, doesn't test real composed behavior
vi.mock('./CartSummary', () => ({ CartSummary: () => <div /> }))
vi.mock('./CheckoutButton', () => ({ CheckoutButton: () => <div /> }))
```

```tsx
// good — render the real tree, mock only true external boundaries (network, timers)
render(<CheckoutPage cart={mockCart} />)
expect(screen.getByRole('button', { name: /pay/i })).toBeEnabled()
```

## 41.7 Wait for async UI updates with `waitFor` or `findBy*` queries; never use `setTimeout` to pace a test.

> Why? A hard-coded `setTimeout` either makes the test slower than
> necessary or, worse, flaky on a slower CI machine; `waitFor`/`findBy*`
> poll until the assertion passes or a sane timeout elapses.

```tsx
// bad — arbitrary fixed delay, flaky and slow
render(<UserProfile userId="1" />)
await new Promise((resolve) => setTimeout(resolve, 500))
expect(screen.getByText('Ada Lovelace')).toBeInTheDocument()
```

```tsx
// good
render(<UserProfile userId="1" />)
expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument()
```

## 41.8 Mock at the network layer with `msw` rather than mocking individual modules, whenever the code under test makes real network calls.

> Why? Mocking at the network boundary tests your actual fetch/parsing
> code path; mocking a module (e.g. your `api.ts` wrapper) skips over that
> code entirely and can hide real bugs in request construction or
> response parsing.

```tsx
// bad — mocks the module, skipping the real fetch/parsing logic entirely
vi.mock('./api', () => ({ getUser: vi.fn().mockResolvedValue({ name: 'Ada' }) }))
```

```tsx
// good
const server = setupServer(
  http.get('/api/users/:id', () => HttpResponse.json({ name: 'Ada' }))
)
```

## 41.9 Reserve snapshot tests for small, stable, deterministic output; do not snapshot large component trees that change frequently.

> Why? A snapshot of a large, frequently-changing tree becomes a rubber
> stamp — developers accept the diff without reading it, defeating the
> point of the test entirely.

```tsx
// bad — snapshotting an entire, frequently-changing page
expect(render(<Dashboard />).container).toMatchSnapshot()
```

```tsx
// good — small, stable, deterministic
expect(formatCurrency(1234.5)).toMatchSnapshot()
```

## 41.10 Run end-to-end tests against real application routes with the real router, not a mocked navigation layer.

> Why? The router is exactly the kind of integration point that unit
> tests mock away; E2E tests exist specifically to verify that navigation,
> URL state, and page transitions work as an actual user would experience
> them.

```ts
// good — Playwright test hitting a real running app
test('can navigate from list to detail', async ({ page }) => {
  await page.goto('/products')
  await page.getByRole('link', { name: 'Wireless Mouse' }).click()
  await expect(page).toHaveURL(/\/products\/\d+/)
})
```

## 41.11 Run automated accessibility checks (`axe-core`, `@axe-core/playwright`) in CI against key pages/components.

> Why? Automated axe checks catch a meaningful subset of the accessibility
> issues in §35 (missing labels, contrast failures, missing alt text)
> mechanically, before a human reviewer ever needs to notice them.

```ts
// good
import { expect, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test('checkout page has no automatic a11y violations', async ({ page }) => {
  await page.goto('/checkout')
  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations).toEqual([])
})
```
