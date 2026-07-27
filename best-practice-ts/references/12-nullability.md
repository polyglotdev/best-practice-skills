<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 12. Nullability

## 12.1 Prefer `undefined` for "absent," reserve `null` for "explicitly empty," and be consistent within a codebase.

> Why? APIs like `Object.get`, optional properties, and default parameters
> all naturally produce `undefined`; mixing in `null` for the same concept
> forces every consumer to check both.

```ts
// bad — inconsistent absence values across one module
function findUser(id: string): User | null { /* ... */ }
function findOrder(id: string): Order | undefined { /* ... */ }

// good — one convention per boundary, documented
function findUser(id: string): User | undefined { /* ... */ }
function findOrder(id: string): Order | undefined { /* ... */ }
```

## 12.2 With `exactOptionalPropertyTypes`, do not assign `undefined` to an optional property; omit the key instead.

> Why? `exactOptionalPropertyTypes` distinguishes "key absent" from "key
> present with value `undefined`" — the two are different at runtime for
> `Object.keys`, spreads, and `JSON.stringify`, and the flag makes that
> distinction visible in the type system.

```ts
// bad — errors under exactOptionalPropertyTypes
type Options = { timeout?: number }
const opts: Options = { timeout: undefined }

// good
const opts: Options = {}
```

## 12.3 Use optional chaining (`?.`) and nullish coalescing (`??`) instead of manual `&&`/`||` chains for nullable access.

> Why? `?.`/`??` short-circuit precisely on `null`/`undefined` only, whereas
> `||` also short-circuits on `0`, `''`, and `false`, which are usually
> valid values you did not intend to replace.

```ts
// bad
const port = config.port || 3000 // wrong if config.port is 0
const city = user && user.address && user.address.city

// good
const port = config.port ?? 3000
const city = user?.address?.city
```

## 12.4 Do not use the definite assignment assertion (`!`) on class fields to paper over `strictPropertyInitialization`; initialize in the constructor or make the field optional.

> Why? The assertion tells the compiler the field is always set before use,
> but provides no actual guarantee — a genuine late-initialization bug
> (e.g. via a lifecycle hook) becomes an unchecked `undefined` access.

```ts
// bad
class Connection {
  socket!: WebSocket
  connect() {
    this.socket = new WebSocket(this.url)
  }
}

// good
class Connection {
  private socket: WebSocket | undefined
  connect() {
    this.socket = new WebSocket(this.url)
  }
  send(data: string) {
    if (!this.socket) throw new Error('Not connected')
    this.socket.send(data)
  }
}
```
