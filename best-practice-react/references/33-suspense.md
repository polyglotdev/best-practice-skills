<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 33. Suspense

## 33.1 Wrap a component that can suspend (via `use()`, `lazy()`, or a Suspense-integrated data library) in a `<Suspense>` boundary with a meaningful fallback.

> Why? Without a boundary, a suspending component bubbles up to the
> nearest ancestor `<Suspense>` (or crashes the app if there is none),
> which is rarely the loading UI you actually want at that spot.

```jsx
// bad — no boundary around a component that can suspend
function Page() {
  return <UserProfile userPromise={userPromise} />
}
```

```jsx
// good
function Page() {
  return (
    <Suspense fallback={<ProfileSkeleton />}>
      <UserProfile userPromise={userPromise} />
    </Suspense>
  )
}
```

## 33.2 Place Suspense boundaries at meaningful UI regions, not one giant boundary around the whole page.

> Why? A single top-level boundary means any slow child blanks the entire
> page with a spinner, discarding already-loaded content. Granular
> boundaries let fast parts of the page render immediately while slow parts
> show their own fallback.

```jsx
// bad — one boundary, one slow widget blanks the whole page
function Dashboard() {
  return (
    <Suspense fallback={<FullPageSpinner />}>
      <Header />
      <SlowRecommendations />
      <Footer />
    </Suspense>
  )
}
```

```jsx
// good
function Dashboard() {
  return (
    <>
      <Header />
      <Suspense fallback={<RecommendationsSkeleton />}>
        <SlowRecommendations />
      </Suspense>
      <Footer />
    </>
  )
}
```

## 33.3 Use `lazy()` + `<Suspense>` for route-level and heavy, rarely-used components (rich text editors, charting libraries, admin-only panels).

> Why? Code-splitting these out of the main bundle reduces initial load
> time; `Suspense` gives you the loading state for free while the chunk
> downloads.

```jsx
// bad — a heavy chart library is bundled into the initial page load
import HeavyChart from './HeavyChart'

function Report() {
  return <HeavyChart />
}
```

```jsx
// good
const HeavyChart = lazy(() => import('./HeavyChart'))

function Report() {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <HeavyChart />
    </Suspense>
  )
}
```

## 33.4 Pair every `<Suspense>` boundary that can error with an `<ErrorBoundary>` above it.

> Why? Suspense only handles the "still loading" state; a rejected Promise
> or a thrown error while resolving still needs an Error Boundary to avoid
> crashing the tree.

```jsx
// good
<ErrorBoundary fallback={<ProfileError />}>
  <Suspense fallback={<ProfileSkeleton />}>
    <UserProfile userPromise={userPromise} />
  </Suspense>
</ErrorBoundary>
```
