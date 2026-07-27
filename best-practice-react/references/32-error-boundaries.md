<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 32. Error Boundaries

## 32.1 Wrap independent sections of the UI in an Error Boundary so one section's crash doesn't take down the whole page.

> Why? Without a boundary, an uncaught render error unmounts the entire
> React tree. Scoped boundaries contain the blast radius to the failing
> section and let the rest of the app keep working.

```tsx
// bad — no boundary, one widget crash blanks the entire dashboard
function Dashboard() {
  return (
    <>
      <RevenueChart />
      <ActivityFeed />
    </>
  )
}
```

```tsx
// good
function Dashboard() {
  return (
    <>
      <ErrorBoundary fallback={<ChartError />}>
        <RevenueChart />
      </ErrorBoundary>
      <ErrorBoundary fallback={<FeedError />}>
        <ActivityFeed />
      </ErrorBoundary>
    </>
  )
}
```

## 32.2 An Error Boundary must be a class component (no hook equivalent exists); keep it small, generic, and reused across the app rather than rewritten per feature.

> Why? React only invokes `getDerivedStateFromError`/`componentDidCatch` on
> class components — this remains the one place a class is still required.
> Writing one generic, well-tested boundary and reusing it avoids
> re-solving the same problem badly in multiple places.

```tsx
// good
type ErrorBoundaryProps = {
  fallback: React.ReactNode
  children: React.ReactNode
}

type ErrorBoundaryState = {
  hasError: boolean
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    reportError(error, info)
  }

  render() {
    if (this.state.hasError) return this.props.fallback
    return this.props.children
  }
}
```

## 32.3 Error Boundaries catch render/lifecycle errors in their child tree; they do not catch errors in event handlers, effects, or async code — handle those with `try`/`catch`.

> Why? An Error Boundary is a render-phase mechanism. An exception thrown
> inside a `setTimeout` callback or an `onClick` handler happens outside
> React's render cycle and will not be caught by any boundary.

```jsx
// bad — assumes the boundary will catch this; it will not
function SubmitButton() {
  function handleClick() {
    throw new Error('boom')
  }
  return <button onClick={handleClick}>Submit</button>
}
```

```jsx
// good — handle it where it actually happens
function SubmitButton() {
  function handleClick() {
    try {
      submit()
    } catch (error) {
      reportError(error)
      showToast('Something went wrong')
    }
  }
  return <button onClick={handleClick}>Submit</button>
}
```

## 32.4 Reset an Error Boundary's state (e.g. via a changing `key`) when the underlying data that caused the error changes, rather than leaving the fallback UI stuck forever.

> Why? Without a reset mechanism, a boundary that has caught an error stays
> in its error state permanently, even if a retry with fresh props would
> succeed.

```jsx
// good — remount (and reset) the boundary when the id changes
<ErrorBoundary key={productId} fallback={<ProductError />}>
  <ProductDetails productId={productId} />
</ErrorBoundary>
```
