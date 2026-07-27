<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 34. Naming Conventions

## 34.1 Name types and interfaces in `PascalCase`; do not prefix interfaces with `I`.

> Why? An `I` prefix is a holdover from languages without structural
> typing; in TypeScript, `interface` and `type` are used interchangeably by
> consumers and a prefix adds no information a reader doesn't already have
> from context.

```ts
// bad
interface IUser {
  id: string
}

// good
interface User {
  id: string
}
```

## 34.2 Name generic type parameters in `PascalCase`, prefixed with `T` only when it improves scanability in a long parameter list (see 14.1); never use lowercase for a type parameter.

```ts
// bad
function identity<t>(value: t): t {
  return value
}

// good
function identity<T>(value: T): T {
  return value
}
```

## 34.3 Name discriminant properties on discriminated unions `kind`, `type`, or `status` consistently within a codebase, and name their literal values in `camelCase` unless matching an external API's casing.

> Why? A consistent discriminant name across all unions in a codebase means
> readers do not have to relearn the convention per-union, and tooling
> (exhaustiveness lint rules, codemods) can target the convention
> reliably.

```ts
// good
type Action =
  | { type: 'increment'; amount: number }
  | { type: 'decrement'; amount: number }
  | { type: 'reset' }
```

## 34.4 Suffix boolean-valued type guard functions with a question-style verb (`is*`, `has*`, `can*`), matching runtime boolean naming from `best-practice-js`.

```ts
// good
function isString(value: unknown): value is string {
  return typeof value === 'string'
}

function hasPermission(user: User, permission: Permission): boolean {
  return user.permissions.includes(permission)
}
```

## 34.5 Name type-only import aliases the same as their value counterparts; do not invent a separate naming convention for type-only imports.

```ts
// bad
import type { User as UserType } from './user'

// good
import type { User } from './user'
```
