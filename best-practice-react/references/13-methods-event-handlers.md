<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 13. Methods → Event Handlers

## 13.1 Define event handlers as local functions (or `useCallback`-wrapped functions when memoization is warranted) inside the component, not as class methods bound in a constructor.

> Why? Function components have no constructor and no `this` binding
> problem. A locally scoped function or `const` arrow function closes over
> the current render's props/state without any binding ceremony.

```jsx
// bad — class-era pattern with binding
class SearchBox extends React.Component {
  constructor(props) {
    super(props)
    this.handleSubmit = this.handleSubmit.bind(this)
  }

  handleSubmit(event) {
    event.preventDefault()
    this.props.onSearch(this.state.value)
  }

  render() {
    return <form onSubmit={this.handleSubmit} />
  }
}
```

```jsx
// good
function SearchBox({ onSearch }) {
  const [value, setValue] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    onSearch(value)
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={value} onChange={(e) => setValue(e.target.value)} />
    </form>
  )
}
```

## 13.2 It is fine to create inline arrow functions in JSX to close over loop variables, but avoid it in hot lists or when passed to a memoized child.

> Why? An inline arrow function is a new function reference every render,
> which is irrelevant for a plain DOM element but defeats `React.memo` on a
> child component and can cause unnecessary re-renders in large lists. See
> §21 for `useCallback` guidance.

```jsx
// bad — recreates a handler per row AND passes it to a memoized child, defeating memoization
const MemoRow = memo(Row)

function ItemList({ items, onSelect }) {
  return (
    <ul>
      {items.map((item) => (
        <MemoRow key={item.id} item={item} onSelect={() => onSelect(item.id)} />
      ))}
    </ul>
  )
}
```

```jsx
// good — Row receives the id and a stable callback, no per-row closures
const MemoRow = memo(Row)

function ItemList({ items, onSelect }) {
  const handleSelect = useCallback((id) => onSelect(id), [onSelect])
  return (
    <ul>
      {items.map((item) => (
        <MemoRow key={item.id} item={item} id={item.id} onSelect={handleSelect} />
      ))}
    </ul>
  )
}
```

## 13.3 Do not prefix internal handler names with an underscore.

> Why? JavaScript has no real privacy for these names; an underscore
> prefix communicates a promise the language cannot keep and adds visual
> noise.

```jsx
// bad
function handleClick() {}
function _handleClick() {}
```

```jsx
// good
function handleClick() {}
```

## 13.4 Always return a value from a component function; never let it fall through to an implicit `undefined`.

> Why? A component that reaches the end of its body without returning JSX
> or `null` throws or renders nothing unexpectedly. Being explicit about
> "render nothing" (`return null`) documents intent.

```jsx
// bad
function Banner({ show, children }) {
  if (show) {
    return <div className="banner">{children}</div>
  }
}
```

```jsx
// good
function Banner({ show, children }) {
  if (!show) return null
  return <div className="banner">{children}</div>
}
```
