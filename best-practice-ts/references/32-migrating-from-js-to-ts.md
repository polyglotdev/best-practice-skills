<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 32. Migrating from JS to TS

## 32.1 Enable `allowJs` and `checkJs` before converting any file, and fix JSDoc-flagged errors in place while files are still `.js`.

> Why? `checkJs` lets you get real type-checking value out of existing
> `.js` files via JSDoc annotations before committing to a rename, so the
> eventual `.js` → `.ts` rename is a mechanical step with no new errors to
> chase.

```json
// good — tsconfig.json during migration
{
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true
  }
}
```

## 32.2 Annotate exported functions in `.js` files with JSDoc types during the JSDoc-first phase, then convert the same annotations to real TS syntax once the file is renamed.

```js
// good — user.js, during the JSDoc-first phase
/**
 * @param {{ name: string, email: string }} input
 * @returns {{ id: string, name: string, email: string }}
 */
function createUser(input) {
  return { id: crypto.randomUUID(), ...input }
}
```

```ts
// good — user.ts, after rename
type CreateUserInput = { name: string; email: string }
type User = { id: string; name: string; email: string }

function createUser(input: CreateUserInput): User {
  return { id: crypto.randomUUID(), ...input }
}
```

## 32.3 Migrate leaf modules (no internal dependents) before migrating modules that many other files import.

> Why? Converting a leaf module first means its new, stricter types cannot
> cause a cascade of new errors elsewhere; converting a widely-depended-on
> module first can surface a large batch of downstream errors all at once.

```ts
// good — migration order for a typical app
// 1. utils/format.ts   (leaf, no internal deps)
// 2. utils/validate.ts (leaf, no internal deps)
// 3. services/api.ts   (depends on the above)
// 4. components/*      (depends on services)
```

## 32.4 Turn on `strict` only after the initial conversion is error-free under loose settings, then fix the resulting errors file by file rather than disabling `strict` again.

> Why? Converting and strict-ifying in the same step produces an
> overwhelming error list that conflates "this file isn't TS-shaped yet"
> errors with "this file has an actual type bug" errors; separating the
> steps makes each batch of errors attributable to one cause.

```json
// good — step 1: convert with strict off
{ "compilerOptions": { "strict": false } }

// good — step 2: flip on strict once conversion is error-free, fix incrementally
{ "compilerOptions": { "strict": true } }
```
