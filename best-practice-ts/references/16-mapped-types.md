<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 16. Mapped Types

## 16.1 Use key remapping with `as` to derive a differently-shaped type from an existing one's keys.

> Why? Key remapping lets you transform property names programmatically
> (e.g. prefixing event handler names) while keeping the mapping tied to
> the source type, so it updates automatically when the source changes.

```ts
// good
type EventHandlers<T> = {
  [K in keyof T as `on${Capitalize<string & K>}`]: (value: T[K]) => void
}

type FormEvents = EventHandlers<{ name: string; age: number }>
// { onName: (value: string) => void; onAge: (value: number) => void }
```

## 16.2 Use `-readonly` in a mapped type to strip readonly-ness deliberately, and prefer this over a manual field-by-field re-declaration.

> Why? `-readonly` derives the mutable counterpart directly from the
> readonly source, guaranteeing the field list can never drift between the
> two.

```ts
// good
type Mutable<T> = { -readonly [K in keyof T]: T[K] }
type MutableUser = Mutable<Readonly<User>>
```

## 16.3 Use `-?` in a mapped type to make every field required, mirroring `Required<T>` for custom mapped shapes.

```ts
// good
type AllRequired<T> = { [K in keyof T]-?: T[K] }
```

## 16.4 Filter keys out of a mapped type by mapping unwanted keys to `never` and re-indexing with `as`, rather than post-processing with `Omit` when the filter condition is type-driven.

> Why? A conditional key filter can select keys based on their *value
> type* (e.g. "only function-valued keys"), which `Omit`'s literal key list
> cannot express.

```ts
// good — keep only function-valued keys
type FunctionKeys<T> = {
  [K in keyof T]: T[K] extends (...args: never[]) => unknown ? K : never
}[keyof T]

type Methods<T> = Pick<T, FunctionKeys<T>>
```
