<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 23. Declaration Files

## 23.1 Write an ambient module declaration for third-party JS packages that ship no types and have no `@types/*` package.

> Why? Without an ambient declaration, importing an untyped package either
> fails to compile (`strict` mode has no implicit `any`) or silently
> becomes `any` everywhere it's used — an explicit, narrow ambient module is
> better than either outcome.

```ts
// good — types/untyped-lib.d.ts
declare module 'untyped-lib' {
  export function run(input: string): { code: number; payload: string }
}
```

## 23.2 Use module augmentation to add properties to a third-party module's existing types; never edit `node_modules` directly.

> Why? Editing `node_modules` is lost on every reinstall; augmentation
> lives in your own source tree, is checked into version control, and
> reapplies automatically.

```ts
// good — types/express-augment.d.ts
import 'express'

declare module 'express' {
  interface Request {
    userId?: string
  }
}
```

## 23.3 Use `declare global {}` inside a module file (a file with at least one top-level `import`/`export`) to augment global ambient types; never use a script-mode global `.d.ts` for project-specific globals.

> Why? `declare global` inside a module is explicit about which file owns
> the augmentation and is included/excluded by the same module graph as
> the rest of your code; a bare script-mode `.d.ts` silently affects every
> file in the program with no import trail.

```ts
// good — global.d.ts
export {}

declare global {
  interface Window {
    __APP_CONFIG__: { apiUrl: string }
  }
}
```

## 23.4 Keep hand-written `.d.ts` ambient files minimal and colocate them near the code that needs them; prefer generating `.d.ts` from source (Chapter 31) over hand-writing types for your own code.

> Why? Hand-written declarations for your own source drift from the
> implementation the moment either one changes without the other; only
> third-party interop and global augmentation genuinely require a
> hand-written `.d.ts`.

```ts
// bad — hand-typed duplicate of your own implementation
// user.d.ts
export function createUser(input: { name: string }): User

// good — let the compiler emit user.d.ts from user.ts (declaration: true)
```
