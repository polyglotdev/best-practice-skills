<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 13. Variables

## 13.1 Never chain variable assignments.

> Why? Chained assignment creates an implicit global if any link in the
> chain isn't declared, and is hard to read at a glance.

```js
// bad
function badExample() {
  let a = (b = c = 1)
}
badExample()

console.log(a)
// throws ReferenceError
console.log(b)
// 1
console.log(c)
// 1

// good
function goodExample() {
  let a = 1
  let b = a
  let c = a
}
goodExample()

console.log(a)
// throws ReferenceError
console.log(b)
// throws ReferenceError
console.log(c)
// throws ReferenceError
```

## 13.2 Avoid unary increment and decrement (`++`, `--`).

> Why? Per the eslint `no-plusplus` rule's rationale, unary
> increment/decrement is subject to automatic semicolon insertion
> pitfalls and silently pads or subtracts values in ways that are easy to
> misread in a dense expression. `num += 1` is unambiguous.

```js
// bad
let num = 1
num++
--num

// good
let num = 1
num += 1
num -= 1
```

## 13.3 Avoid unnecessary ternary statements.

> Why? A ternary that just re-expresses a boolean condition is longer
> and less clear than the condition itself.

```js
// bad
const foo = a ? a : b
const bar = c ? true : false
const baz = c ? false : true

// good
const foo = a || b
const bar = Boolean(c)
const baz = !c
```

## 13.4 No unused variables.

> Why? An unused variable is either dead code or a bug where you meant
> to use it and didn't — either way it should be removed.

```js
// bad
function checkName(hasName) {
  const name = getName()
  if (hasName === 'test') {
    return false
  }
  return true
}

// good
function checkName(hasName) {
  if (hasName === 'test') {
    return false
  }
  return true
}
```

---
