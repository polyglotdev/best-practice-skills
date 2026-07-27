<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 1. Basic Rules

## 1.1 One component per file, PascalCase filename matching the component.

> Why? One component per file keeps modules easy to locate, test, and
> tree-shake. Matching the filename to the export makes navigation
> predictable.

```jsx
// bad — MyComponents.jsx exporting two unrelated components
export function UserCard() {
  return <div>User</div>
}

export function BillingCard() {
  return <div>Billing</div>
}
```

```jsx
// good — UserCard.jsx
export function UserCard() {
  return <div>User</div>
}
```

Small, tightly-coupled presentational helpers that are never used outside
the file (e.g. a private `Row` used only inside a `Table`) may stay in the
same file. Anything importable from elsewhere gets its own file.

## 1.2 Always use JSX; do not call `React.createElement` by hand.

> Why? JSX compiles to the same calls but is far more readable and
> diffable. Hand-written `createElement` is only appropriate in the one
> entry file that bootstraps the app before any JSX transform is available
> (rare with modern tooling).

```jsx
// bad
const el = React.createElement('div', { className: 'card' }, 'Hello')
```

```jsx
// good
const el = <div className="card">Hello</div>
```

## 1.3 Do not import `React` for JSX itself; only import the hooks/APIs you use.

> Why? The modern JSX runtime (`react-jsx`, default since React 17 and in
> every current toolchain) injects the JSX factory automatically. Importing
> `React` just to satisfy JSX is dead weight.

```jsx
// bad
import React from 'react'

function Avatar({ src }) {
  return <img src={src} alt="" />
}
```

```jsx
// good
function Avatar({ src }) {
  return <img src={src} alt="" />
}

// good — only import what you actually use
import { useState } from 'react'

function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(count + 1)}>{count}</button>
}
```

## 1.4 Type component props explicitly; never rely on `PropTypes`.

> Why? `PropTypes` are runtime-only, unmaintained relative to modern
> tooling, and give no editor autocomplete. TypeScript (or JSDoc typedefs in
> plain JS) gives compile-time and editor-time safety for free. See §43 for
> the full migration rationale.

```tsx
// bad
import PropTypes from 'prop-types'

function UserCard({ name, age }) {
  return <div>{name} ({age})</div>
}

UserCard.propTypes = {
  name: PropTypes.string.isRequired,
  age: PropTypes.number
}
```

```tsx
// good
type UserCardProps = {
  name: string
  age?: number
}

function UserCard({ name, age }: UserCardProps) {
  return (
    <div>
      {name} ({age})
    </div>
  )
}
```

## 1.5 Keep components small and single-purpose; extract when a component does more than one job.

> Why? Small components are easier to test, memoize, and reuse. A component
> that fetches data, formats it, and renders three unrelated UI regions is
> three components wearing a trenchcoat.

```jsx
// bad — one giant component doing data shaping AND three UI concerns
function Dashboard({ user }) {
  const initials = user.name
    .split(' ')
    .map((part) => part[0])
    .join('')
  return (
    <div>
      <div className="avatar">{initials}</div>
      <div className="stats">{user.stats.map((s) => s.label).join(', ')}</div>
      <div className="footer">v{user.appVersion}</div>
    </div>
  )
}
```

```jsx
// good — extracted, each piece is independently testable
function Avatar({ name }) {
  const initials = name
    .split(' ')
    .map((part) => part[0])
    .join('')
  return <div className="avatar">{initials}</div>
}

function StatsBar({ stats }) {
  return <div className="stats">{stats.map((s) => s.label).join(', ')}</div>
}

function Dashboard({ user }) {
  return (
    <div>
      <Avatar name={user.name} />
      <StatsBar stats={user.stats} />
      <div className="footer">v{user.appVersion}</div>
    </div>
  )
}
```
