<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 16. useState

## 16.1 Split state into the smallest independently-updatable pieces; do not default to one big state object.

> Why? Separate `useState` calls make each update trivial (`setName(x)`
> instead of `setState((s) => ({ ...s, name: x }))`) and avoid accidental
> loss of sibling fields when an update forgets to spread.

```jsx
// bad
function Form() {
  const [state, setState] = useState({ name: '', email: '' })
  return (
    <input
      value={state.name}
      onChange={(e) => setState({ ...state, name: e.target.value })}
    />
  )
}
```

```jsx
// good
function Form() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  return <input value={name} onChange={(e) => setName(e.target.value)} />
}
```

Keep fields together in one state object only when they are always read and
written together (e.g. `{ x, y }` coordinates, or fields tied to one
reducer — see §17).

## 16.2 Use the updater-function form of `setState` whenever the next state depends on the previous state.

> Why? State updates inside the same event/batch can be stale if you read
> the outer `count` variable directly; the updater form always receives the
> latest pending value, which matters for double-invocations (Strict Mode)
> and multiple updates in one handler.

```jsx
// bad — reads a possibly-stale `count` from closure
function Counter() {
  const [count, setCount] = useState(0)
  function handleTripleClick() {
    setCount(count + 1)
    setCount(count + 1)
    setCount(count + 1)
  }
  return <button onClick={handleTripleClick}>{count}</button>
}
```

```jsx
// good
function Counter() {
  const [count, setCount] = useState(0)
  function handleTripleClick() {
    setCount((c) => c + 1)
    setCount((c) => c + 1)
    setCount((c) => c + 1)
  }
  return <button onClick={handleTripleClick}>{count}</button>
}
```

## 16.3 Pass a function (lazy initializer) to `useState` when the initial value is expensive to compute; never call the expensive function inline as the argument.

> Why? `useState(expensiveCall())` invokes `expensiveCall` on **every**
> render, even though the result is thrown away after the first. Passing a
> function defers the call to mount only.

```jsx
// bad — parses on every render
function Table({ raw }) {
  const [rows, setRows] = useState(parseHugeCsv(raw))
}
```

```jsx
// good — parses once, at mount
function Table({ raw }) {
  const [rows, setRows] = useState(() => parseHugeCsv(raw))
}
```

## 16.4 Do not mirror props into state unless you are intentionally freezing a value at a point in time; prefer deriving values from props during render.

> Why? Props-to-state mirroring is one of the most common sources of "my
> component doesn't update when props change" bugs, because the mirrored
> state only reflects the value at mount/prior update.

```jsx
// bad — email state goes stale if the `user` prop changes
function ProfileForm({ user }) {
  const [email, setEmail] = useState(user.email)
  return <input value={email} onChange={(e) => setEmail(e.target.value)} />
}
```

```jsx
// good — if you need to reset editable state when the user changes, key the component
function ProfileForm({ user }) {
  const [email, setEmail] = useState(user.email)
  return <input value={email} onChange={(e) => setEmail(e.target.value)} />
}

// mount a fresh instance (and fresh state) per user, instead of syncing in an effect
<ProfileForm key={user.id} user={user} />
```

## 16.5 Never mutate state directly; always create a new array/object reference.

> Why? React compares state by reference to decide whether to re-render.
> Mutating in place leaves the reference unchanged, so React may skip the
> re-render entirely, and you lose the previous value for debugging.

```jsx
// bad
function TodoList() {
  const [todos, setTodos] = useState([])
  function addTodo(todo) {
    todos.push(todo)
    setTodos(todos)
  }
}
```

```jsx
// good
function TodoList() {
  const [todos, setTodos] = useState([])
  function addTodo(todo) {
    setTodos((prev) => [...prev, todo])
  }
}
```
