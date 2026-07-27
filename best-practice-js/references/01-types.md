<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 1. Types

## 1.1 Know your primitives.

> Why? Primitives are copied by value; mutating a copy never affects the
> original, which is the source of a whole class of "why did this change"
> bugs when people forget it.

```js
const foo = 1
let bar = foo

bar = 9

console.log(foo, bar)
// => 1, 9
```

Primitives are: `string`, `number`, `boolean`, `null`, `undefined`, `symbol`,
`bigint`.

## 1.2 Know your complex types.

> Why? Objects, arrays, and functions are copied by reference. Two variables
> can point at the same underlying value, so mutating through one is visible
> through the other.

```js
const foo = [1, 2]
const bar = foo

bar[0] = 9

console.log(foo[0], bar[0])
// => 9, 9
```

## 1.3 Never mutate a reference you don't own, and prefer immutable updates.

> Why? Shared mutable state is the single largest source of "spooky action at
> a distance" bugs. Cloning is now cheap and native.

```js
// bad
function addItem(cart, item) {
  cart.items.push(item)
  return cart
}

// good
function addItem(cart, item) {
  return { ...cart, items: [...cart.items, item] }
}
```

## 1.4 Use `structuredClone` for real deep copies; do not roll your own.

> Why? `JSON.parse(JSON.stringify(x))` silently drops `undefined`,
> functions, `Date` fidelity, `Map`/`Set`, and throws on circular references.
> `structuredClone` is a native, correct, engine-level deep clone.

```js
// bad
const copy = JSON.parse(JSON.stringify(original))

// good
const copy = structuredClone(original)
```

## 1.5 Do not use `Symbol` or `BigInt` unless you actually need their
semantics.

> Why? They cannot be faithfully polyfilled and have surprising interactions
> with `JSON.stringify`, coercion, and equality. Reach for them only for
> unique property keys (`Symbol`) or integers beyond
> `Number.MAX_SAFE_INTEGER` (`BigInt`), not as a default.

```js
// good — real use case for BigInt
const totalSatoshis = 21000000n * 100000000n

// good — real use case for Symbol
const CACHE_KEY = Symbol('cache-key')
```

---
