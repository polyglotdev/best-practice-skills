<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 24. useSyncExternalStore

## 24.1 Use `useSyncExternalStore` (not `useEffect` + `useState`) to subscribe to any store outside React (browser APIs, third-party state containers, module-level singletons).

> Why? `useSyncExternalStore` is designed specifically for external stores
> and guarantees tearing-free reads under concurrent rendering — a
> hand-rolled `useEffect` subscription can show inconsistent values across
> components during a concurrent render.

```jsx
// bad — hand-rolled subscription, vulnerable to tearing under concurrent rendering
function OnlineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  useEffect(() => {
    function handleChange() {
      setIsOnline(navigator.onLine)
    }
    window.addEventListener('online', handleChange)
    window.addEventListener('offline', handleChange)
    return () => {
      window.removeEventListener('online', handleChange)
      window.removeEventListener('offline', handleChange)
    }
  }, [])
  return <span>{isOnline ? 'online' : 'offline'}</span>
}
```

```jsx
// good
function subscribe(callback) {
  window.addEventListener('online', callback)
  window.addEventListener('offline', callback)
  return () => {
    window.removeEventListener('online', callback)
    window.removeEventListener('offline', callback)
  }
}

function OnlineStatus() {
  const isOnline = useSyncExternalStore(subscribe, () => navigator.onLine, () => true)
  return <span>{isOnline ? 'online' : 'offline'}</span>
}
```

## 24.2 Always provide a server snapshot function (the third argument) for any store used in a server-rendered app.

> Why? The server has no `window`/`navigator`; omitting the third argument
> throws during SSR for any store that reads browser-only globals.

```jsx
// bad — throws during SSR, no server snapshot provided
useSyncExternalStore(subscribe, () => navigator.onLine)
```

```jsx
// good
useSyncExternalStore(
  subscribe,
  () => navigator.onLine,
  () => true
)
```
