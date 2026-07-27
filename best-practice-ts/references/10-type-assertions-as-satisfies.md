<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 10. Type Assertions (`as`, `!`, `satisfies`)

## 10.1 Prefer narrowing over `as`; reach for `as` only when you have information TypeScript cannot infer.

> Why? `as` is a compile-time claim with zero runtime check — it silences
> the compiler rather than proving the value's shape, and a wrong assertion
> fails at some later, harder-to-debug point.

```ts
// bad
const el = document.getElementById('app') as HTMLDivElement
el.focus() // crashes if the element does not exist or is the wrong tag

// good
const el = document.getElementById('app')
if (el instanceof HTMLDivElement) {
  el.focus()
}
```

## 10.2 Never use double assertion through `as unknown as T` outside of test fixtures or documented interop shims.

> Why? Casting through `unknown` bypasses TypeScript's assignability check
> entirely, which exists specifically to stop you from asserting between
> unrelated types by mistake.

```ts
// bad
const user = rawApiResponse as unknown as User

// good — validate instead (see Chapter 24)
const user = userSchema.parse(rawApiResponse)
```

## 10.3 Avoid the non-null assertion `!`; prefer a guard, default value, or a narrowing helper.

> Why? `!` is a promise to the compiler with no runtime backing — if the
> value actually is `null`/`undefined`, the failure surfaces later as a
> generic "cannot read property of undefined," far from the real cause.

```ts
// bad
function getUser(id: string): User {
  return cache.get(id)!
}

// good
function getUser(id: string): User {
  const user = cache.get(id)
  if (!user) {
    throw new Error(`User not found: ${id}`)
  }
  return user
}
```

## 10.4 Use `satisfies` instead of a type annotation when you want validation without widening or losing literal inference.

> Why? An annotation (`: T`) widens the expression to exactly `T`, discarding
> literal types; `satisfies` checks the expression against `T` but keeps the
> narrower inferred type, so downstream consumers still see literal keys and
> values.

```ts
// bad — annotation widens; route.path is now just `string`
const route: { path: string; method: string } = {
  path: '/users',
  method: 'GET'
}

// good — satisfies validates but keeps literal types
const route = {
  path: '/users',
  method: 'GET'
} satisfies { path: string; method: string }
```

## 10.5 Use `satisfies` for config objects to catch typos in keys while preserving the literal value types callers rely on.

> Why? Config objects are frequently consumed via their literal keys
> (`config.env === 'production'`); a plain annotation would widen `env` to
> `string` and lose that ability, while an unchecked plain object would let
> a bad key through silently.

```ts
// good
type Env = 'development' | 'staging' | 'production'

const config = {
  env: 'production',
  apiUrl: 'https://api.example.com',
  retries: 3
} satisfies { env: Env; apiUrl: string; retries: number }

// config.env is the literal 'production', not widened to string
```

## 10.6 Use `satisfies` to validate a route map or handler table against a discriminated union without losing per-key precision.

> Why? Each handler's specific parameter and return type stays visible to
> callers, while `satisfies` still guarantees every route in the union is
> present and correctly shaped.

```ts
// good
type Route = { path: string; auth: boolean }

const routes = {
  home: { path: '/', auth: false },
  dashboard: { path: '/dashboard', auth: true },
  settings: { path: '/settings', auth: true }
} satisfies Record<string, Route>

routes.home.path // '/' — still the literal type, not widened to string
```
