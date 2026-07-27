<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 2. References

## 2.1 Use `const` for all references; never use `var`.

> Why? `const` prevents reassignment, which removes an entire category of
> bugs where a binding silently changes underneath you.

```js
// bad
var a = 1
var b = 2

// good
const a = 1
const b = 2
```

## 2.2 If you must reassign, use `let` — never `var`.

> Why? `let` is block-scoped like every other modern binding; `var` is
> function-scoped and hoists in ways that surprise readers.

```js
// bad
var count = 1
if (true) {
  count += 1
}

// good
let count = 1
if (true) {
  count += 1
}
```

## 2.3 Understand that `const`/`let` are block-scoped; `var` is not.

```js
// const and let only exist in the blocks they are defined in
{
  let a = 1
  const b = 1
  var c = 1
}
console.log(a)
// ReferenceError
console.log(b)
// ReferenceError
console.log(c)
// 1 — var leaked out of the block
```

## 2.4 Declare one variable per `const`/`let` statement.

> Why? It's easier to add or remove a declaration in a diff, and a typo
> can't accidentally chain a comma-separated declaration into a global.

```js
// bad
const a = 1,
  b = 2

// good
const a = 1
const b = 2
```

## 2.5 Group all `const` declarations, then all `let` declarations.

> Why? You may need to assign a variable later depending on a previous
> assignment, and grouping keeps intent readable.

```js
// bad
let i
const items = getItems()
let dragonball
const goSportsTeam = true
let len

// good
const goSportsTeam = true
const items = getItems()
let dragonball
let i
let len
```

## 2.6 Assign variables where you need them, in a reasonable place.

> Why? `let` and `const` are block-scoped, not function-scoped — placing
> them far from their first use scatters state across the function.

```js
// bad — unnecessary function call before the early return
function checkName(hasName) {
  const name = getName()

  if (hasName === 'test') {
    return false
  }

  if (name === 'test') {
    this.setName('')
    return false
  }

  return name
}

// good
function checkName(hasName) {
  if (hasName === 'test') {
    return false
  }

  const name = getName()

  if (name === 'test') {
    this.setName('')
    return false
  }

  return name
}
```

---
