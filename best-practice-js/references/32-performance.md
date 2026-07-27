<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 32. Performance

## 32.1 Measure before optimizing; don't guess.

> Why? Intuition about what's slow in JavaScript engines is frequently
> wrong. Profile with `node --prof`, Chrome DevTools, or a benchmarking
> library, then optimize the function that the profile actually points
> to.

```js
// good — measure first
import { performance } from 'node:perf_hooks'

const start = performance.now()
runExpensiveOperation()
console.log(`took ${performance.now() - start}ms`)
```

## 32.2 Never do blocking synchronous work on a request-handling
path.

> Why? Node runs your handler on a single event-loop thread; a
> synchronous CPU-bound or blocking-I/O call there stalls every other
> in-flight request until it finishes.

```js
// bad — blocks the event loop for every concurrent request
import fs from 'node:fs'

app.get('/report', (req, res) => {
  const data = fs.readFileSync('big-report.json', 'utf8')
  res.send(data)
})

// good
import { readFile } from 'node:fs/promises'

app.get('/report', async (req, res) => {
  const data = await readFile('big-report.json', 'utf8')
  res.send(data)
})
```

## 32.3 Batch or paginate large data operations instead of loading
everything into memory at once.

```js
// bad — loads the entire table into memory
const allUsers = await db.users.findAll()

// good — processes in bounded chunks
for await (const batch of db.users.findInBatches({ batchSize: 500 })) {
  await processBatch(batch)
}
```

## 32.4 Cache expensive, pure, repeatedly-called computations; scope
the cache lifetime intentionally (request, session, or process) rather
than caching forever by accident.

```js
// good
const memoCache = new Map()

function memoize(fn) {
  return (key) => {
    if (!memoCache.has(key)) {
      memoCache.set(key, fn(key))
    }
    return memoCache.get(key)
  }
}
```

## 32.5 Avoid unnecessary intermediate array allocations in hot
paths by combining transformations.

```js
// bad — three full passes and two intermediate arrays
const result = items
  .map((item) => item.value)
  .filter((value) => value > 0)
  .reduce((sum, value) => sum + value, 0)

// good — one pass, no intermediate arrays
const result = items.reduce((sum, item) => {
  return item.value > 0 ? sum + item.value : sum
}, 0)
```

For further reading, see the community-maintained
[JS performance notes referenced by the Airbnb guide](https://github.com/petkaantonov/bluebird/wiki/Optimization-killers).

---
