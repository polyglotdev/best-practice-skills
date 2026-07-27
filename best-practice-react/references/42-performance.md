<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 42. Performance

## 42.1 Measure before optimizing — use the React DevTools Profiler and the browser's Performance panel; never optimize based on a hunch about what's slow.

> Why? Intuition about React performance is frequently wrong (the actual
> bottleneck is often somewhere unexpected, like an unmemoized context
> value or a layout thrash), and "optimizing" the wrong thing adds
> complexity for zero measured benefit.

```jsx
// bad — memoizing a component because it "feels" like it might be slow, with no profiling done
const ProductRow = memo(function ProductRow({ product }) {
  return <li>{product.name}</li>
})
```

```jsx
// good — profile first (React DevTools Profiler), then apply memoization only where the flame graph shows a real cost
```

## 42.2 Virtualize lists with roughly 100+ items using `@tanstack/react-virtual` rather than rendering every row.

> Why? Rendering thousands of DOM nodes for an unbounded list is
> expensive to create, lay out, and keep in the DOM; a virtualizer renders
> only the rows currently in (or near) the viewport.

```jsx
// bad — renders every row regardless of list size
function ProductList({ products }) {
  return (
    <ul>
      {products.map((product) => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  )
}
```

```jsx
// good
function ProductList({ products }) {
  const parentRef = useRef(null)
  const virtualizer = useVirtualizer({
    count: products.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40
  })

  return (
    <ul ref={parentRef} style={{ overflow: 'auto', height: 600 }}>
      {virtualizer.getVirtualItems().map((row) => (
        <li key={products[row.index].id}>{products[row.index].name}</li>
      ))}
    </ul>
  )
}
```

## 42.3 Code-split routes and heavy sub-trees with `React.lazy` + `Suspense`, or the framework's native route-level splitting.

> Why? Shipping every route's JavaScript in the initial bundle delays
> time-to-interactive for the first page a user actually needs; splitting
> defers the cost of rarely-visited routes until they're actually visited.

```jsx
// bad — a rarely-visited admin panel bundled into the main app chunk
import AdminPanel from './AdminPanel'
```

```jsx
// good
const AdminPanel = lazy(() => import('./AdminPanel'))
```

## 42.4 Debounce or throttle high-frequency inputs (search-as-you-type, scroll, resize); `useDeferredValue` is often sufficient without a manual timer.

> Why? Recomputing or refetching on every single keystroke/scroll tick can
> overwhelm the main thread or the network with redundant work;
> deprioritizing or batching that work keeps the UI responsive.

```jsx
// bad — fires a network request on every keystroke
function SearchBox() {
  const [query, setQuery] = useState('')
  useEffect(() => {
    search(query)
  }, [query])
}
```

```jsx
// good — deferred value lets typing stay responsive while search work is deprioritized
function SearchBox() {
  const [query, setQuery] = useState('')
  const deferredQuery = useDeferredValue(query)
  useEffect(() => {
    search(deferredQuery)
  }, [deferredQuery])
}
```

## 42.5 Move CPU-bound pure computation that blocks the main thread into a Web Worker (via `comlink` or similar), rather than accepting a janky UI.

> Why? Any synchronous computation on the main thread blocks rendering and
> input handling for its entire duration; a worker runs on a separate
> thread, keeping the UI responsive while the computation completes.

```jsx
// bad — a heavy synchronous computation blocks the UI thread
function ImageProcessor({ imageData }) {
  const processed = applyFiltersSync(imageData)
  return <Canvas data={processed} />
}
```

```jsx
// good — offloaded to a worker via comlink
const worker = wrap(new Worker(new URL('./image-worker.js', import.meta.url)))

function ImageProcessor({ imageData }) {
  const [processed, setProcessed] = useState(null)
  useEffect(() => {
    worker.applyFilters(imageData).then(setProcessed)
  }, [imageData])
  return processed ? <Canvas data={processed} /> : <Spinner />
}
```

## 42.6 Do not memoize primitive values with no dependencies (`useMemo(() => 42, [])` is strictly worse than the literal `42`).

> Why? `useMemo` has its own bookkeeping overhead (storing deps,
> comparing them); wrapping a constant or trivially-cheap expression in it
> adds cost with no computation being avoided.

