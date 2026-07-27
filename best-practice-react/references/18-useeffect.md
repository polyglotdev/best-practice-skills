<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 18. useEffect

`useEffect` is the most misused hook in React. Read this section fully
before adding a new effect — in most cases where a beginner reaches for
`useEffect`, the correct answer is **not to use an effect at all**.

## 18.1 An effect exists to synchronize a component with a system **outside** React — not to compute values, not to react to prop/state changes in general.

> Why? React already re-renders your component whenever props or state
> change; you don't need an effect to "notice" a change and react to it in
> JS-only terms. Effects are for keeping something outside React's model
> (the DOM, a subscription, a network connection, browser storage, a
> third-party widget) in sync with React's current state.

```jsx
// bad — using an effect to compute a derived value
function Cart({ items }) {
  const [total, setTotal] = useState(0)
  useEffect(() => {
    setTotal(items.reduce((sum, item) => sum + item.price, 0))
  }, [items])
  return <div>{total}</div>
}
```

```jsx
// good — compute during render, no effect, no extra state, no extra render
function Cart({ items }) {
  const total = items.reduce((sum, item) => sum + item.price, 0)
  return <div>{total}</div>
}
```

## 18.2 Do not use an effect to transform data for rendering. Compute it directly in the render body (optionally memoized — §21).

> Why? Same principle as 18.1: an effect runs *after* render and commits a
> second render just to show the transformed value, causing a visible
> flash and wasted work.

```jsx
// bad
function FilteredList({ items, query }) {
  const [filtered, setFiltered] = useState([])
  useEffect(() => {
    setFiltered(items.filter((item) => item.name.includes(query)))
  }, [items, query])
  return <List items={filtered} />
}
```

```jsx
// good
function FilteredList({ items, query }) {
  const filtered = items.filter((item) => item.name.includes(query))
  return <List items={filtered} />
}
```

## 18.3 Do not use an effect to run logic that belongs in an event handler (e.g. "when the user submits, do X").

> Why? An effect fires because *something rendered*, not because a
> specific user action happened. Tying business logic to a render side
> effect makes it fire on remounts, Strict Mode double-invokes, and any
> unrelated re-render that happens to touch the same dependency.

```jsx
// bad — effect watches a "submitted" flag to trigger a purchase
function CheckoutForm() {
  const [submitted, setSubmitted] = useState(false)
  useEffect(() => {
    if (submitted) buyProduct()
  }, [submitted])
  return <button onClick={() => setSubmitted(true)}>Buy</button>
}
```

```jsx
// good — the event handler does the thing the event caused, directly
function CheckoutForm() {
  function handleClick() {
    buyProduct()
  }
  return <button onClick={handleClick}>Buy</button>
}
```

## 18.4 Do not use an effect to reset all state when a prop (like an id) changes; give the component a `key` instead.

> Why? Changing `key` tells React to treat the element as a brand-new
> component instance, unmounting the old one and mounting a fresh one with
> reset state — no effect, no bug where one field resets but another
> doesn't.

```jsx
// bad — effect manually resets each field when userId changes
function EditProfile({ userId, initialName }) {
  const [name, setName] = useState(initialName)
  useEffect(() => {
    setName(initialName)
  }, [userId, initialName])
}
```

```jsx
// good — parent remounts the form per user via key
function EditProfile({ initialName }) {
  const [name, setName] = useState(initialName)
  return <input value={name} onChange={(e) => setName(e.target.value)} />
}

// good — usage
<EditProfile key={userId} initialName={user.name} />
```

## 18.5 Do not use an effect to adjust some state when another prop/state changes if it can be computed during render instead.

> Why? "Adjusting state in response to a prop change" inside an effect
> introduces an extra render (state starts stale, effect runs, state
> updates, re-render) where a direct render-time computation would show the
> right value immediately.

```jsx
// bad
function List({ items }) {
  const [selection, setSelection] = useState(null)
  useEffect(() => {
    if (!items.includes(selection)) setSelection(null)
  }, [items, selection])
}
```

