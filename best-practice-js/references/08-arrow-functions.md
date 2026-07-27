<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 8. Arrow Functions

## 8.1 Use arrow function syntax for anonymous inline callbacks.

> Why? An arrow function executes in the enclosing `this` context, which
> is nearly always what you want for a callback, and is more concise than
> `function`.

```js
const numbers = [1, 2, 3]

// bad
numbers.map(function (x) {
  const y = x + 1
  return x * y
})

// good
numbers.map((x) => {
  const y = x + 1
  return x * y
})
```

## 8.2 Omit braces and use an implicit return only for a single
expression with no side effects; otherwise keep braces and `return`.

> Why? Implicit return reads well when several functions are chained
> together, but hides control flow once there's real logic in the body.

```js
const numbers = [1, 2, 3]

// bad
numbers.map((number) => {
  const nextNumber = number + 1
  `A string containing the ${nextNumber}.`
})

// good
numbers.map((number) => `A string containing the ${number + 1}.`)

// good
numbers.map((number) => {
  const nextNumber = number + 1
  return `A string containing the ${nextNumber}.`
})

// good — implicit return of an object literal needs wrapping parens
numbers.map((number, index) => ({
  [index]: number
}))
```

## 8.3 Wrap a multiline implicit-return expression in parentheses.

> Why? The parens make the expression's start and end unambiguous once it
> no longer fits on one line.

```js
// bad
['get', 'post', 'put'].map((httpMethod) =>
  Object.hasOwn(httpMagicObjectWithAVeryLongName, httpMethod)
)

// good
['get', 'post', 'put'].map((httpMethod) => (
  Object.hasOwn(httpMagicObjectWithAVeryLongName, httpMethod)
))
```

## 8.4 Always parenthesize arrow function parameters, even a single one.

> Why? It minimizes the diff when a second parameter is added later, and
> stays consistent whether the function takes zero, one, or many
> parameters. (This is enforced by our Prettier config's `arrowParens:
> always`.)

```js
const numbers = [1, 2, 3]

// bad (would be produced by arrowParens: "avoid" — not our config)
// numbers.map(x => x * x)

// good — this is what our formatter produces regardless of arity
numbers.map((x) => x * x)
```

## 8.5 Avoid confusing arrow syntax (`=>`) with comparison operators
(`<=`, `>=`) by wrapping a ternary body in parentheses.

> Why? `(item) => item.height <= 256 ? small : large` visually crowds
> `=>` against `<=`; parens around the ternary separate them.

```js
// bad
const itemHeight = (item) =>
  item.height <= 256 ? item.largeSize : item.smallSize

// good
const itemHeight = (item) => (item.height <= 256 ? item.largeSize : item.smallSize)

// good — extract when it gets crowded
const itemHeight = (item) => {
  const { height, largeSize, smallSize } = item
  return height <= 256 ? largeSize : smallSize
}
```

## 8.6 Don't reach for `this`-bound arrow class fields as a substitute
for understanding method binding — bind deliberately, once, in the
constructor or via a class field, not ad hoc at every call site.

> Why? Scattering `.bind(this)` or new arrow wrappers at every call site
> duplicates the same fix everywhere; doing it once next to the method
> declaration documents the requirement in one place.

```js
// bad
class Widget {
  constructor() {
    this.el.addEventListener('click', this.handleClick.bind(this))
  }

  handleClick() {
    this.doThing()
  }
}

// good — arrow class field is already bound once, at definition
class Widget {
  constructor() {
    this.el.addEventListener('click', this.handleClick)
  }

  handleClick = () => {
    this.doThing()
  }
}
```

---
