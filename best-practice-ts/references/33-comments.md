<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 33. Comments

## 33.1 Write JSDoc on every exported function, type, interface, and class, even in `.ts` files where types make parameter/return types visible in editor tooltips already.

> Why? Types communicate *shape*; JSDoc communicates *intent, side
> effects, and constraints that don't fit in a type* — why the function
> exists, when it throws, and any invariant callers must uphold.

```ts
// bad — no context beyond the type signature
export function retry<T>(fn: () => Promise<T>, attempts: number): Promise<T> {}

// good
/**
 * Retries an async operation with linear backoff.
 * Throws the last error if every attempt fails.
 */
export function retry<T>(fn: () => Promise<T>, attempts: number): Promise<T> {}
```

## 33.2 Do not restate the type in prose inside JSDoc `@param`/`@returns` tags; TypeScript already surfaces the type — describe the meaning instead.

```ts
// bad
/**
 * @param id - a string
 * @returns a User
 */
function getUser(id: string): User {}

// good
/**
 * @param id - the user's UUID, not the email
 * @returns the user, or throws NotFoundError if no match exists
 */
function getUser(id: string): User {}
```

## 33.3 Use `// TODO(username): reason` comments for known type-safety gaps (e.g. a temporary `as` cast) so they are searchable and attributable.

```ts
// good
// TODO(alex): remove this cast once the upstream SDK ships proper types (SDK-123)
const client = createClient() as unknown as TypedClient
```
