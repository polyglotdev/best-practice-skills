<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 18. Comments

## 18.1 Use `/** ... */` for multiline comments that document a
function, class, or module's contract.

```js
// bad
// make() returns a new element
// based on the passed-in tag name
//
// @param {string} tag
// @return {Element} element
function make(tag) {
  // ...
  return element
}

// good
/**
 * make() returns a new element
 * based on the passed-in tag name
 */
function make(tag) {
  // ...
  return element
}
```

## 18.2 Use `//` for single-line comments. Place them on their own
line above the code they describe, with a blank line before the
comment unless it's the first line of a block.

```js
// bad
const active = true // is current tab

// good
// is current tab
const active = true

// bad
function getType() {
  console.log('fetching type...')
  // set the default type to 'no type'
  const type = this.type || 'no type'
  return type
}

// good
function getType() {
  console.log('fetching type...')

  // set the default type to 'no type'
  const type = this.type || 'no type'

  return type
}
```

## 18.3 Prefix actionable comments with `FIXME` or `TODO` so tooling
and teammates can grep for them.

```js
class Calculator extends Abacus {
  constructor() {
    super()

    // FIXME: shouldn't use a global here
    total = 0
  }
}

class Calculator extends Abacus {
  constructor() {
    super()

    // TODO: total should be configurable by an options param
    this.total = 0
  }
}
```

## 18.4 Comments explain *why*, not *what* — the code already says
what it does.

> Why? A comment that restates the code goes stale the moment the code
> changes; a comment that explains a non-obvious reason stays useful.

```js
// bad
// increment i by 1
i += 1

// good
// skip the header row when computing totals
i += 1
```

---
