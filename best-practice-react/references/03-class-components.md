<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 3. Class Components

Class components exist in this codebase only where React has no function
equivalent — today that means **Error Boundaries** (§32). Do not write new
class components for anything else: no local-state class components, no
class-based data fetching, no class-based lifecycle logic.

## 3.1 If you must write a class (Error Boundary only), keep it minimal and isolated.

> Why? Concentrating the one remaining legitimate class-component use case
> in a single small file keeps the rest of the codebase hook-only and
> avoids "class creep" where contributors copy the pattern for unrelated
> components.

```tsx
// bad — a class component used for ordinary UI + state, no boundary need
class Counter extends React.Component {
  state = { count: 0 }

  render() {
    return <button onClick={() => this.setState({ count: this.state.count + 1 })}>{this.state.count}</button>
  }
}
```

```tsx
// good — function + hook
function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount((c) => c + 1)}>{count}</button>
}

// good — class reserved strictly for the one job classes still do
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) return this.props.fallback
    return this.props.children
  }
}
```

## 3.2 Never use `React.createClass` or mixins.

> Why? Both were removed from React years ago (`createClass` requires the
> unmaintained `create-react-class` package) and mixins caused implicit
> dependency and name-clash bugs that motivated hooks and HOCs in the first
> place. See §43.

```jsx
// bad
const Listing = React.createClass({
  render() {
    return <div>{this.state.hello}</div>
  }
})
```

```jsx
// good
function Listing({ hello }) {
  return <div>{hello}</div>
}
```
