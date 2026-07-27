<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 16b. State

This chapter mirrors Airbnb's dedicated "State" section, translated for
function components. Rules that are specific to the `useState` hook API
(setter identity, lazy init, functional updaters) live in
[`16-usestate.md`](./16-usestate.md); this chapter is about the shape and
philosophy of state itself. Reducer patterns live in
[`17-usereducer.md`](./17-usereducer.md).

## 16b.1 State is data that changes over the lifetime of the component and cannot be derived from props or other state.

> Why? Anything derivable should be computed during render — storing it as
> state duplicates the source of truth and guarantees a moment when the two
> are out of sync.

```jsx
// bad
function Cart({ items }) {
  const [total, setTotal] = useState(0)

  useEffect(() => {
    setTotal(items.reduce((n, i) => n + i.price, 0))
  }, [items])

  return <div>{total}</div>
}

// good
function Cart({ items }) {
  const total = items.reduce((n, i) => n + i.price, 0)
  return <div>{total}</div>
}
```

## 16b.2 Keep each piece of state focused on one concern; don't merge unrelated flags into a single object.

> Why? Merged state forces every unrelated update to spread the previous
> object, and it hides which fields actually change together. Split state
> lets React batch efficiently and lets readers see the concerns.

```jsx
// bad
const [state, setState] = useState({
  isOpen: false,
  cursor: 0,
  query: ''
})

const onType = (e) =>
  setState((prev) => ({ ...prev, query: e.target.value }))

// good
const [isOpen, setIsOpen] = useState(false)
const [cursor, setCursor] = useState(0)
const [query, setQuery] = useState('')

const onType = (e) => setQuery(e.target.value)
```

## 16b.3 Group state into an object (or reducer) only when the fields must move together.

> Why? Two fields that always change in the same event should live in the
> same state so an update is atomic — otherwise intermediate renders can
> observe an inconsistent pair.

```jsx
// bad
const [x, setX] = useState(0)
const [y, setY] = useState(0)

const onMove = (e) => {
  setX(e.clientX)
  setY(e.clientY) // renders twice, one with new x + old y
}

// good
const [point, setPoint] = useState({ x: 0, y: 0 })

const onMove = (e) => setPoint({ x: e.clientX, y: e.clientY })
```

## 16b.4 Treat state as immutable — always produce a new value, never mutate in place.

> Why? React reads Object.is on the reference to decide whether to render.
> Mutating skips the render, produces stale UI, and breaks devtools time
> travel.

```jsx
// bad
const [todos, setTodos] = useState([])

const toggle = (id) => {
  const t = todos.find((t) => t.id === id)
  t.done = !t.done // mutation
  setTodos(todos)
}

// good
const [todos, setTodos] = useState([])

const toggle = (id) =>
  setTodos((prev) =>
    prev.map((t) => (t.id === id ? { ...t, done: !t.done } : t))
  )
```

## 16b.5 Never store props in state to "make them editable" — lift the state up or copy on a specific event.

> Why? Copying props into state on mount desyncs them from the parent the
> instant the parent updates. If a child truly needs its own value derived
> from a prop, key the component on the source so React remounts on change.

```jsx
// bad
function EmailField({ initialEmail }) {
  const [email, setEmail] = useState(initialEmail)
  return <input value={email} onChange={(e) => setEmail(e.target.value)} />
}

// good — lift the state
function EmailField({ email, onChange }) {
  return <input value={email} onChange={(e) => onChange(e.target.value)} />
}

// good — reset on identity change using key
;<EmailField key={userId} email={email} onChange={setEmail} />
```

## 16b.6 Reset state by remounting the component with a new `key`, not by writing an effect that clears it.

> Why? A `key` change is a single, declarative signal that means "this is
> a different logical instance". Effects that reset state on prop changes
> race with user input and typically introduce their own bugs.

```jsx
// bad
function ProfileForm({ userId, initial }) {
  const [form, setForm] = useState(initial)

  useEffect(() => {
    setForm(initial) // races with user typing
  }, [userId])

  return <form>{/* ... */}</form>
}

// good
;<ProfileForm key={userId} initial={initial} />
```

## 16b.7 Reach for `useReducer` when updates span multiple fields, encode a state machine, or must be tested in isolation.

> Why? A reducer names the transitions, keeps updates atomic, and is a
> pure function — trivially unit-testable without React.

```jsx
// bad
const [step, setStep] = useState('idle')
const [data, setData] = useState(null)
const [error, setError] = useState(null)

const start = () => {
  setStep('loading')
  setError(null)
  setData(null)
}

// good
function reducer(state, action) {
  switch (action.type) {
    case 'START':
      return { status: 'loading' }
    case 'RESOLVE':
      return { status: 'success', data: action.data }
    case 'REJECT':
      return { status: 'error', error: action.error }
    default:
      return state
  }
}

const [state, dispatch] = useReducer(reducer, { status: 'idle' })
```

## 16b.8 Model mutually exclusive UI states as a discriminated union, not as parallel booleans.

> Why? Parallel booleans allow impossible combinations (`isLoading &&
> hasError`). A discriminated status field makes the invalid states
> unrepresentable and simplifies rendering to a `switch`.

```jsx
// bad
const [isLoading, setLoading] = useState(false)
const [isError, setError] = useState(false)
const [data, setData] = useState(null)

// good
const [state, setState] = useState({ status: 'idle' })

switch (state.status) {
  case 'idle':
    return <Idle />
  case 'loading':
    return <Spinner />
  case 'success':
    return <View data={state.data} />
  case 'error':
    return <ErrorBox error={state.error} />
}
```

## 16b.9 Update state based on the previous state with the functional updater form.

> Why? Multiple updates in the same event, in a `useEffect`, or in a
> `Promise.then` all see the same closed-over value. The updater form
> gives each call the latest state.

```jsx
// bad
const inc = () => {
  setCount(count + 1)
  setCount(count + 1) // still +1 total
}

// good
const inc = () => {
  setCount((n) => n + 1)
  setCount((n) => n + 1) // +2 total
}
```

## 16b.10 Persist state (URL, localStorage, server) at the boundary — not inside `useState`'s initializer if the value can change externally.

> Why? A lazy initializer runs only once per mount. If the persisted value
> can change from another tab, another route, or the server, subscribe to
> that source instead of copying it into state on mount.

```jsx
// bad
const [theme, setTheme] = useState(() => localStorage.getItem('theme'))

// good
const theme = useSyncExternalStore(
  (cb) => {
    window.addEventListener('storage', cb)
    return () => window.removeEventListener('storage', cb)
  },
  () => localStorage.getItem('theme') ?? 'light',
  () => 'light'
)
```

## 16b.11 Do not read state inside `setState`'s updater and then dispatch other actions; keep updaters pure.

> Why? React may call the updater multiple times (strict mode, batching).
> Side effects there run repeatedly. Effects and event handlers are the
> right place for side effects.

```jsx
// bad
setCount((n) => {
  analytics.track('increment', n + 1) // side effect in updater
  return n + 1
})

// good
setCount((n) => n + 1)
analytics.track('increment')
```