```jsx
// good — clamp during render; only call setSelection from the actual event that changes it
function List({ items }) {
  const [selection, setSelection] = useState(null)
  const validSelection = items.includes(selection) ? selection : null
}
```

## 18.6 In a framework that supports Server Components or route loaders, fetch data there — do not fetch inside a `useEffect` + `useState` pair on the client when a server-side alternative exists.

> Why? An effect-driven client fetch means: render with no data → commit →
> effect fires → request goes out → response arrives → re-render. That is
> strictly worse for time-to-content and SEO than fetching before the first
> paint on the server. See §36 and §38.

```jsx
// bad — client-only waterfall
function UserPage({ userId }) {
  const [user, setUser] = useState(null)
  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then(setUser)
  }, [userId])
  if (!user) return <Spinner />
  return <div>{user.name}</div>
}
```

```tsx
// good — Server Component fetches before the client ever sees a loading state
async function UserPage({ userId }: { userId: string }) {
  const user = await getUser(userId)
  return <div>{user.name}</div>
}
```

## 18.7 When a client-side effect fetch is genuinely necessary, always guard against race conditions with either `AbortController` or an `ignore` flag.

> Why? If `userId` changes quickly (e.g. fast navigation), an earlier,
> slower request can resolve *after* a later one and overwrite fresher data
> with stale data. Both patterns below prevent that.

```jsx
// bad — no protection against out-of-order responses
function UserProfile({ userId }) {
  const [user, setUser] = useState(null)
  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then(setUser)
  }, [userId])
  return <div>{user?.name}</div>
}
```

```jsx
// good — AbortController cancels the stale request outright
function UserProfile({ userId }) {
  const [user, setUser] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    fetch(`/api/users/${userId}`, { signal: controller.signal })
      .then((res) => res.json())
      .then(setUser)
      .catch((error) => {
        if (error.name !== 'AbortError') throw error
      })
    return () => controller.abort()
  }, [userId])

  return <div>{user?.name}</div>
}

// good — ignore flag when the API has no cancellation support
function UserProfile({ userId }) {
  const [user, setUser] = useState(null)

  useEffect(() => {
    let ignore = false
    fetchUser(userId).then((data) => {
      if (!ignore) setUser(data)
    })
    return () => {
      ignore = true
    }
  }, [userId])

  return <div>{user?.name}</div>
}
```

## 18.8 Never pass an `async` function directly as the effect callback; `useEffect` requires its callback to return either nothing or a cleanup function, and a Promise is neither.

> Why? `useEffect(async () => {...})` returns a Promise, which React will
> try to call as a cleanup function on unmount/re-run, producing confusing
> runtime errors and a React warning about an effect callback returning a
> Promise.

```jsx
// bad — the effect callback itself is async
useEffect(async () => {
  const data = await fetchData()
  setData(data)
}, [])
```

```jsx
// good — declare the async function inside the effect and call it
useEffect(() => {
  async function load() {
    const data = await fetchData()
    setData(data)
  }
  load()
}, [])
```

## 18.9 Always return a cleanup function from an effect that subscribes, opens a connection, starts a timer, or adds a listener.

> Why? Without cleanup, every remount (including React 18 Strict Mode's
> deliberate mount→unmount→mount in development) leaks the previous
> subscription/timer/listener, compounding with every re-render.

```jsx
// bad — no cleanup, listener accumulates on every mount
function WindowWidth() {
  const [width, setWidth] = useState(window.innerWidth)
  useEffect(() => {
    window.addEventListener('resize', () => setWidth(window.innerWidth))
  }, [])
  return <div>{width}</div>
}
```

```jsx
// good
function WindowWidth() {
  const [width, setWidth] = useState(window.innerWidth)

  useEffect(() => {
    function handleResize() {
      setWidth(window.innerWidth)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return <div>{width}</div>
}
```

## 18.10 Always list every reactive value the effect reads (props, state, and anything derived from them) in the dependency array; do not suppress `exhaustive-deps` to silence it.

