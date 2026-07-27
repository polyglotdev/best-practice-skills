<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 15. Utility Types

## 15.1 Use `Partial<T>` for update/patch payloads where every field is individually optional.

> Why? `Partial` expresses "any subset of `T`'s fields" without hand-listing
> every field as optional, and stays in sync automatically as `T` changes.

```ts
// good
function updateUser(id: string, patch: Partial<User>): Promise<User> {
  return api.patch(`/users/${id}`, patch)
}
```

## 15.2 Use `Required<T>` when a type with optional fields must be fully populated at a specific point, such as after applying all defaults.

> Why? `Required` documents that a previously-optional shape now has every
> field guaranteed, which downstream code can rely on without further
> guards.

```ts
// good
type UserInput = { name?: string; role?: string }
function withDefaults(input: UserInput): Required<UserInput> {
  return { name: input.name ?? 'Anonymous', role: input.role ?? 'viewer' }
}
```

## 15.3 Use `Readonly<T>` for values handed to consumers who must not mutate them (see also 13.3).

```ts
// good
function freeze<T extends object>(value: T): Readonly<T> {
  return Object.freeze(value)
}
```

## 15.4 Use `Pick<T, K>` to select a known subset of fields, and `Omit<T, K>` to exclude a known subset — prefer `Omit` when the excluded set is smaller than the included set.

> Why? Whichever list is shorter communicates intent more directly and is
> less likely to need updating when `T` grows new fields.

```ts
// good
type UserCredentials = Pick<User, 'email' | 'passwordHash'>
type PublicUser = Omit<User, 'passwordHash'>
```

## 15.5 Use `Record<K, V>` to build map types and to enforce exhaustive lookup tables (see 8.4).

```ts
// good
type FeatureFlags = Record<'darkMode' | 'betaBanner', boolean>
```

## 15.6 Use `Awaited<T>` to unwrap the resolved type of a `Promise` in a generic helper, especially through nested promises.

> Why? `Awaited` correctly unwraps `Promise<Promise<T>>` to `T` in one step,
> matching how `await` actually behaves, which manual unwrapping does not
> handle correctly for nested promises.

```ts
// good
async function firstResolved<T>(promises: Promise<T>[]): Promise<Awaited<T>> {
  return Promise.race(promises)
}
```

## 15.7 Use `NonNullable<T>` to strip `null`/`undefined` from a type derived from another generic, rather than re-declaring the union manually.

```ts
// good
function compact<T>(items: T[]): NonNullable<T>[] {
  return items.filter((item): item is NonNullable<T> => item != null)
}
```

## 15.8 Use `Parameters<T>` and `ReturnType<T>` to derive types from an existing function instead of duplicating its signature.

> Why? Deriving keeps the derived type in sync automatically if the source
> function's signature changes; a hand-copied signature silently drifts.

```ts
// bad
function wrap(fn: (a: string, b: number) => boolean) {
  return (a: string, b: number): boolean => fn(a, b)
}

// good
function wrap<TFn extends (...args: never[]) => unknown>(fn: TFn) {
  return (...args: Parameters<TFn>): ReturnType<TFn> => fn(...args) as ReturnType<TFn>
}
```

## 15.9 Use `Extract<T, U>` / `Exclude<T, U>` to derive sub-unions from an existing union instead of retyping the members.

```ts
// good
type Status = 'idle' | 'loading' | 'success' | 'error'
type TerminalStatus = Extract<Status, 'success' | 'error'>
type NonTerminalStatus = Exclude<Status, TerminalStatus>
```

## 15.10 Use `ConstructorParameters<T>` when a factory function must accept the exact argument list of a class constructor.

```ts
// good
class Widget {
  constructor(
    public id: string,
    public label: string
  ) {}
}

function createWidget(...args: ConstructorParameters<typeof Widget>): Widget {
  return new Widget(...args)
}
```
