<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 21. useMemo & useCallback

There are exactly three legitimate reasons to reach for `useMemo` or
`useCallback`. If your use case isn't one of these three, remove the memo
and let the value recompute every render.

1. **Referential stability for a memoized child** (`React.memo`) so the
   child doesn't re-render on every parent render.
2. **Referential stability for a hook dependency array** so a `useEffect`,
   another `useMemo`, or a custom hook doesn't re-fire every render.
3. **Skipping measurably expensive pure computation** on renders where the
   inputs haven't changed.

## 21.1 Wrap a callback in `useCallback` when it's passed as a prop to a `React.memo`-wrapped child.

> Why? Without it, the child receives a new function reference every
> parent render and re-renders regardless of `memo`, defeating the whole
> point of memoizing the child.

```jsx
// bad — MemoRow re-renders every time Parent renders, memo is pointless
const MemoRow = memo(Row)

function Parent({ items }) {
  function handleSelect(id) {
    console.log(id)
  }
  return items.map((item) => <MemoRow key={item.id} item={item} onSelect={handleSelect} />)
}
```

```jsx
// good
const MemoRow = memo(Row)

function Parent({ items }) {
  const handleSelect = useCallback((id) => {
    console.log(id)
  }, [])
  return items.map((item) => <MemoRow key={item.id} item={item} onSelect={handleSelect} />)
}
```

## 21.2 Wrap a derived object/array in `useMemo` when it feeds another hook's dependency array and would otherwise cause that hook to re-run every render.

> Why? A fresh `{}`/`[]` literal is a new reference every render; if it's a
> dependency of `useEffect`, the effect re-runs every render regardless of
> whether the actual contents changed.

```jsx
// bad — options is a new object every render, effect re-fires every render
function Search({ query }) {
  const options = { query, limit: 20 }
  useEffect(() => {
    runSearch(options)
  }, [options])
}
```

```jsx
// good
function Search({ query }) {
  const options = useMemo(() => ({ query, limit: 20 }), [query])
  useEffect(() => {
    runSearch(options)
  }, [options])
}
```

## 21.3 Wrap a computation in `useMemo` only after measuring that it is actually expensive; do not memoize trivial arithmetic or short array operations "just in case."

> Why? `useMemo` itself has a cost (storing the previous deps and value,
> comparing deps every render). For cheap computations that cost exceeds
> the recomputation it's trying to avoid, making the code slower and
> harder to read for no benefit.

```jsx
// bad — memoizing a trivial calculation adds overhead for nothing
function Price({ amount, taxRate }) {
  const total = useMemo(() => amount * (1 + taxRate), [amount, taxRate])
  return <span>{total}</span>
}
```

```jsx
// good — just compute it
function Price({ amount, taxRate }) {
  const total = amount * (1 + taxRate)
  return <span>{total}</span>
}

// good — memoized because it's measured as expensive (e.g. large-list sort/filter)
function Leaderboard({ scores }) {
  const ranked = useMemo(() => [...scores].sort((a, b) => b.value - a.value), [scores])
  return <List items={ranked} />
}
```

## 21.4 Do not wrap every function passed as a prop in `useCallback` by default; only do it when 21.1 or 21.2 applies.

> Why? "Wrap everything in useCallback" is a cargo-cult habit that adds
> noise and a dependency array to maintain, without the memoized child or
> hook dependency that would make it pay off.

```jsx
// bad — child is a plain div, no memoization benefit exists
function Toolbar({ onSave }) {
  const handleClick = useCallback(() => {
    onSave()
  }, [onSave])
  return <button onClick={handleClick}>Save</button>
}
```

```jsx
// good
function Toolbar({ onSave }) {
  function handleClick() {
    onSave()
  }
  return <button onClick={handleClick}>Save</button>
}
```

## 21.5 Prefer the React Compiler (React 19's `babel-plugin-react-compiler`) where available instead of hand-written `useMemo`/`useCallback`; keep manual memoization only where the compiler cannot run or the project hasn't adopted it yet.

> Why? The React Compiler automatically memoizes values and callbacks
> based on static analysis, removing the need for most hand-written
> `useMemo`/`useCallback` and eliminating dependency-array bugs entirely.
> Until it's adopted project-wide, keep applying rules 21.1–21.4 manually.

```jsx
// good — with the React Compiler enabled, this is already optimal;
// no useMemo/useCallback needed, the compiler inserts memoization
function Leaderboard({ scores }) {
  const ranked = [...scores].sort((a, b) => b.value - a.value)
  return <List items={ranked} />
}
```
