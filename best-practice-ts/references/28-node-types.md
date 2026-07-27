<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 28. Node Types

## 28.1 Import Node built-ins using the `node:` protocol specifier, and install `@types/node` as a dev dependency for every project that runs on Node.

> Why? The `node:` prefix is unambiguous — it cannot be shadowed by a
> same-named package in `node_modules` — and `@types/node` is required for
> any of `process`, `Buffer`, or `node:*` modules to type-check at all.

```ts
// bad
import fs from 'fs'

// good
import fs from 'node:fs'
import { readFile } from 'node:fs/promises'
```

## 28.2 Never read `process.env` inline with an inferred `string | undefined`; validate it once into a typed config (see 24.2) and import that instead.

```ts
// bad
export function connect() {
  return createClient(process.env.DATABASE_URL) // string | undefined
}

// good
import { env } from './env'
export function connect() {
  return createClient(env.DATABASE_URL) // string, validated at startup
}
```

## 28.3 Type Node event emitters and streams with their generic type parameters instead of leaving them as the default untyped base class.

```ts
// bad
import { EventEmitter } from 'node:events'
const emitter = new EventEmitter()
emitter.emit('data', 'anything') // no checking at all

// good
import { EventEmitter } from 'node:events'

type Events = { data: [chunk: string]; error: [err: Error] }

class TypedEmitter extends EventEmitter {
  override emit<K extends keyof Events>(event: K, ...args: Events[K]): boolean {
    return super.emit(event, ...args)
  }
  override on<K extends keyof Events>(event: K, listener: (...args: Events[K]) => void): this {
    return super.on(event, listener)
  }
}
```
