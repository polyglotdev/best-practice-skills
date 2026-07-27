<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 9. `any` vs `unknown` vs `never`

## 9.1 Never use `any` in an exported function signature, exported type, or exported class member.

> Why? `any` at a public boundary disables checking for every consumer of
> that export, and the unsoundness propagates outward with no way for
> callers to opt back into safety.

```ts
// bad
export function parseConfig(raw: any): any {
  return JSON.parse(raw)
}

// good
export function parseConfig(raw: string): unknown {
  return JSON.parse(raw)
}
```

## 9.2 Use `unknown` for values whose type is not yet known, and narrow before use.

> Why? `unknown` accepts any value like `any`, but forbids every operation
> until the type is narrowed, preserving safety at the boundary while still
> being maximally permissive about input.

```ts
// bad
function stringify(value: any): string {
  return value.toString()
}

// good
function stringify(value: unknown): string {
  if (typeof value === 'string') {
    return value
  }
  return JSON.stringify(value)
}
```

## 9.3 Use `never` for values that should be provably unreachable — exhaustiveness checks, impossible unions, functions that always throw.

> Why? `never` documents intent — this code path must not be reachable —
> and the compiler will flag any assignment into a `never`-typed position as
> an error.

```ts
// good
function fail(message: string): never {
  throw new Error(message)
}

function pick(flag: true | false): string {
  if (flag) return 'yes'
  if (!flag) return 'no'
  return fail('unreachable')
}
```

## 9.4 If an internal-only escape hatch to `any` is unavoidable (e.g. interop with an untyped library), isolate it behind a single narrowly-typed wrapper and never let it leak.

> Why? Containing the `any` to one file/function means the unsoundness has
> exactly one place to be reviewed and fixed later, instead of contaminating
> every call site.

```ts
// good — untyped-legacy-lib.ts, the only file that touches `any`
// eslint-disable-next-line @typescript-eslint/no-explicit-any
import legacyLib from 'untyped-legacy-lib'

interface LegacyResult {
  code: number
  payload: string
}

export function callLegacy(input: string): LegacyResult {
  return legacyLib.run(input) as LegacyResult
}
```
