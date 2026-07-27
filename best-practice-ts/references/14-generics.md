<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 14. Generics

## 14.1 Name generic type parameters descriptively once there is more than one; reserve single letters (`T`, `K`, `V`) for the single-obvious-parameter case.

> Why? `T`/`U`/`V` are fine when there is exactly one type parameter and its
> role is self-evident from context; beyond that, unclear letters force
> readers to trace usage to figure out what each parameter represents.

```ts
// bad
function merge<T, U, V>(a: T, b: U, c: V): T & U & V {
  return { ...a, ...b, ...c }
}

// good
function merge<TFirst, TSecond, TThird>(
  a: TFirst,
  b: TSecond,
  c: TThird
): TFirst & TSecond & TThird {
  return { ...a, ...b, ...c }
}
```

## 14.2 Constrain generics with `extends` instead of accepting `any`/`unknown` and casting inside the function body.

> Why? A constraint documents and enforces the actual shape the function
> needs, and lets the compiler check the function body against that shape
> instead of trusting an internal cast.

```ts
// bad
function getId(entity: any) {
  return entity.id
}

// good
function getId<TEntity extends { id: string }>(entity: TEntity): string {
  return entity.id
}
```

## 14.3 Do not introduce a generic parameter that is used only once; it adds no type safety over hardcoding the concrete type.

> Why? A type parameter earns its complexity by relating two or more
> positions (e.g. a parameter and the return type). If it appears once, it
> is not preserving any information the caller could not already infer.

```ts
// bad — T isn't used to relate anything
function logAndReturn<T>(value: T): void {
  console.log(value)
}

// good
function logAndReturn(value: unknown): void {
  console.log(value)
}
```

## 14.4 Use `const` type parameters (TS 5.0+) when a generic function should infer literal types from its argument without the caller writing `as const`.

> Why? `const T` applies `as const`-style inference to the argument
> automatically, so callers get literal-type inference for free instead of
> having to remember to annotate every call site.

```ts
// bad — callers must remember `as const` or lose literal inference
function first<T>(arr: readonly T[]): T {
  return arr[0]
}
const dir = first(['left', 'right']) // string, not 'left' | 'right'

// good
function first<const T>(arr: readonly T[]): T {
  return arr[0]
}
const dir = first(['left', 'right']) // 'left' | 'right'
```

## 14.5 Use `NoInfer<T>` (TS 5.4+) to block inference from a parameter that should only accept, not drive, a type argument.

> Why? Without `NoInfer`, TypeScript infers the type parameter from *every*
> position it appears in, including a "default value" argument that should
> instead be validated against a type inferred elsewhere.

```ts
// bad — default's type leaks into inference, widening TValue unexpectedly
function withDefault<TValue>(value: TValue | undefined, fallback: TValue): TValue {
  return value ?? fallback
}
withDefault('active' as const, 'unknown') // TValue widens to string

// good
function withDefault<TValue>(
  value: TValue | undefined,
  fallback: NoInfer<TValue>
): TValue {
  return value ?? fallback
}
```

## 14.6 Provide sensible generic defaults (`<T = Default>`) for generics that are usually, but not always, a specific type.

> Why? A default keeps the common call site simple while still allowing the
> uncommon case to override it explicitly.

```ts
// good
type ApiResponse<TData = unknown> = {
  data: TData
  status: number
}
```
