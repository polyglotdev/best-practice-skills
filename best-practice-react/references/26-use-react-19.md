<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 26. use() (React 19)

## 26.1 Use the `use()` API to read a Promise or context conditionally — inside `if` statements, loops, or after early returns — where `useContext`/effects could not.

> Why? Unlike other hooks, `use()` is explicitly allowed to be called
> conditionally, because React tracks it differently (via Suspense
> integration rather than call-order state). This is the one exception to
> §15's top-level rule, and only applies to `use()`.

```jsx
// good — conditional use() call, valid in React 19+
function Message({ messagePromise, show }) {
  if (!show) return null
  const message = use(messagePromise)
  return <p>{message}</p>
}
```

## 26.2 Prefer `use()` over `useEffect` + `useState` for consuming a Promise that a Server Component or a framework loader already created; pair it with `<Suspense>` for the loading state.

> Why? `use()` integrates with Suspense so the loading UI is declared once
> at the boundary, instead of manually tracked with `isLoading` state per
> component.

```jsx
// bad
function Comments({ commentsPromise }) {
  const [comments, setComments] = useState(null)
  useEffect(() => {
    commentsPromise.then(setComments)
  }, [commentsPromise])
  if (!comments) return <Spinner />
  return <CommentList comments={comments} />
}
```

```jsx
// good
function Comments({ commentsPromise }) {
  const comments = use(commentsPromise)
  return <CommentList comments={comments} />
}

// good — usage, loading state owned by Suspense
<Suspense fallback={<Spinner />}>
  <Comments commentsPromise={commentsPromise} />
</Suspense>
```

## 26.3 Do not create a new Promise inline on every render and pass it to `use()`; the Promise must be created once (in a Server Component, a cache, or a ref) and remain stable across renders.

> Why? A fresh Promise every render re-triggers Suspense every render,
> producing an infinite loading loop instead of a resolved value.

```jsx
// bad — new Promise created on every render
function Comments({ postId }) {
  const comments = use(fetchComments(postId))
  return <CommentList comments={comments} />
}
```

```jsx
// good — Promise created once, upstream (e.g. in a Server Component or a cache), and passed down
function Comments({ commentsPromise }) {
  const comments = use(commentsPromise)
  return <CommentList comments={comments} />
}
```
