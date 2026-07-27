<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 10. Refs

## 10.1 Never use string refs.

> Why? String refs were removed from strict mode React, can't be composed,
> and force React to hold a name-to-instance map behind the scenes. This
> rule is unconditional and unchanged from the original Airbnb guide.

```jsx
// bad
<Foo ref="myRef" />
```

```jsx
// good
function Foo() {
  const myRef = useRef(null)
  return <div ref={myRef} />
}
```

## 10.2 Prefer `useRef` over callback refs for simple DOM/instance references; use callback refs only when you need to run code exactly when the node attaches or detaches.

> Why? `useRef` is simpler and sufficient for "give me a handle to this
> node." Callback refs are the right tool only for measuring on
> attach/detach, managing multiple dynamic refs, or reacting to a ref
> change (which `useRef` alone cannot do, since updating `.current` does
> not re-render).

```jsx
// bad — callback ref used where useRef would do
function TextInput() {
  let inputEl = null
  return (
    <input
      ref={(el) => {
        inputEl = el
      }}
    />
  )
}
```

```jsx
// good — plain useRef for a simple handle
function TextInput() {
  const inputRef = useRef(null)
  function focus() {
    inputRef.current?.focus()
  }
  return <input ref={inputRef} />
}

// good — callback ref because we need to react to attach/detach
function MeasuredBox({ onHeightChange }) {
  const callbackRef = useCallback(
    (node) => {
      if (node !== null) onHeightChange(node.getBoundingClientRect().height)
    },
    [onHeightChange]
  )
  return <div ref={callbackRef} />
}
```

## 10.3 In React 19+, accept `ref` as a normal prop; do not reach for `forwardRef` in new code targeting React 19.

> Why? React 19 made `ref` a regular prop for function components, removing
> the need for `forwardRef` entirely in new code. For libraries that must
> also support React 18, keep using `forwardRef`.

```tsx
// good — React 19+, ref is just a prop
type InputProps = {
  ref?: React.Ref<HTMLInputElement>
  label: string
}

function Input({ ref, label }: InputProps) {
  return (
    <label>
      {label}
      <input ref={ref} />
    </label>
  )
}

// good — still targeting React 18, use forwardRef
const Input18 = forwardRef<HTMLInputElement, { label: string }>(function Input18(
  { label },
  ref
) {
  return (
    <label>
      {label}
      <input ref={ref} />
    </label>
  )
})
```

## 10.4 Never read or write `ref.current` during render; only inside effects or event handlers.

> Why? Refs are mutable and not tracked by React's rendering — reading
> `.current` during render produces values that can differ between renders
> committed and ones that never commit (in Strict Mode / concurrent
> features), which is a correctness bug, not just a style nit.

```jsx
// bad — reading a ref during render
function Timer() {
  const startRef = useRef(Date.now())
  const elapsed = Date.now() - startRef.current // reads during render
  return <div>{elapsed}ms</div>
}
```

```jsx
// good — compute derived values in an effect or from state, not from a ref read at render time
function Timer() {
  const [elapsed, setElapsed] = useState(0)
  const startRef = useRef(Date.now())

  useEffect(() => {
    const id = setInterval(() => {
      setElapsed(Date.now() - startRef.current)
    }, 1000)
    return () => clearInterval(id)
  }, [])

  return <div>{elapsed}ms</div>
}
```
