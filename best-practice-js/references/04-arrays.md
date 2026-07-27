<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 4. Arrays

## 4.1 Use the literal syntax for array creation.

> Why? It is shorter, and `new Array(3)` produces a confusing sparse array
> of length 3, not `[3]`.

```js
// bad
const items = new Array()

// good
const items = []
```

## 4.2 Use `Array#push` instead of direct index assignment to add items.

> Why? It states intent — appending — instead of relying on the reader to
> know that `length` already points past the last element.

```js
const someStack = []

// bad
someStack[someStack.length] = 'abracadabra'

// good
someStack.push('abracadabra')
```

## 4.3 Use array spreads `...` to copy arrays.

> Why? It is a single expression instead of a manual loop, and it clearly
> signals "a new array with the same items."

```js
// bad
const len = items.length
const itemsCopy = []
let i

for (i = 0; i < len; i += 1) {
  itemsCopy[i] = items[i]
}

// good
const itemsCopy = [...items]
```

## 4.4 Use spread `...` to convert an iterable to an array.

> Why? It is the shortest, most direct expression of "materialize this
> iterable as an array."

```js
const foo = document.querySelectorAll('.foo')

// good
const nodes = Array.from(foo)

// best
const nodes = [...foo]
```

## 4.5 Use `Array.from` for converting an array-like object to an array.

> Why? Array-likes (such as `arguments` or a DOM `NodeList` without an
> iterator) don't support spread directly in every context; `Array.from`
> handles the `length` + indexed-access shape explicitly.

```js
const arrLike = { 0: 'foo', 1: 'bar', 2: 'baz', length: 3 }

// bad
const arr = Array.prototype.slice.call(arrLike)

// good
const arr = Array.from(arrLike)
```

## 4.6 Use `Array.from` instead of spread for mapping over an iterable.

> Why? `Array.from(iterable, mapFn)` maps in the same pass instead of
> materializing an intermediate array first.

```js
// bad
const baz = [...foo].map(bar)

// good
const baz = Array.from(foo, bar)
```

## 4.7 Always `return` inside array method callbacks.

> Why? A callback with no return produces `undefined` for every element,
> silently corrupting `map`/`reduce`/`filter` chains. It's fine to omit
> `return` only for a single-expression arrow body (see §8.2).

```js
const nested = [
  [0, 1],
  [2, 3],
  [4, 5]
]

// bad — no returned value means `acc` becomes undefined after iteration 1
const flatBad = nested.reduce((acc, item) => {
  const flatten = acc.concat(item)
})

// good
const flatGood = nested.reduce((acc, item) => {
  const flatten = acc.concat(item)
  return flatten
})

// bad
inbox.filter((msg) => {
  const { subject, author } = msg
  if (subject === 'Mockingbird') {
    return author === 'Harper Lee'
  } else {
    return false
  }
})

// good
inbox.filter((msg) => {
  const { subject, author } = msg
  if (subject === 'Mockingbird') {
    return author === 'Harper Lee'
  }

  return false
})
```

## 4.8 Reach for the right higher-order method instead of bending `map`
or `forEach` to do another method's job.

> Why? `find`/`findLast` stop at the first match instead of scanning the
> whole array; `some`/`every` short-circuit; `flatMap` fuses a map + flatten
> into one pass. Each is both faster and clearer than a general-purpose
> substitute.

```js
// bad
const firstAdmin = users.filter((user) => user.isAdmin)[0]

// good
const firstAdmin = users.find((user) => user.isAdmin)

// bad
const hasAdmin = users.filter((user) => user.isAdmin).length > 0

// good
const hasAdmin = users.some((user) => user.isAdmin)

// bad
const words = sentences.map((s) => s.split(' ')).flat()

// good
const words = sentences.flatMap((s) => s.split(' '))
```

## 4.9 Use `Array.prototype.at` for offset-from-end access, and
`findLast`/`findLastIndex` for reverse search.

> Why? `arr[arr.length - 1]` is a repeated, error-prone computation;
> `arr.at(-1)` says exactly what it means. Reversing an array just to find
> the last match wastes an allocation.

```js
// bad
const last = arr[arr.length - 1]

// good
const last = arr.at(-1)

// bad
const lastAdmin = [...users].reverse().find((user) => user.isAdmin)

// good
const lastAdmin = users.findLast((user) => user.isAdmin)
```

---
