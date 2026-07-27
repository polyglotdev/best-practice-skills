<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 5. Declaration & Exports

## 5.1 Prefer named exports for components; reserve default exports for framework-mandated entry points (Next.js pages/layouts, lazy-loaded routes).

> Why? Named exports are renamed consistently by refactoring tools, can't
> be accidentally given a different name at each import site, and support
> multiple exports per file when that is intentional (e.g. a component plus
> its subcomponents).

```jsx
// bad
export default function UserCard({ name }) {
  return <div>{name}</div>
}
```

```jsx
// good
export function UserCard({ name }) {
  return <div>{name}</div>
}

// good — framework requires default export for a route file
export default function Page() {
  return <UserCard name="Ada" />
}
```

## 5.2 Do not use `displayName` as a substitute for naming the component by reference.

> Why? A named function/const already provides the name React DevTools and
> stack traces use. Setting `displayName` on an ordinary component is
> redundant and easy to let drift out of sync with the real name.

```jsx
// bad
const ReservationCard = () => null
ReservationCard.displayName = 'ReservationCard'
```

```jsx
// good
function ReservationCard() {
  return null
}
```

## 5.3 One default export maximum per file, and only when the framework requires it.

> Why? Mixing named and default exports freely, or having multiple default
> candidates conceptually, confuses import ergonomics and autocomplete.

```jsx
// bad — file exports two "default-like" things via re-export tricks
export default function Page() {
  return <div />
}
export default function Page2() {
  return <div />
}
```

```jsx
// good
export default function Page() {
  return <div />
}
```
