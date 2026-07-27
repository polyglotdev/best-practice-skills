<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 43. Modernization Notes (what Airbnb React says that is now outdated)

This section is a delta against Airbnb's original React style guide, which
predates hooks, Server Components, and React 19. Where Airbnb's guide
assumes Class Components as the default, treat the notes below as the
current replacement.

## 43.1 Class components → function components + hooks.

Airbnb's guide is written class-component-first: lifecycle methods,
`this.state`, `this.setState`. All of that is obsolete for new code.
Function components with hooks are the only style used in this guide,
covered in §2 and §15-27. The **single** remaining exception is Error
Boundaries (§32), which still require a class because React has no hook
equivalent for `getDerivedStateFromError`/`componentDidCatch`.

## 43.2 `React.createClass` and mixins → obsolete.

`React.createClass` was removed from React itself years ago; ES6 classes
replaced it, and classes themselves are now mostly replaced by function
components. Mixins — the original mechanism for sharing behavior across
components — are replaced by composition, custom hooks (§27), and,
where a wrapping component is truly needed, HOCs (§43.10).

## 43.3 `isMounted()` → deprecated; use effect cleanup and `AbortController` instead.

`isMounted()` was a workaround for calling `setState` after a component
had already unmounted. The modern fix is to cancel the underlying work
in an effect's cleanup function or via `AbortController`, so the
callback that would call `setState` never fires after unmount at all —
see §18.7 and §18.9.

## 43.4 `PropTypes` → superseded by TypeScript for typed projects; JSDoc + `checkJs` for JS-only projects.

`PropTypes` provided only runtime prop-shape checking with no
compile-time guarantees and no editor autocomplete. TypeScript (covered
in `best-practice-ts`) checks the same contract at compile time with
full tooling support. For codebases that must stay in plain JavaScript,
JSDoc annotations combined with `checkJs` in `tsconfig.json`/`jsconfig.json`
get a comparable level of static checking without introducing `.tsx`.

## 43.5 String refs (`ref="input"`) → banned; use `useRef` or a callback ref.

String refs were already deprecated under Airbnb's own original guide,
and remain fully removed as a viable pattern today. `useRef` (§20) is
the standard replacement for function components; callback refs remain
useful when a component needs to run code exactly when the ref attaches
or detaches.

## 43.6 Binding methods in the constructor → obsolete; hooks and closures replace it entirely.

Airbnb's guide spends real estate on `this.foo = this.foo.bind(this)` in
class constructors, working around `this` losing its binding when a
method is passed as a callback. Function components have no `this` at
all — an inner function declared in the component body already closes
over the right values, so the entire category of bug (and the
boilerplate to prevent it) disappears.

## 43.7 `displayName` for HOCs → still useful; set it on the wrapping component for better DevTools output.

Unlike most of Airbnb's class-era advice, this one recommendation is
still valid where HOCs remain in use: without a `displayName`, a HOC-
wrapped component shows up in React DevTools as an unhelpful anonymous
name, making the component tree harder to read.

```jsx
// good
function withLogging(Component) {
  function WithLogging(props) {
    return <Component {...props} />
  }
  WithLogging.displayName = `withLogging(${Component.displayName || Component.name})`
  return WithLogging
}
```

## 43.8 Life-cycle methods (`componentDidMount`, `componentDidUpdate`, `componentWillUnmount`) → replaced by `useEffect`.

These three methods, central to Airbnb's original guide, map onto a
single `useEffect` hook (mount+update behavior in the effect body,
unmount behavior in its returned cleanup function) — see §18 for the
full treatment, including the many cases where no effect is needed at
all where a class-era instinct would have reached for
`componentDidUpdate`.

## 43.9 `getDerivedStateFromProps` → replaced by computing during render, or resetting via `key`.

Airbnb's guide covers this static class method for deriving state from
incoming props. The function-component equivalent is almost always to
skip the derived state entirely and compute the value directly during
render (§18.1, §18.5), or, when the intent was really "start fresh for
this prop," to reset via a changing `key` (§18.4) instead of copying
props into state at all.

## 43.10 HOCs (`withX(Component)`) → mostly replaced by custom hooks; still legitimate for injecting cross-cutting props.

Most HOC use cases from the class era (injecting data, injecting
behavior) are better served by a custom hook today, since a hook avoids
the extra wrapper component in the tree and the prop-name collisions
HOCs are prone to. HOCs remain a reasonable choice specifically when you
need to inject props from outside the component's own render (e.g. a
router library wrapping a component with route params) rather than
inside it.

## 43.11 Render props → still valid, but rarely the first choice now that hooks cover most of the same use cases.

The render-prop pattern (a component that takes a function as a prop
and calls it with internal state) predates hooks and was the primary
non-HOC way to share stateful logic. A custom hook usually expresses the
same sharing with less nesting and better composability; render props
remain a reasonable choice when the shared logic must control exactly
where/how its output renders (e.g. a `<Draggable>` wrapper) in a way a
hook alone can't.

## 43.12 `React.Children` utilities → still available, but rarely needed with modern composition patterns.

`React.Children.map`/`.forEach`/`.count` exist for manipulating
`props.children` generically, which was more common in the class era's
component-library patterns. Modern composition (passing explicit named
props/slots instead of relying on opaque children traversal) needs these
utilities far less often; reach for them only when building a genuinely
generic layout/composition primitive.
