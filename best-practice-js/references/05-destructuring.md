<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 5. Destructuring

## 5.1 Use object destructuring when accessing and using multiple
properties of an object.

> Why? Destructuring saves you from creating temporary references, avoids
> repetitive `object.prop` access, and gives one single site of definition
> for which shape a block depends on.

```js
// bad
function getFullName(user) {
  const firstName = user.firstName
  const lastName = user.lastName

  return `${firstName} ${lastName}`
}

// good
function getFullName(user) {
  const { firstName, lastName } = user
  return `${firstName} ${lastName}`
}

// best
function getFullName({ firstName, lastName }) {
  return `${firstName} ${lastName}`
}
```

## 5.2 Use array destructuring.

> Why? It avoids throwaway index variables and states positional intent
> directly.

```js
const arr = [1, 2, 3, 4]

// bad
const first = arr[0]
const second = arr[1]

// good
const [first, second] = arr
```

## 5.3 Use object destructuring for multiple return values, not array
destructuring.

> Why? You can add new properties or reorder them over time without
> breaking call sites, and callers can pick only what they need by name.

```js
// bad
function processInput(input) {
  return [left, right, top, bottom]
}

// the caller needs to know and preserve the exact order
const [left, , top] = processInput(input)

// good
function processInput(input) {
  return { left, right, top, bottom }
}

// the caller selects only the data it needs, by name
const { left, top } = processInput(input)
```

## 5.4 Destructure function parameters with defaults instead of
checking for `undefined` inline.

> Why? It puts the fallback next to the shape it applies to and reads as
> declarative configuration rather than imperative branching.

```js
// bad
function createUser(options) {
  const role = options.role !== undefined ? options.role : 'member'
  const name = options.name
  return { name, role }
}

// good
function createUser({ name, role = 'member' }) {
  return { name, role }
}
```

---