> Why? A missing dependency means the effect closes over a stale value from
> a previous render — one of the most common and hardest-to-spot React
> bugs. If you're tempted to disable the lint rule, that's a signal the
> effect is doing too much or needs restructuring (e.g. using the updater
> form of `setState`, or moving a value into a ref).

```jsx
// bad — reads `roomId` but omits it from deps; suppressed lint warning
function ChatRoom({ roomId }) {
  useEffect(() => {
    const connection = createConnection(roomId)
    connection.connect()
    return () => connection.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}
```

```jsx
// good
function ChatRoom({ roomId }) {
  useEffect(() => {
    const connection = createConnection(roomId)
    connection.connect()
    return () => connection.disconnect()
  }, [roomId])
}
```

## 18.11 Do not use an effect purely to call a parent callback prop on every render or state change; call it from the event handler that caused the change.

> Why? An effect that exists only to "notify the parent" fires on every
> commit where the dependency changed, including ones caused by unrelated
> re-renders, and delays the notification by one extra commit compared to
> calling it directly in the handler.

```jsx
// bad
function Toggle({ onToggle }) {
  const [on, setOn] = useState(false)
  useEffect(() => {
    onToggle(on)
  }, [on, onToggle])
  return <button onClick={() => setOn(!on)}>Toggle</button>
}
```

```jsx
// good
function Toggle({ onToggle }) {
  const [on, setOn] = useState(false)
  function handleClick() {
    const next = !on
    setOn(next)
    onToggle(next)
  }
  return <button onClick={handleClick}>Toggle</button>
}
```

## 18.12 Do not chain effects that each set state to trigger the next effect ("effect chains"); consolidate the logic into one event handler or one effect.

> Why? A chain of effects, each triggered by the previous effect's state
> update, produces a cascade of renders and makes the actual sequence of
> operations nearly impossible to trace from the code.

```jsx
// bad — three effects chained through state, each waiting on the last
function Wizard() {
  const [step, setStep] = useState(1)
  const [cardVisible, setCardVisible] = useState(false)
  const [confirmVisible, setConfirmVisible] = useState(false)

  useEffect(() => {
    if (step === 2) setCardVisible(true)
  }, [step])

  useEffect(() => {
    if (cardVisible) setConfirmVisible(true)
  }, [cardVisible])
}
```

```jsx
// good — one handler computes the whole next state
function Wizard() {
  const [step, setStep] = useState(1)

  function handleNext() {
    setStep(2)
  }

  const cardVisible = step >= 2
  const confirmVisible = step >= 2
}
```

## 18.13 Split unrelated concerns into separate effects rather than one effect with an `if`/`else` per concern.

> Why? One effect per concern keeps each effect's dependency array minimal
> and honest; a combined effect tends to accumulate dependencies that only
> matter to one branch, causing it to re-run for unrelated reasons.

```jsx
// bad — one effect, two unrelated jobs
useEffect(() => {
  document.title = title
  const id = setInterval(tick, 1000)
  return () => clearInterval(id)
}, [title, tick])
```

```jsx
// good
useEffect(() => {
  document.title = title
}, [title])

useEffect(() => {
  const id = setInterval(tick, 1000)
  return () => clearInterval(id)
}, [tick])
```

## 18.14 Do not fetch inside an effect just to compute a value that could be sent from the server or derived from props already available — check https://react.dev/learn/you-might-not-need-an-effect before adding any new effect.

> Why? The React docs maintain a canonical list of "effect smells":
> resetting state on prop change, adjusting state on prop change,
> sharing logic between event handlers via an effect, chains of effects to
> compute derived state, sending POST requests on mount that belong in an
> event handler, and notifying parents from an effect. Every one of these
> has a non-effect fix, shown throughout this section.

```jsx
// bad — POST on mount, modeled as "sync with server" when it's really a one-time action
function Analytics({ event }) {
  useEffect(() => {
    fetch('/api/track', { method: 'POST', body: JSON.stringify(event) })
  }, [event])
}
```

```jsx
// good — fire it from the action that actually produced the event
function useTrackedClick(event) {
  return function handleClick() {
    fetch('/api/track', { method: 'POST', body: JSON.stringify(event) })
  }
}
```
