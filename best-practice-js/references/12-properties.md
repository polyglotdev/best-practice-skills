<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 12. Properties

## 12.1 Use dot notation to access properties.

> Why? It's shorter and reads closer to natural language than bracket
> notation.

```js
const luke = {
  jedi: true,
  age: 28
}

// bad
const isJedi = luke['jedi']

// good
const isJedi = luke.jedi
```

## 12.2 Use bracket notation when the key is a variable.

```js
const luke = {
  jedi: true,
  age: 28
}

function getProp(prop) {
  return luke[prop]
}

const isJedi = getProp('jedi')
```

## 12.3 Use `**` for exponentiation.

> Why? The exponentiation operator is native and reads more directly
> than a `Math.pow` call.

```js
// bad
const binary = Math.pow(2, 10)

// good
const binary = 2 ** 10
```

## 12.4 Use optional chaining (`?.`) instead of manual existence
checks, and nullish coalescing (`??`) instead of `||` for defaults.

> Why? `?.` short-circuits to `undefined` the moment any link in the
> chain is nullish, replacing a pyramid of `&&` guards. `??` only falls
> back on `null`/`undefined`, unlike `||`, which also overrides `0`,
> `''`, and `false` — frequently a bug.

```js
// bad
const street = user && user.address && user.address.street

// good
const street = user?.address?.street

// bad — 0 is a valid retry count, but || overrides it
const retries = config.retries || 3

// good
const retries = config.retries ?? 3
```

---
