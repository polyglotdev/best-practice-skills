<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 22. Modules & `import type`

## 22.1 With `verbatimModuleSyntax`, use `import type` / `export type` explicitly for anything used only as a type; never rely on the compiler to elide the import for you.

> Why? `verbatimModuleSyntax` emits every import/export exactly as written
> — it does not analyze usage to decide what to elide. A type-only import
> written as a value import will be emitted as a runtime import of a
> module that may not exist at runtime (e.g. a `.d.ts`-only package).

```ts
// bad — emitted as a real runtime import under verbatimModuleSyntax
import { User } from './types'

// good
import type { User } from './types'
```

## 22.2 Use inline `type` modifiers on individual named specifiers when a module exports both types and values that are imported together.

> Why? Splitting into two separate import statements for a mixed
> type/value module is verbose; the inline `type` modifier keeps one import
> statement while still telling the emitter which specifiers are type-only.

```ts
// bad
import { createUser } from './user'
import type { User } from './user'

// good
import { createUser, type User } from './user'
```

## 22.3 Re-export types explicitly with `export type { ... }` from a barrel file; do not re-export them as values.

```ts
// bad
export { User } from './user'

// good
export type { User } from './user'
export { createUser } from './user'
```

## 22.4 Use ESM `import`/`export` exclusively in new code; do not mix `require`/`module.exports` into a `verbatimModuleSyntax` project.

> Why? `verbatimModuleSyntax` assumes a consistent module syntax throughout
> a file — mixing `require` into an otherwise-ESM file produces confusing
> emit and defeats the purpose of the flag.

```ts
// bad
import { readFile } from 'node:fs/promises'
const path = require('node:path')

// good
import { readFile } from 'node:fs/promises'
import path from 'node:path'
```
