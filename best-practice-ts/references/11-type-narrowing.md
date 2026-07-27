<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 11. Type Narrowing

## 11.1 Use `typeof` guards for primitives, `instanceof` for class instances, and `in` for distinguishing object shapes by property presence.

> Why? Each operator narrows correctly for its own category; using the
> wrong one either fails to narrow or throws at runtime (e.g. `instanceof`
> on a non-constructor).

```ts
// good
function describe(value: string | number | Date): string {
  if (typeof value === 'string') return value.toUpperCase()
  if (typeof value === 'number') return value.toFixed(2)
  if (value instanceof Date) return value.toISOString()
  return assertNever(value)
}

function area(shape: { kind: 'circle'; r: number } | { w: number; h: number }) {
  if ('kind' in shape) return Math.PI * shape.r ** 2
  return shape.w * shape.h
}
```

## 11.2 Write user-defined type guards (`value is T`) for reusable narrowing logic that spans more than a single call site.

> Why? A named type guard documents the check's intent and lets every call
> site narrow consistently, instead of duplicating the same structural
> check inline everywhere it is needed.

```ts
// bad
if (typeof err === 'object' && err !== null && 'message' in err) {
  console.log((err as { message: string }).message)
}

// good
function isErrorWithMessage(err: unknown): err is { message: string } {
  return (
    typeof err === 'object' &&
    err !== null &&
    'message' in err &&
    typeof (err as { message: unknown }).message === 'string'
  )
}

if (isErrorWithMessage(err)) {
  console.log(err.message)
}
```

## 11.3 Use assertion functions (`asserts value is T` / `asserts condition`) for guards that throw rather than return a boolean.

> Why? An assertion function narrows the type for every line *after* the
> call in the same scope, which a boolean-returning guard cannot do without
> an `if` wrapper.

```ts
// good
function assertIsUser(value: unknown): asserts value is User {
  if (typeof value !== 'object' || value === null || !('id' in value)) {
    throw new Error('Not a User')
  }
}

function handle(value: unknown) {
  assertIsUser(value)
  console.log(value.id) // value is narrowed to User here
}
```

## 11.4 Prefer control-flow narrowing (early return / early throw) over nested conditionals to keep the narrowed type alive for the rest of the function.

> Why? An early return lets TypeScript carry the narrowed type through the
> remainder of the function body without an extra indentation level, and
> matches the "guard clause" style already required by `best-practice-js`.

```ts
// bad
function greet(name: string | null) {
  if (name !== null) {
    return `Hello, ${name}`
  } else {
    return 'Hello, stranger'
  }
}

// good
function greet(name: string | null) {
  if (name === null) return 'Hello, stranger'
  return `Hello, ${name}`
}
```