```jsx
// bad
const max = useMemo(() => 100, [])
```

```jsx
// good
const max = 100
```

## 42.7 Do not wrap a handler in `useCallback` when it's used only inline in this render and never passed to a memoized child or a hook dependency array.

> Why? See §21.4 — without a memoized consumer downstream, the
> `useCallback` wrapper adds a dependency array to maintain for zero
> referential-stability benefit.

```jsx
// bad — no memoized child, no hook dependency consuming this
function Toolbar({ onSave }) {
  const handleClick = useCallback(() => onSave(), [onSave])
  return <button onClick={handleClick}>Save</button>
}
```

```jsx
// good
function Toolbar({ onSave }) {
  return <button onClick={() => onSave()}>Save</button>
}
```

## 42.8 Once the React Compiler is enabled project-wide, remove manual `useMemo`/`useCallback` opportunistically rather than continuing to hand-write them.

> Why? The compiler statically inserts equivalent (and often better)
> memoization automatically; keeping hand-written memoization alongside it
> is redundant and adds dependency-array maintenance the compiler doesn't
> need.

```jsx
// bad — hand-written memoization left in place after adopting the React Compiler
const total = useMemo(() => items.reduce((sum, item) => sum + item.price, 0), [items])
```

```jsx
// good — the compiler handles this automatically once enabled
const total = items.reduce((sum, item) => sum + item.price, 0)
```

## 42.9 Split large Client Components into smaller pieces so `React.memo` boundaries actually have something narrow to compare.

> Why? Wrapping one enormous component in `memo` means almost any prop
> change forces a full re-render anyway; smaller components give `memo` a
> narrower, more effective prop set to compare against.

```jsx
// bad — one giant memoized component, most prop changes still force a full re-render
const Dashboard = memo(function Dashboard({ user, notifications, settings, theme }) {
  return (
    <>
      <Header user={user} theme={theme} />
      <NotificationList notifications={notifications} />
      <SettingsPanel settings={settings} />
    </>
  )
})
```

```jsx
// good — smaller, independently memoized pieces
const Header = memo(function Header({ user, theme }) {
  return <header>{user.name}</header>
})
const NotificationList = memo(function NotificationList({ notifications }) {
  return <ul>{notifications.map((n) => <li key={n.id}>{n.text}</li>)}</ul>
})
```

## 42.10 Wrap a component in `React.memo` when it renders many times with mostly-stable props and profiling shows its re-render cost matters.

> Why? `memo` skips re-rendering when props are shallowly equal to the
> previous render — valuable for components rendered often (e.g. list
> rows) whose props rarely actually change, and a net loss for components
> that render rarely or whose props change every time anyway.

```jsx
// bad — memo on a component that re-renders with new props virtually every time anyway
const Clock = memo(function Clock({ now }) {
  return <span>{now}</span>
})
```

```jsx
// good — memo pays off for a list row rendered hundreds of times with stable per-row props
const ProductRow = memo(function ProductRow({ product }) {
  return <li>{product.name}</li>
})
```

## 42.11 Avoid rendering the full cost of off-screen content; use `content-visibility: auto` in CSS for long pages with sections far below the fold.

> Why? `content-visibility: auto` tells the browser to skip layout and
> paint work for content that isn't near the viewport, without requiring
> any component-level virtualization logic.

```css
/* good */
.below-fold-section {
  content-visibility: auto;
  contain-intrinsic-size: 800px;
}
```

## 42.12 Analyze bundle size with `next-bundle-analyzer` or `vite-bundle-visualizer`, tree-shake unused code, and avoid deep imports from `lodash` and similar utility libraries.

> Why? A deep import like `import debounce from 'lodash/debounce'` (or
> worse, `import _ from 'lodash'`) can pull in far more code than the app
> actually uses; regularly checking the bundle analyzer catches these
> regressions before they ship.

```js
// bad — imports the entire lodash library for one function
import _ from 'lodash'
const debounced = _.debounce(handleSearch, 300)
```

```js
// good — import only what's needed, or use a native/lighter alternative
import debounce from 'lodash-es/debounce'
const debounced = debounce(handleSearch, 300)
```
