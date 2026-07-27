<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 21. Enums

## 21.1 Prefer a literal string union over a numeric `enum` for closed sets of values.

> Why? Numeric enums serialize as numbers with no self-documentation, are
> not structurally compatible with plain numbers cleanly, and add a runtime
> object that a literal union does not need.

```ts
// bad
enum Status {
  Pending,
  Active,
  Archived
}

// good
type Status = 'pending' | 'active' | 'archived'
```

## 21.2 If you need an object with both keys and values at runtime (e.g. for iteration), use an `as const` object instead of `enum`.

> Why? An `as const` object is a plain JS object with zero special compiler
> behavior, works identically under `isolatedModules`, and its keys/values
> are both available for iteration without an enum's extra runtime
> artifacts.

```ts
// bad
enum Role {
  Admin = 'admin',
  Editor = 'editor'
}

// good
const Role = {
  Admin: 'admin',
  Editor: 'editor'
} as const
type Role = (typeof Role)[keyof typeof Role]
```

## 21.3 Never use `const enum`.

> Why? `const enum` requires whole-program knowledge at compile time to
> inline its values, which is fundamentally incompatible with
> `isolatedModules` (required in Chapter 1 for per-file transpilation by
> esbuild/swc/Babel) — each file must be compilable in isolation, and
> `const enum` cannot be.

```ts
// bad — fails under isolatedModules
const enum Direction {
  Up,
  Down
}

// good
const Direction = {
  Up: 'up',
  Down: 'down'
} as const
type Direction = (typeof Direction)[keyof typeof Direction]
```
