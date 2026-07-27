<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 2. Function Components

Function components + hooks are the default and near-universal way to write
React in 2026. Class components are legacy except for Error Boundaries
(§32), which still require a class today.

## 2.1 Always write function components as named `function` declarations, not arrow functions assigned to `const`, for top-level components.

> Why? Named function declarations are hoisted, produce a real `name` for
> debugging/DevTools/error stacks without relying on inference, and read
> like a declaration ("this file declares a component") rather than an
> expression.

```jsx
// bad — relies on inferred name, hurts hoisting, harder to spot in a diff
const Listing = ({ hello }) => {
  return <div>{hello}</div>
}
```

```jsx
// good
function Listing({ hello }) {
  return <div>{hello}</div>
}
```

Arrow functions remain correct for inline callbacks, small local helpers
inside a hook body, and higher-order-component factories — see §13 and §27.

## 2.2 Never use `React.FC` / `React.FunctionComponent`.

> Why? `React.FC` implicitly types `children` (wrongly, and differently
> across React/@types versions), makes generic components awkward, and
> provides no benefit over typing props directly. The React/TypeScript
> community, including the official React TypeScript cheatsheet, no longer
> recommends it.

```tsx
// bad
import { FC } from 'react'

const UserCard: FC<{ name: string }> = ({ name }) => {
  return <div>{name}</div>
}
```

```tsx
// good — type the props, return type is inferred as JSX.Element
type UserCardProps = {
  name: string
}

function UserCard({ name }: UserCardProps) {
  return <div>{name}</div>
}
```

## 2.3 Name the props type `<ComponentName>Props` and colocate it directly above the component.

> Why? A predictable naming convention makes props types easy to find,
> import (`import type { UserCardProps } from './UserCard'`), and extend.

```tsx
// bad — anonymous inline type, no reusable name
function UserCard({ name, onSelect }: { name: string, onSelect: () => void }) {
  return <button onClick={onSelect}>{name}</button>
}
```

```tsx
// good
type UserCardProps = {
  name: string
  onSelect: () => void
}

function UserCard({ name, onSelect }: UserCardProps) {
  return <button onClick={onSelect}>{name}</button>
}
```

## 2.4 In plain JS files, document props with JSDoc `@typedef` instead of `PropTypes`.

> Why? JSDoc typedefs give editor autocomplete and can be checked by `tsc
> --checkJs` without adopting TypeScript syntax, and stay accurate as the
> component evolves — unlike comments.

```jsx
// bad — no type information at all
function UserCard({ name, age }) {
  return (
    <div>
      {name} ({age})
    </div>
  )
}
```

```jsx
// good
/**
 * @typedef {object} UserCardProps
 * @property {string} name
 * @property {number} [age]
 */

/**
 * @param {UserCardProps} props
 */
function UserCard({ name, age }) {
  return (
    <div>
      {name} ({age})
    </div>
  )
}
```

## 2.5 Destructure props in the function signature, not inside the body.

> Why? Destructuring in the signature documents the component's contract at
> the call site you're most likely to read first, and avoids an extra line
> before any logic.

```jsx
// bad
function UserCard(props) {
  const { name, age } = props
  return (
    <div>
      {name} ({age})
    </div>
  )
}
```

```jsx
// good
function UserCard({ name, age }) {
  return (
    <div>
      {name} ({age})
    </div>
  )
}
```
