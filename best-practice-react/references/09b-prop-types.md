<!-- Part of the `best-practice-react` skill. See SKILL.md for the index. -->

# 9b. Prop Types (superseded by TypeScript)

Airbnb's React guide dedicates a section to `prop-types` — declaring the
shape and required-ness of props, validating enum-style props, and
providing `defaultProps`. That entire mechanism is **deprecated** in React
19 and unnecessary in any modern codebase because the same guarantees are
enforced statically by TypeScript at compile time. This chapter documents
the modern replacement pattern rule by rule, so an Airbnb-style review of a
component's prop contract can still be performed against a checklist.

For general prop conventions (spread, boolean shorthand, event-handler
naming), see [`09-props.md`](./09-props.md). For the underlying TS types
themselves, load `best-practice-ts` alongside this skill.

## 9b.1 Type every component's props with a TS `type` (or `interface`) declared next to the component; do not use `PropTypes`.

> Why? `prop-types` runs at runtime, in development only, and was removed
> from React 19's public API. TS gives the same contract at compile time
> for both JS and TS callers via `.d.ts` output, in every environment.

```tsx
// bad
import PropTypes from 'prop-types'

function Avatar({ src, size }) {
  return <img src={src} width={size} height={size} />
}

Avatar.propTypes = {
  src: PropTypes.string.isRequired,
  size: PropTypes.number
}

// good
type AvatarProps = {
  src: string
  size?: number
}

function Avatar({ src, size = 32 }: AvatarProps) {
  return <img src={src} width={size} height={size} />
}
```

## 9b.2 Prefer `type` for component props; reserve `interface` for public/extendable APIs.

> Why? Component props are usually closed shapes owned by one file.
> `type` is precise, supports unions, and doesn't participate in
> declaration merging (a common source of accidental prop leaks).

```tsx
// bad
interface ButtonProps {
  label: string
  onClick(): void
}

// good
type ButtonProps = {
  label: string
  onClick: () => void
}
```

## 9b.3 Do not use `React.FC` / `React.FunctionComponent`; type props explicitly on the parameter.

> Why? `React.FC` implicitly adds `children`, blocks generic components,
> and hides the actual prop contract behind a helper. Typing the
> parameter is clearer, generic-safe, and matches React's own docs.

```tsx
// bad
const Card: React.FC<CardProps> = ({ title }) => <div>{title}</div>

// good
function Card({ title }: CardProps) {
  return <div>{title}</div>
}
```

## 9b.4 Mark optional props with `?:` and give a default in the parameter destructure — never use `defaultProps`.

> Why? `defaultProps` is deprecated on function components in React 19.
> Destructure defaults are ES2015, work with TS narrowing, and place the
> default next to the parameter it defaults.

```tsx
// bad
function Badge({ tone }: { tone?: 'info' | 'warn' | 'danger' }) {
  return <span className={tone}>·</span>
}
Badge.defaultProps = { tone: 'info' }

// good
type BadgeProps = { tone?: 'info' | 'warn' | 'danger' }

function Badge({ tone = 'info' }: BadgeProps) {
  return <span className={tone}>·</span>
}
```

## 9b.5 Model enum-like props as string literal unions, not as an `enum` and not as `string`.

> Why? A string-literal union gives autocomplete, exhaustiveness checking,
> and zero runtime cost. `enum` produces JS output and namespace baggage;
> plain `string` accepts typos silently.

```tsx
// bad
type ButtonProps = {
  variant: string
}

// bad
enum Variant {
  Primary = 'primary',
  Secondary = 'secondary'
}

// good
type ButtonProps = {
  variant: 'primary' | 'secondary' | 'ghost'
}
```

## 9b.6 Model `children` explicitly with the tightest type the component actually accepts.

> Why? `React.ReactNode` accepts anything, including `undefined` and
> booleans, which is often too loose. Prefer a specific type when the
> component actually requires, say, a single element.

