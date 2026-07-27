<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 25. Async & Promise Types

## 25.1 Type async functions by their resolved value only; never write the return type as `Promise<Promise<T>>` or manually wrap an already-`Promise`-returning expression.

```ts
// bad
async function fetchAll(): Promise<Promise<User[]>> {
  return getUsers()
}

// good
async function fetchAll(): Promise<User[]> {
  return getUsers()
}
```

## 25.2 Use `Awaited<T>` when writing a generic helper that must express "the resolved type of whatever was passed in," rather than requiring callers to pre-unwrap it.

```ts
// good
async function withRetry<T>(fn: () => Promise<T>, attempts = 3): Promise<Awaited<T>> {
  for (let i = 0; i < attempts; i += 1) {
    try {
      return await fn()
    } catch (err) {
      if (i === attempts - 1) throw err
    }
  }
  throw new Error('unreachable')
}
```

## 25.3 Type `Promise.all`/`Promise.allSettled` results by letting inference flow from a tuple literal input, rather than annotating the result manually.

> Why? TypeScript infers a precise tuple of result types from a tuple of
> input promises; a manual annotation is redundant at best and wrong at
> worst if the inputs change.

```ts
// good
async function loadDashboard(userId: string) {
  const [user, orders] = await Promise.all([getUser(userId), getOrders(userId)])
  return { user, orders }
}
```

## 25.4 Use `using`/`await using` (TS 5.2+) for resources that implement `Symbol.dispose`/`Symbol.asyncDispose`, instead of manual `try`/`finally` cleanup.

> Why? `using` guarantees disposal runs even if an exception is thrown or a
> `return` happens mid-block, exactly like `try`/`finally`, but without the
> boilerplate and without the risk of forgetting the `finally` clause.

```ts
// bad
async function withConnection(run: (conn: Connection) => Promise<void>) {
  const conn = await openConnection()
  try {
    await run(conn)
  } finally {
    await conn.close()
  }
}

// good
class Connection {
  async [Symbol.asyncDispose]() {
    await this.close()
  }
  async close() {
    /* ... */
  }
}

async function withConnection(run: (conn: Connection) => Promise<void>) {
  await using conn = await openConnection()
  await run(conn)
}
```
