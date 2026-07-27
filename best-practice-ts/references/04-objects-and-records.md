<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 4. Objects & Records

## 4.1 Use `Record<K, V>` for objects used as maps with a known key type.

> Why? `Record` documents both the key domain and the value type in one
> place, and pairs correctly with `noUncheckedIndexedAccess` to force a
> presence check on read.

```ts
// bad
const config: { [key: string]: number } = {}

// good
const config: Record<string, number> = {}
```

## 4.2 With `noUncheckedIndexedAccess`, always guard a `Record`/index-signature read before use.

> Why? `noUncheckedIndexedAccess` types `config[key]` as `V | undefined`,
> matching what can actually happen at runtime for an arbitrary key. Skipping
> the guard reintroduces the exact class of bug the flag exists to prevent.

```ts
// bad
const limit = config[env] // number | undefined, used as number
return limit * 2

// good
const limit = config[env]
if (limit === undefined) {
  throw new Error(`No config for env: ${env}`)
}
return limit * 2
```

## 4.3 Do not access properties through an index signature using dot notation; use bracket notation, as enforced by `noPropertyAccessFromIndexSignature`.

> Why? Dot access on an index-signature type reads as if the property is
> statically known, hiding the fact that it is actually a dynamic lookup that
> can be `undefined`.

```ts
// bad
declare const env: { [key: string]: string }
console.log(env.NODE_ENV)

// good
console.log(env['NODE_ENV'])
```

## 4.4 Use `Pick`/`Omit` to derive narrower object types instead of re-declaring a subset of fields.

> Why? A hand-copied subset silently drifts from the source type when the
> source changes; a derived type stays in sync automatically.

```ts
// bad
type UserPreview = {
  id: string
  name: string
}

// good
type UserPreview = Pick<User, 'id' | 'name'>
```

## 4.5 Model "exactly one of" object shapes with a discriminated union, not with a bag of optional fields.

> Why? A bag of optional fields allows invalid combinations to type-check
> (both fields set, or neither set). A discriminated union makes invalid
> states unrepresentable — see Chapter 8.

```ts
// bad
type Notification = {
  email?: string
  sms?: string
}

// good
type Notification =
  | { channel: 'email'; email: string }
  | { channel: 'sms'; sms: string }
```
