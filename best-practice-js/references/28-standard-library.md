<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 28. Standard Library

## 28.1 Use the native platform method instead of a userland
reimplementation.

> Why? Every extra dependency is extra bytes, extra supply-chain surface,
> and extra behavior to audit — when the platform already does the job.

```js
// bad
import isString from 'lodash/isString.js'

// good
function isString(value) {
  return typeof value === 'string'
}
```

## 28.2 Use `Number.isNaN`/`Number.isFinite`, never the global
`isNaN`/`isFinite`.

> Why? The global versions coerce their argument first, so `isNaN('a')`
> is `true` for a reason that has nothing to do with the number `NaN`.

```js
// bad
isNaN('1.2')
// false
isNaN('1.2.3')
// true

// good
Number.isNaN('1.2.3')
// false
Number.isNaN(Number('1.2.3'))
// true
```

## 28.3 Reach for `Map`/`Set` instead of a plain object when keys
aren't simple strings, or when you need guaranteed insertion order and
O(1) has/delete.

```js
// bad — abusing an object as a set, plus the hasOwnProperty dance
const seen = {}
for (const id of ids) {
  seen[id] = true
}

// good
const seen = new Set(ids)
```

## 28.4 Use `structuredClone`, `Intl`, and `crypto` before reaching
for a dependency that reimplements them.

```js
// good
const id = crypto.randomUUID()

const formatted = new Intl.DateTimeFormat('en-US', {
  dateStyle: 'medium'
}).format(new Date())

const deepCopy = structuredClone(largeConfigObject)
```

## 28.5 Use `WeakMap`/`WeakRef` for caches keyed by object identity
that must not keep entries alive forever.

> Why? A regular `Map` keyed by object holds a strong reference,
> preventing garbage collection for the lifetime of the map — a slow
> memory leak in long-running processes.

```js
// bad — entries never get garbage collected
const metadataCache = new Map()

// good — entries are collected once the key object is unreachable
const metadataCache = new WeakMap()
```

---
