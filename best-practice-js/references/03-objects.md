<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 3. Objects

## 3.1 Use the literal syntax for object creation.

> Why? It is more concise, and identical in the engine.

```js
// bad
const item = new Object()

// good
const item = {}
```

## 3.2 Use computed property names when creating objects with dynamic
property names.

> Why? They let you define every property of an object in one place instead
> of splitting the shape across a literal and follow-up assignments.

```js
function getKey(k) {
  return `a key named ${k}`
}

// bad
const obj = {
  id: 5,
  name: 'San Francisco'
}
obj[getKey('enabled')] = true

// good
const obj = {
  id: 5,
  name: 'San Francisco',
  [getKey('enabled')]: true
}
```

## 3.3 Use object method shorthand.

> Why? It removes a redundant `function` keyword and a redundant colon.

```js
// bad
const atom = {
  value: 1,
  addValue: function (value) {
    return atom.value + value
  }
}

// good
const atom = {
  value: 1,
  addValue(value) {
    return atom.value + value
  }
}
```

## 3.4 Use property value shorthand.

> Why? It is shorter and states the intent directly — this property is that
> variable.

```js
const lukeSkywalker = 'Luke Skywalker'

// bad
const obj = {
  lukeSkywalker: lukeSkywalker
}

// good
const obj = {
  lukeSkywalker
}
```

## 3.5 Group shorthand properties at the beginning of the object
declaration.

> Why? It's easier to tell at a glance which properties are using the
> shorthand.

```js
const anakinSkywalker = 'Anakin Skywalker'
const lukeSkywalker = 'Luke Skywalker'

// bad
const obj = {
  episodeOne: 1,
  twoJediWalkIntoACantina: 2,
  lukeSkywalker,
  episodeThree: 3,
  mayTheFourth: 4,
  anakinSkywalker
}

// good
const obj = {
  lukeSkywalker,
  anakinSkywalker,
  episodeOne: 1,
  twoJediWalkIntoACantina: 2,
  episodeThree: 3,
  mayTheFourth: 4
}
```

## 3.6 Only quote properties that are invalid identifiers.

> Why? Unquoted keys are easier to read, get proper syntax highlighting, and
> are more easily optimized by engines. This is a naming rule, not a
> formatting rule — Prettier will not add or remove quotes for you.

```js
// bad
const bad = {
  foo: 3,
  bar: 4,
  'data-blah': 5
}

// good
const good = {
  foo: 3,
  bar: 4,
  'data-blah': 5
}
```

## 3.7 Never call `Object.prototype` methods directly off an instance;
use `Object.hasOwn` instead.

> Why? An object's own property might shadow the method (`{ hasOwnProperty:
> false }`), or the object might have a null prototype
> (`Object.create(null)`). `Object.hasOwn` is the native ES2022 answer and
> sidesteps both problems.

```js
// bad
console.log(object.hasOwnProperty(key))

// bad
console.log(Object.prototype.hasOwnProperty.call(object, key))

// good
console.log(Object.hasOwn(object, key))
```

## 3.8 Prefer object spread over `Object.assign` for shallow copies; use
object rest to omit properties.

> Why? Spread cannot accidentally mutate its source the way
> `Object.assign(original, patch)` can, and rest destructuring reads as
> intent ("everything except these") rather than an imperative `delete`.

```js
// very bad
const original = { a: 1, b: 2 }
const copy = Object.assign(original, { c: 3 })
// mutates `original`
delete copy.a
// mutates it again

// bad
const original = { a: 1, b: 2 }
const copy = Object.assign({}, original, { c: 3 })

// good
const original = { a: 1, b: 2 }
const copy = { ...original, c: 3 }
// copy => { a: 1, b: 2, c: 3 }

const { a, ...noA } = copy
// noA => { b: 2, c: 3 }
```

## 3.9 Use `Object.groupBy` instead of hand-rolled `reduce` grouping.

> Why? It is a native, allocation-minimal way to express the extremely
> common "bucket these items by a key" operation.

```js
// bad
const grouped = orders.reduce((acc, order) => {
  const key = order.status
  acc[key] = acc[key] || []
  acc[key].push(order)
  return acc
}, {})

// good
const grouped = Object.groupBy(orders, (order) => order.status)
```

---
