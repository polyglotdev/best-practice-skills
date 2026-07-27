<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 8. Discriminated Unions & Exhaustiveness

## 8.1 Give every member of a state/result/event union a shared literal discriminant field.

> Why? A shared discriminant lets `switch`/`if` narrow the entire member
> shape from a single check, which is the mechanism the rest of this chapter
> depends on.

```ts
// bad
type FetchState<T> =
  | { data: T; loading: false; error: null }
  | { data: null; loading: true; error: null }
  | { data: null; loading: false; error: Error }

// good
type FetchState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error }
```

## 8.2 Narrow discriminated unions with `switch` on the discriminant, and enforce exhaustiveness with an `assertNever` helper in `default`.

> Why? `assertNever` makes the `default` branch a compile error the moment a
> new union member is added anywhere upstream without being handled here —
> catching it at build time instead of at runtime.

```ts
// good
function assertNever(value: never): never {
  throw new Error(`Unhandled case: ${JSON.stringify(value)}`)
}

function render<T>(state: FetchState<T>): string {
  switch (state.status) {
    case 'idle':
      return 'Idle'
    case 'loading':
      return 'Loading…'
    case 'success':
      return 'Loaded'
    case 'error':
      return `Error: ${state.error.message}`
    default:
      return assertNever(state)
  }
}
```

## 8.3 Never add a catch-all `default` branch that returns a value instead of calling `assertNever`.

> Why? A value-returning `default` silently swallows unhandled new members
> instead of failing the build, defeating the entire purpose of the
> exhaustiveness check.

```ts
// bad
switch (state.status) {
  case 'idle':
    return 'Idle'
  default:
    return 'Unknown'
}

// good
switch (state.status) {
  case 'idle':
    return 'Idle'
  default:
    return assertNever(state)
}
```

## 8.4 Use `satisfies Record<Discriminant, unknown>` on a lookup table as an alternate exhaustiveness check when a `switch` is not the natural shape.

> Why? A `Record` keyed by every discriminant value fails to compile if a
> member is missing, giving the same safety as `assertNever` for
> table-driven dispatch.

```ts
// good
type Status = 'idle' | 'loading' | 'success' | 'error'

const labels = {
  idle: 'Idle',
  loading: 'Loading…',
  success: 'Loaded',
  error: 'Failed'
} satisfies Record<Status, string>
```
