<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 16. Blocks

## 16.1 Use braces for all multiline blocks.

> Why? An unbraced multiline block invites a bug the moment someone
> adds a second statement expecting it to be inside the block.

```js
// bad
if (test) return false

// good
if (test) {
  return false
}

// bad
function foo() {
  return false
}

// good
function bar() {
  return false
}
```

## 16.2 Put `else` on the same line as the closing brace of the `if`.

> Why? Per Prettier's formatting, `if`/`else` blocks are visually one
> unit; splitting them across separate top-level lines suggests they are
> unrelated.

```js
// bad
if (test) {
  thing1()
} else {
  thing2()
}

// good — this is what Prettier already produces
if (test) {
  thing1()
} else {
  thing2()
}
```

## 16.3 Avoid deep nesting; prefer early returns and guard clauses.

> Why? Every additional nesting level is another condition the reader
> must hold in their head simultaneously. A guard clause resolves the
> exceptional case immediately and lets the rest of the function assume
> the happy path.

```js
// bad
function getPayoutAmount(invoice) {
  if (invoice) {
    if (invoice.isPaid) {
      return 0
    } else {
      if (invoice.amount > 0) {
        return invoice.amount
      }
    }
  }
  return null
}

// good
function getPayoutAmount(invoice) {
  if (!invoice) {
    return null
  }
  if (invoice.isPaid) {
    return 0
  }
  return invoice.amount > 0 ? invoice.amount : null
}
```

---
