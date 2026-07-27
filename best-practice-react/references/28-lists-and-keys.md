<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 28. Lists & Keys

## 28.1 Always assign a `key` when rendering an array of elements, and take it from stable, data-derived identity — never from array index for lists that can reorder, filter, or grow.

> Why? React uses `key` to match array items across renders. An
> index-based key is only "stable" as long as nothing reorders — insert an
> item at the front and every subsequent row is misidentified, causing
> stale local state (uncontrolled inputs, animations, `useState` inside
> that row) to attach to the wrong data.

```jsx
// bad
{todos.map((todo, index) => (
  <Todo {...todo} key={index} />
))}
```

```jsx
// good
{todos.map((todo) => (
  <Todo {...todo} key={todo.id} />
))}
```

## 28.2 Use array index as a key only for lists that are permanently static — never re-ordered, filtered, or mutated for the component's lifetime.

> Why? If a list genuinely never changes order or membership (e.g. a fixed
> set of legend labels rendered once), index keys are harmless and saving
> an id field is not worth inventing one.

```jsx
// good — a truly static, never-reordered list
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function WeekHeader() {
  return (
    <>
      {DAYS.map((day, index) => (
        <th key={index}>{day}</th>
      ))}
    </>
  )
}
```

## 28.3 Never use `Math.random()` or a freshly generated value as a key.

> Why? A key generated at render time is a new value every render, forcing
> React to unmount and remount the element every single time — destroying
> all internal state and defeating the purpose of keys entirely.

```jsx
// bad — new key every render, item never keeps its identity
{items.map((item) => (
  <Item key={Math.random()} {...item} />
))}
```

```jsx
// good
{items.map((item) => (
  <Item key={item.id} {...item} />
))}
```

## 28.4 Put the `key` on the outermost element returned from the `.map()` callback, not on a nested child.

> Why? React reads `key` from the direct children of the array being
> reconciled; a key placed deeper in the tree is invisible to the
> algorithm it's meant to help.

```jsx
// bad — key is on a grandchild, React never sees it
{items.map((item) => (
  <li>
    <span key={item.id}>{item.label}</span>
  </li>
))}
```

```jsx
// good
{items.map((item) => (
  <li key={item.id}>
    <span>{item.label}</span>
  </li>
))}
```

## 28.5 Extract list rows into their own named component instead of large inline JSX inside `.map()`.

> Why? A named row component is independently readable, testable, and easy
> to wrap in `React.memo` when the list is large (§42).

```jsx
// bad — large inline JSX makes the list hard to scan
function TodoList({ todos }) {
  return (
    <ul>
      {todos.map((todo) => (
        <li key={todo.id}>
          <input type="checkbox" checked={todo.done} readOnly />
          <span style={{ textDecoration: todo.done ? 'line-through' : 'none' }}>{todo.title}</span>
        </li>
      ))}
    </ul>
  )
}
```

```jsx
// good
function TodoRow({ todo }) {
  return (
    <li>
      <input type="checkbox" checked={todo.done} readOnly />
      <span style={{ textDecoration: todo.done ? 'line-through' : 'none' }}>{todo.title}</span>
    </li>
  )
}

function TodoList({ todos }) {
  return (
    <ul>
      {todos.map((todo) => (
        <TodoRow key={todo.id} todo={todo} />
      ))}
    </ul>
  )
}
```
