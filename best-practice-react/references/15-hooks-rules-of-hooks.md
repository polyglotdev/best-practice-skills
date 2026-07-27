<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 15. Hooks — Rules of Hooks

## 15.1 Only call hooks at the top level of a function component or custom hook; never inside loops, conditions, or nested functions.

> Why? React matches hooks to state by **call order**, not by name. A hook
> called conditionally shifts every subsequent hook's slot on renders where
> the condition differs, silently corrupting state. This is enforced by the
> `eslint-plugin-react-hooks` `rules-of-hooks` rule — treat any violation as
> a build-breaking error, not a warning.

```jsx
// bad — hook called conditionally
function Profile({ userId }) {
  if (!userId) return null
  const [name, setName] = useState('')
  return <div>{name}</div>
}
```

```jsx
// good — hook always runs; the condition moves after the hook
function Profile({ userId }) {
  const [name, setName] = useState('')
  if (!userId) return null
  return <div>{name}</div>
}
```

## 15.2 Only call hooks from React function components or from custom hooks (functions whose name starts with `use`).

> Why? Hooks rely on React's internal render dispatcher, which is only set
> up while rendering a component or executing another hook. Calling a hook
> from a plain utility function is a silent contract violation the linter
> can only catch if the function is named `useXxx`.

```js
// bad — hook called from a non-hook, non-component function
function getUserLabel() {
  const [locale] = useState('en')
  return locale
}
```

```js
// good — either make it a proper hook…
function useUserLabel() {
  const [locale] = useState('en')
  return locale
}

// …or call the hook where a component actually renders
function UserBadge() {
  const [locale] = useState('en')
  return <span>{locale}</span>
}
```

## 15.3 Call hooks in the same order on every render — do not early-return above a hook call.

> Why? Same underlying reason as 15.1: hook order must be stable across
> renders of the same component instance.

```jsx
// bad
function Panel({ isOpen }) {
  if (!isOpen) return null
  const ref = useRef(null)
  return <div ref={ref} />
}
```

```jsx
// good
function Panel({ isOpen }) {
  const ref = useRef(null)
  if (!isOpen) return null
  return <div ref={ref} />
}
```

## 15.4 Enable `eslint-plugin-react-hooks` and treat `rules-of-hooks` and `exhaustive-deps` as errors, not warnings.

> Why? Both rules catch real bugs — stale closures and corrupted hook state
> — that are otherwise invisible until a specific, hard-to-reproduce user
> interaction triggers them.

```json
// good — eslint config excerpt
{
  "rules": {
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "error"
  }
}
```
