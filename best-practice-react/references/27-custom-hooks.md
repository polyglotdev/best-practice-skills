<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 27. Custom Hooks

## 27.1 Extract a custom hook when the same stateful logic (not just JSX) is duplicated across two or more components.

> Why? Custom hooks are the modern replacement for mixins and
> render-prop/HOC-based logic sharing — they compose cleanly, keep full
> type inference, and avoid wrapper-component nesting ("wrapper hell").

```jsx
// bad — the same subscribe/unsubscribe logic copy-pasted in two components
function OnlineDot() {
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
  return <span>{isOnline ? 'green' : 'red'}</span>
}
```

```jsx
// good — extracted once, reused everywhere
function useOnlineStatus() {
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
  return isOnline
}

function OnlineDot() {
  const isOnline = useOnlineStatus()
  return <span>{isOnline ? 'green' : 'red'}</span>
}
```

## 27.2 Name every custom hook starting with `use`, even if it doesn't call another hook internally today.

> Why? The `use` prefix is what allows `eslint-plugin-react-hooks` to apply
> the Rules of Hooks checks to your function at all. Without it, the
> linter treats the function as an ordinary utility and won't catch
> violations.

```jsx
// bad — calls useState internally but isn't named like a hook
function toggle(initial) {
  const [value, setValue] = useState(initial)
  return [value, () => setValue((v) => !v)]
}
```

```jsx
// good
function useToggle(initial) {
  const [value, setValue] = useState(initial)
  return [value, () => setValue((v) => !v)]
}
```

## 27.3 Return a small, purposeful value from a custom hook — a tuple for state-like hooks, an object for hooks with many named fields — not a giant grab-bag.

> Why? A tuple (`[value, setValue]`) lets callers rename freely, matching
> the convention of `useState`/`useReducer`. An object return should be
> used when there are many fields, since positional tuples become
> unreadable past two or three items.

```jsx
// bad — six-element tuple, unreadable at the call site
function useForm(initial) {
  return [values, errors, touched, handleChange, handleBlur, handleSubmit]
}
```

```jsx
// good — named object for a hook with many fields
function useForm(initial) {
  return { values, errors, touched, handleChange, handleBlur, handleSubmit }
}

// good — tuple is fine for the classic two-value case
function useToggle(initial) {
  return [value, toggle]
}
```

## 27.4 Keep a custom hook's dependencies explicit in its own signature; do not have it silently reach into module-level mutable state that callers can't see.

> Why? A hook that secretly depends on a module-level variable is
> impossible to test in isolation and creates hidden coupling between
> unrelated components that happen to use the same hook.

```jsx
// bad — hidden module-level mutable state
let currentUser = null

function useCurrentUser() {
  return currentUser
}
```

```jsx
// good — dependency is explicit via context or a parameter
function useCurrentUser() {
  return useContext(AuthContext).user
}
```
