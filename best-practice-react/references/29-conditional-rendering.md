<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 29. Conditional Rendering

## 29.1 Use `&&` for a simple show/hide, and wrap the JSX in parentheses only when it spans multiple lines.

> Why? `{condition && <Thing />}` is the most direct way to express
> "render this or nothing"; parenthesizing multiline JSX prevents ASI
> pitfalls and keeps indentation clear.

```jsx
// bad
{showButton &&
<Button />
}
```

```jsx
// good
{showButton && <Button />}

// good — multiline body
{showButton && (
  <Button onClick={handleClick}>
    Continue
  </Button>
)}
```

## 29.2 Never rely on `&&` when the left-hand value can be `0`, `NaN`, or an empty string — coerce to a boolean first.

> Why? `{count && <Badge count={count} />}` renders the literal text `0`
> when `count` is `0`, because `0` is falsy but not `null`/`undefined`, and
> React renders falsy numbers (unlike `false`/`null`) as text.

```jsx
// bad — renders a stray "0" when count is 0
function Badge({ count }) {
  return <div>{count && <span>{count}</span>}</div>
}
```

```jsx
// good
function Badge({ count }) {
  return <div>{count > 0 && <span>{count}</span>}</div>
}
```

## 29.3 Use a ternary for either/or rendering; use early returns for "render nothing at all" or "render a completely different tree."

> Why? A ternary keeps two-way branching compact and inline; an early
> return avoids deeply nested ternaries when the alternative is an entire
> unrelated layout.

```jsx
// bad — nested ternaries for structurally different trees
function Page({ status }) {
  return status === 'loading' ? (
    <Spinner />
  ) : status === 'error' ? (
    <ErrorMessage />
  ) : (
    <Content />
  )
}
```

```jsx
// good — early returns for structurally distinct states
function Page({ status }) {
  if (status === 'loading') return <Spinner />
  if (status === 'error') return <ErrorMessage />
  return <Content />
}

// good — ternary is fine for a true either/or inline
function StatusDot({ isOnline }) {
  return <span>{isOnline ? 'Online' : 'Offline'}</span>
}
```

## 29.4 Extract a named boolean variable for a non-trivial condition instead of inlining the expression in JSX.

> Why? A named variable (`const canSubmit = ...`) documents intent and
> keeps the JSX free of business logic, which makes both the logic and the
> markup easier to read independently.

```jsx
// bad — unreadable inline condition
function SubmitButton({ form }) {
  return (
    <button disabled={!form.name || !form.email || form.errors.length > 0}>
      Submit
    </button>
  )
}
```

```jsx
// good
function SubmitButton({ form }) {
  const canSubmit = form.name && form.email && form.errors.length === 0
  return <button disabled={!canSubmit}>Submit</button>
}
```
