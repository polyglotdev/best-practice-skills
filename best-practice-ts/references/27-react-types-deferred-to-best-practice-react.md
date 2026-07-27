<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 27. React Types (deferred to best-practice-react)

Detailed component and hook typing conventions live in `best-practice-react`.
Load that skill for JSX-heavy work. This section covers only the small
type-level surface that belongs to the type-system layer itself.

## 27.1 Type a component's DOM-forwarding props with `React.ComponentPropsWithoutRef<'tag'>` instead of hand-listing the HTML attributes you want to forward.

```ts
// bad
type ButtonProps = {
  onClick?: () => void
  className?: string
  disabled?: boolean
}

// good
type ButtonProps = React.ComponentPropsWithoutRef<'button'>
```

## 27.2 Type children and other renderable values as `React.ReactNode`, not `JSX.Element` or `any`.

> Why? `ReactNode` correctly includes strings, numbers, fragments, arrays,
> and `null`/`undefined` — everything React can actually render — while
> `JSX.Element` excludes most of those valid cases.

```ts
// bad
type CardProps = { children: JSX.Element }

// good
type CardProps = { children: React.ReactNode }
```

## 27.3 Type a `forwardRef` component with the element type as the first generic argument and the props type as the second.

```ts
// good
const Input = React.forwardRef<HTMLInputElement, React.ComponentPropsWithoutRef<'input'>>(
  (props, ref) => <input ref={ref} {...props} />
)
```
