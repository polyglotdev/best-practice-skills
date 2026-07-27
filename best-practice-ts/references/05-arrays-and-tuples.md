<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 5. Arrays & Tuples

## 5.1 Use `T[]` for simple element types and `Array<T>` when `T` itself is a union or a complex generic.

> Why? `(A | B)[]` reads ambiguously at a glance; `Array<A | B>` is
> unambiguous about what is being made into an array.

```ts
// bad
const items: string | number[] = [] // parses as string | number[]

// good
const items: Array<string | number> = []
```

## 5.2 Use tuple types for fixed-length, heterogeneous sequences; do not use a loosely-typed array.

> Why? A tuple encodes both the length and the per-position type, which
> `T[]` cannot express, and prevents accidental out-of-range access.

```ts
// bad
function useToggle(): boolean[] {
  return [false, () => {}] as any
}

// good
function useToggle(): [state: boolean, toggle: () => void] {
  let state = false
  const toggle = () => {
    state = !state
  }
  return [state, toggle]
}
```

## 5.3 Use labeled tuple elements for readability in public signatures.

> Why? Labels show up in editor tooltips and documentation, turning
> `[string, number]` into a self-describing `[name: string, age: number]`
> without changing runtime behavior.

```ts
// good
type LatLng = [lat: number, lng: number]
```

## 5.4 Use variadic tuple types to type functions that forward or concatenate a variable-length argument list.

> Why? Variadic tuples preserve the exact per-position types through
> spreads and concatenation, which a single rest parameter typed as `T[]`
> would collapse into one union type.

```ts
// bad
function concat(a: unknown[], b: unknown[]): unknown[] {
  return [...a, ...b]
}

// good
function concat<A extends unknown[], B extends unknown[]>(
  a: [...A],
  b: [...B]
): [...A, ...B] {
  return [...a, ...b]
}
const result = concat([1, 2] as const, ['a'] as const) // [1, 2, 'a']
```

## 5.5 Prefer `ReadonlyArray<T>` / `readonly T[]` for array parameters a function does not mutate.

> Why? Marking the parameter `readonly` documents non-mutation as part of
> the type and makes calling with a `readonly` array (or a tuple) legal
> without a cast.

```ts
// bad
function sum(values: number[]): number {
  return values.reduce((total, n) => total + n, 0)
}

// good
function sum(values: readonly number[]): number {
  return values.reduce((total, n) => total + n, 0)
}
```
