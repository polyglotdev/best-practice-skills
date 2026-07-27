<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 15. Comparison Operators & Equality

## 15.1 Use `===` and `!==` over `==` and `!=`.

> Why? Loose equality coerces its operands through a long list of
> surprising rules; strict equality compares values as-is, which is
> almost always what you actually mean.

```js
// bad
if (name == 'test') {
  // ...
}

// good
if (name === 'test') {
  // ...
}
```

## 15.2 Understand how conditionals coerce with `ToBoolean`.

> Why? Knowing the rules removes any need to memorize special cases:

- **Objects** evaluate to **true**
- **Undefined** evaluates to **false**
- **Null** evaluates to **false**
- **Booleans** evaluate to **the value of the boolean**
- **Numbers** are **false** if `+0`, `-0`, or `NaN`, otherwise **true**
- **Strings** are **false** if an empty string `''`, otherwise **true**

```js
if ([0] && []) {
  // true, because both are objects, even though they look "empty"
}
```

## 15.3 Use shortcuts for booleans, but explicit comparisons for
strings and numbers.

> Why? A boolean check reads naturally as a truthy check, but strings
> and numbers have falsy edge cases (`''`, `0`, `NaN`) worth naming
> explicitly.

```js
// bad
if (isValid === true) {
  // ...
}

// good
if (isValid) {
  // ...
}

// bad
if (name) {
  // ...
}

// good
if (name !== '') {
  // ...
}

// bad
if (collection.length) {
  // ...
}

// good
if (collection.length > 0) {
  // ...
}
```

## 15.4 Use braces for `case` and `default` clauses that declare
lexical bindings.

> Why? A `let`/`const` inside a `switch` is scoped to the whole `switch`
> block, not the individual `case` — so sibling clauses can collide over
> the same name unless each is wrapped in its own block.

```js
// bad
switch (foo) {
  case 1: {
    let x = 1
    break
  }
  case 2:
    let x = 2
    break
  default:
    class C {}
}

// good
switch (foo) {
  case 1: {
    let x = 1
    break
  }
  case 2: {
    let x = 2
    break
  }
  case 3: {
    function f() {}
    break
  }
  default: {
    class C {}
  }
}
```

## 15.5 Ternaries should not be nested and should generally be
single-line expressions.

> Why? A nested ternary asks the reader to parse two decisions in one
> expression; an `if`/`else if`/`else` chain or an early return states
> the same logic more plainly.

```js
// bad
const foo = maybe1 > maybe2 ? 'bar' : value1 > value2 ? 'baz' : null

// split into two independent ternaries
const maybeNull = value1 > value2 ? 'baz' : null
const foo = maybe1 > maybe2 ? 'bar' : maybeNull

// best
const maybeNull = value1 > value2 ? 'baz' : null
const foo = maybe1 > maybe2 ? 'bar' : maybeNull
```

## 15.6 Avoid unneeded ternary statements when a boolean or default
expression will do (see 13.3), and don't mix operators without
parentheses.

> Why? Mixing operators without explicit grouping forces the reader to
> recall operator precedence instead of seeing the intended grouping.

```js
// bad
const foo = a && b < 0 || c > 0 || d + 1 === 0

// good
const foo = (a && b < 0) || c > 0 || d + 1 === 0
```

---
