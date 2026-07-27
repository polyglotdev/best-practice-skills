<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 25. useTransition & useDeferredValue

## 25.1 Wrap a state update that triggers an expensive re-render in `startTransition` when you want the UI to remain responsive to more urgent updates (typing, clicking) while it completes.

> Why? Transitions let React interrupt a low-priority render (e.g.
> re-filtering a huge list) to handle a higher-priority one (e.g. the next
> keystroke), instead of blocking the input while the list re-renders.

```jsx
// bad — every keystroke blocks on re-filtering a huge list
function SearchPage({ allItems }) {
  const [query, setQuery] = useState('')
  const filtered = allItems.filter((item) => item.name.includes(query))
  return (
    <>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <List items={filtered} />
    </>
  )
}
```

```jsx
// good — typing stays instant, the filtered list update is deprioritized
function SearchPage({ allItems }) {
  const [query, setQuery] = useState('')
  const [isPending, startTransition] = useTransition()
  const [filtered, setFiltered] = useState(allItems)

  function handleChange(event) {
    const next = event.target.value
    setQuery(next)
    startTransition(() => {
      setFiltered(allItems.filter((item) => item.name.includes(next)))
    })
  }

  return (
    <>
      <input value={query} onChange={handleChange} />
      {isPending ? <Spinner /> : <List items={filtered} />}
    </>
  )
}
```

## 25.2 Use `useDeferredValue` when you don't control the state setter (e.g. a value from props or a form library) but still want to deprioritize a slow render derived from it.

> Why? `useDeferredValue` gives you the transition benefit without needing
> to wrap the original `setState` call, which matters when that call
> happens outside your component.

```jsx
// bad — no way to wrap the parent's setState in startTransition
function ExpensiveList({ query }) {
  const filtered = filterHugeList(query)
  return <List items={filtered} />
}
```

```jsx
// good
function ExpensiveList({ query }) {
  const deferredQuery = useDeferredValue(query)
  const filtered = filterHugeList(deferredQuery)
  return <List items={filtered} />
}
```

## 25.3 Do not use `useTransition`/`useDeferredValue` as a substitute for actually fixing an O(n²) render or an unmemoized expensive computation.

> Why? These APIs reschedule *when* work happens; they do not make the
> work itself cheaper. If a render is slow enough to need deprioritizing,
> also check whether it can be made faster (§21, §42).

```jsx
// bad — papering over an O(n^2) computation with a transition instead of fixing it
function Grid({ rows, cols }) {
  const [, startTransition] = useTransition()
  const cells = rows.flatMap((row) => cols.map((col) => computeExpensive(row, col)))
}
```

```jsx
// good — fix the algorithm, then apply a transition only if still needed
function Grid({ rows, cols }) {
  const cells = useMemo(() => precomputeGrid(rows, cols), [rows, cols])
}
```
