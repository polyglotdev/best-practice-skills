<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 7. Functions

## 7.1 Prefer named function declarations for top-level functions;
use named function expressions when you need a function value.

> Why? A named function gives you a readable stack trace and a
> self-documenting call site, whether declared at the top level or
> assigned to a `const`.

```js
// bad — anonymous, hurts stack traces
const calculateTotal = function (items) {
  return items.reduce((sum, item) => sum + item.price, 0)
}

// good
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0)
}
```

## 7.2 Never declare a function inside a non-function block
(`if`, `while`, `for`).

> Why? Block-scoped function declarations are interpreted inconsistently
> across engines. Assign a function expression to a `let`/`const` instead.

```js
// bad
if (currentUser) {
  function test() {
    console.log('Nope.')
  }
}

// good
let test
if (currentUser) {
  test = () => {
    console.log('Yup.')
  }
}
```

## 7.3 Never name a parameter `arguments`.

> Why? It shadows the array-like `arguments` object every non-arrow
> function scope receives, and confuses anyone who expects the real one.

```js
// bad
function foo(name, options, arguments) {
  // ...
}

// good
function foo(name, options, args) {
  // ...
}
```

## 7.4 Never use `arguments`; use rest parameters `...args` instead.

> Why? `...args` is explicit about which parameters you're collecting,
> and it produces a real `Array`, not merely an array-like object. There
> is no longer any reason to reach for `arguments` in modern code.

```js
// bad
function concatenateAll() {
  const args = Array.prototype.slice.call(arguments)
  return args.join('')
}

// good
function concatenateAll(...args) {
  return args.join('')
}
```

## 7.5 Use default parameter syntax rather than mutating arguments
inside the body.

> Why? Default parameters are declarative, visible in the signature, and
> can't be defeated by a falsy-but-valid argument the way `opts = opts ||
> {}` can (which incorrectly overrides `0`, `''`, or `false`).

```js
// really bad
function handleThings(opts) {
  opts = opts || {}
  // ...
}

// still bad
function handleThings(opts) {
  if (opts === undefined) {
    opts = {}
  }
  // ...
}

// good
function handleThings(opts = {}) {
  // ...
}
```

## 7.6 Avoid side effects inside default parameter expressions.

> Why? A default parameter that mutates outer state runs at unpredictable
> times — only when the argument is omitted — which is confusing to trace.

```js
let b = 1

// bad
function count(a = b++) {
  console.log(a)
}
count()
// 1
count()
// 2
count(3)
// 3
count()
// 3
```

## 7.7 Always put default parameters last.

> Why? Parameters before a default-valued one can't be omitted anyway, so
> putting defaults last keeps every call site's positional arguments
> meaningful.

```js
// bad
function handleThings(opts = {}, name) {
  // ...
}

// good
function handleThings(name, opts = {}) {
  // ...
}
```

## 7.8 Never use the `Function` constructor to create a function.

> Why? It evaluates a string as code, identical in risk to `eval()`.

```js
// bad
const add = new Function('a', 'b', 'return a + b')

// good
const add = (a, b) => a + b
```

## 7.9 Never mutate or reassign parameters.

> Why? Mutating an object parameter causes surprising side effects in the
> caller; reassigning a parameter binding confuses readers about what the
> function actually received, and can defeat engine optimizations.

```js
// bad
function f1(obj) {
  obj.key = 1
}

// good
function f2(obj) {
  const key = Object.hasOwn(obj, 'key') ? obj.key : 1
  return { ...obj, key }
}

// bad
function f3(a) {
  a = 1
}

// good
function f4(a = 1) {
  // ...
}
```

## 7.10 Prefer spread syntax over `apply`/`call` to invoke a function
with an array of arguments.

> Why? Spread is shorter, needs no explicit `this` context, and composes
> cleanly with `new`.

```js
// bad
const x = [1, 2, 3, 4, 5]
console.log.apply(console, x)

// good
const x = [1, 2, 3, 4, 5]
console.log(...x)

// bad
const d1 = new (Function.prototype.bind.apply(Date, [null, 2024, 8, 5]))()

// good
const d2 = new Date(...[2024, 8, 5])
```

## 7.11 Keep function signatures small; group related parameters into
a single options object once you pass more than two or three.

> Why? Long positional parameter lists are impossible to call correctly
> from memory and force every call site to repeat argument order.

```js
// bad
function createUser(name, email, role, isActive, sendWelcomeEmail) {
  // ...
}

// good
function createUser({ name, email, role, isActive, sendWelcomeEmail }) {
  // ...
}
```

---
