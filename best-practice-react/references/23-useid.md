<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 23. useId

## 23.1 Use `useId` to generate unique ids for accessibility attributes (`htmlFor`/`id`, `aria-describedby`); never hand-roll ids with `Math.random()` or a module-level counter.

> Why? `useId` produces stable ids that match between server and client
> renders, avoiding hydration mismatches. `Math.random()` produces a
> different value on the server than the client, guaranteed to mismatch.

```jsx
// bad — random id causes a hydration mismatch and isn't stable across renders
function TextField({ label }) {
  const id = `field-${Math.random()}`
  return (
    <>
      <label htmlFor={id}>{label}</label>
      <input id={id} />
    </>
  )
}
```

```jsx
// good
function TextField({ label }) {
  const id = useId()
  return (
    <>
      <label htmlFor={id}>{label}</label>
      <input id={id} />
    </>
  )
}
```

## 23.2 Do not use `useId` to generate list keys.

> Why? `useId` generates one stable id per component instance, not per
> list item, and is not intended to model data identity — see §28 for the
> correct source of keys.

```jsx
// bad
function Item({ label }) {
  const id = useId()
  return <li key={id}>{label}</li>
}
```

```jsx
// good — key comes from the data itself, assigned by the parent's map
function ItemList({ items }) {
  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>{item.label}</li>
      ))}
    </ul>
  )
}
```
