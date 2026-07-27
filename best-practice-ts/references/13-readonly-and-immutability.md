<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 13. Readonly & Immutability

## 13.1 Mark object type properties `readonly` when a consumer should not mutate them after construction.

> Why? `readonly` catches accidental mutation of shared state at compile
> time, which is otherwise a silent runtime bug that only manifests as
> "spooky action at a distance" in an unrelated part of the codebase.

```ts
// bad
type Point = { x: number; y: number }

// good
type Point = { readonly x: number; readonly y: number }
```

## 13.2 Use `as const` for literal object/array constants so their members are inferred as readonly literal types, not widened primitives.

> Why? Without `as const`, `{ role: 'admin' }` infers `role: string`; with
> it, `role` is the literal type `'admin'`, which is what discriminated
> unions and `satisfies` lookups (Chapter 8, 10) depend on.

```ts
// bad
const roles = ['admin', 'editor', 'viewer']
type Role = (typeof roles)[number] // string

// good
const roles = ['admin', 'editor', 'viewer'] as const
type Role = (typeof roles)[number] // 'admin' | 'editor' | 'viewer'
```

## 13.3 Use `Readonly<T>` / `ReadonlyArray<T>` / `ReadonlyMap`/`ReadonlySet` at API boundaries that hand out internal state.

> Why? Returning a mutable reference to internal state lets callers mutate
> it without your knowledge; a readonly view communicates and enforces
> "look, don't touch" through the type system.

```ts
// bad
class Store {
  private items: Item[] = []
  getItems(): Item[] {
    return this.items
  }
}

// good
class Store {
  private items: Item[] = []
  getItems(): readonly Item[] {
    return this.items
  }
}
```

## 13.4 Remember that `readonly` and `as const` are shallow; use recursive helper types (or a library like `type-fest`'s `ReadonlyDeep`) when nested mutation must also be prevented.

> Why? `readonly` only freezes the outer level — a `readonly` array of
> mutable objects still allows `arr[0].field = x`. Assuming deep immutability
> from a shallow `readonly` is a common source of "immutable" bugs.

```ts
// bad — inner object is still mutable
type Config = Readonly<{ nested: { flag: boolean } }>
const config: Config = { nested: { flag: false } }
config.nested.flag = true // allowed — no error

// good
type DeepReadonly<T> = T extends object
  ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
  : T
type Config = DeepReadonly<{ nested: { flag: boolean } }>
```