```tsx
// bad
type ModalProps = {
  children: any
}

// still too loose when only one child is valid
type ModalProps = {
  children: React.ReactNode
}

// good — single element required
type ModalProps = {
  children: React.ReactElement
}

// good — render-prop children
type ListProps<T> = {
  items: T[]
  children: (item: T) => React.ReactNode
}
```

## 9b.7 Type event handlers with React's synthetic event types, not `any` and not the DOM types.

> Why? React's synthetic events wrap the native ones and carry
> `currentTarget` typed to the element. Using the DOM's `Event` type loses
> that narrowing.

```tsx
// bad
type InputProps = {
  onChange: (e: any) => void
}

// bad — DOM event, not React's
type InputProps = {
  onChange: (e: Event) => void
}

// good
type InputProps = {
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}
```

## 9b.8 Type refs with `React.RefObject<T>` / `React.Ref<T>`, and pass `HTMLElement` subclasses — not `any`.

> Why? Precise ref types prevent accessing methods that don't exist on the
> underlying element and make forwarded refs safe.

```tsx
// bad
type Props = {
  inputRef: any
}

// good
type Props = {
  inputRef: React.Ref<HTMLInputElement>
}

const Field = React.forwardRef<HTMLInputElement, { label: string }>(
  function Field({ label }, ref) {
    return (
      <label>
        {label}
        <input ref={ref} />
      </label>
    )
  }
)
```

## 9b.9 Model mutually exclusive props with a discriminated union, not with a bag of optionals and runtime asserts.

> Why? Optional props allow invalid combinations. A discriminated union
> forces callers to pick a valid variant at compile time.

```tsx
// bad
type IconProps = {
  name?: string
  src?: string // one of these must be set — TS can't tell
}

// good
type IconProps =
  | { kind: 'symbol'; name: string }
  | { kind: 'image'; src: string; alt: string }

function Icon(props: IconProps) {
  switch (props.kind) {
    case 'symbol':
      return <svg><use href={`#${props.name}`} /></svg>
    case 'image':
      return <img src={props.src} alt={props.alt} />
  }
}
```

## 9b.10 Reuse element attribute types with `ComponentPropsWithoutRef<T>` when wrapping a DOM element.

> Why? Retyping `type`, `disabled`, `aria-*`, `data-*` for every button
> wrapper is a source of drift. `ComponentPropsWithoutRef` inherits the
> full attribute set exactly.

```tsx
// bad
type ButtonProps = {
  onClick?: () => void
  disabled?: boolean
  type?: 'button' | 'submit'
  // ...forgets aria-label, data-*, name, form, etc.
}

// good
type ButtonProps = React.ComponentPropsWithoutRef<'button'> & {
  variant?: 'primary' | 'secondary'
}

function Button({ variant = 'primary', ...rest }: ButtonProps) {
  return <button data-variant={variant} {...rest} />
}
```

## 9b.11 Do not export `PropTypes` shims, `.propTypes` blocks, or `defaultProps` from any component in a new codebase.

> Why? They're dead code in React 19 and confuse readers about the source
> of truth. If you're migrating from a legacy codebase, delete them as you
> touch each component and add the TS type instead.

```jsx
// bad — legacy PropTypes still declared alongside a TS type
type CardProps = { title: string }
function Card({ title }: CardProps) { /* ... */ }
Card.propTypes = { title: PropTypes.string.isRequired }
Card.defaultProps = { title: 'Untitled' }

// good
type CardProps = { title?: string }

function Card({ title = 'Untitled' }: CardProps) {
  return <h2>{title}</h2>
}
```

## 9b.12 In a JS-only codebase without TS, use JSDoc `@typedef` and `@param` — not runtime `prop-types`.

> Why? Modern editors and `tsc --checkJs` read JSDoc as types and give the
> same red squigglies TS does, at zero runtime cost.

```jsx
// bad
Avatar.propTypes = {
  src: PropTypes.string.isRequired,
  size: PropTypes.number
}

// good
/**
 * @typedef {object} AvatarProps
 * @property {string} src
 * @property {number} [size]
 */

/** @param {AvatarProps} props */
function Avatar({ src, size = 32 }) {
  return <img src={src} width={size} height={size} />
}
```
