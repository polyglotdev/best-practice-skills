<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 11. Iterators and Generators

## 11.1 Prefer array higher-order methods over manual `for`/`for-in`
loops.

> Why? `map`/`filter`/`reduce`/`some`/`every` express the transformation
> being performed instead of the mechanics of iterating, and they avoid
> mutable loop counters entirely.

```js
const numbers = [1, 2, 3, 4, 5]

// bad
let sum = 0
for (let num of numbers) {
  sum += num
}

// good
const sum = numbers.reduce((total, num) => total + num, 0)

// bad
const increasedByOne = []
for (let i = 0; i < numbers.length; i++) {
  increasedByOne.push(numbers[i] + 1)
}

// good
const increasedByOne = numbers.map((num) => num + 1)
```

## 11.2 Use `for...of` (not `for...in`) when you must iterate an
iterable directly, and never iterate an object's keys with `for...in`
without an own-property guard.

> Why? `for...in` walks the prototype chain, silently including
> inherited enumerable properties. `for...of` iterates values directly
> and needs no guard.

```js
// bad
for (const key in obj) {
  doSomething(key)
}

// good
for (const key of Object.keys(obj)) {
  doSomething(key)
}

// good
for (const [key, value] of Object.entries(obj)) {
  doSomething(key, value)
}
```

## 11.3 Write generators only when you need lazy, potentially
infinite, or externally-driven sequences; otherwise return an array.

> Why? A generator is the right tool when the caller may not consume the
> whole sequence, or when each value depends on expensive work that
> should happen on demand. For a known, finite, eagerly-computed list, a
> plain array is simpler.

```js
// good — lazy, could be infinite, consumer decides how much to pull
function* idGenerator() {
  let id = 1
  while (true) {
    yield id
    id += 1
  }
}

const ids = idGenerator()
const firstId = ids.next().value
```

## 11.4 Space generator function signatures per Prettier and treat
`function*` as a single conceptual token.

> Why? Consistent spacing (owned by Prettier) removes yet another
> bikeshed; treating `function*` as one unit keeps the star from being
> read as multiplication.

```js
// good
function* range(start, end) {
  for (let i = start; i < end; i += 1) {
    yield i
  }
}
```

## 11.5 Implement custom iterables with `Symbol.iterator` when a
value is naturally a sequence.

> Why? It makes your type work with `for...of`, spread, and
> `Array.from` for free, instead of exposing an ad hoc `.getItems()`
> method every caller has to remember to call.

```js
class Range {
  constructor(start, end) {
    this.start = start
    this.end = end
  }

  [Symbol.iterator]() {
    let current = this.start
    const { end } = this
    return {
      next() {
        if (current < end) {
          const value = current
          current += 1
          return { value, done: false }
        }
        return { value: undefined, done: true }
      }
    }
  }
}

const range = new Range(1, 4)
console.log([...range])
// => [1, 2, 3]
```

---
