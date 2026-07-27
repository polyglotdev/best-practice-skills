<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 24. Accessors

## 24.1 Accessor functions are not required; if you write them,
use `getVal()`/`setVal(value)`, not bare `val()`/`val(value)`.

> Why? A function that both reads and writes depending on arity is
> surprising to call and to grep for.

```js
// bad
class Dragon {
  scale(scale) {
    if (scale === undefined) {
      return this._scale
    }
    this._scale = scale
  }
}

// good
class Dragon {
  getScale() {
    return this._scale
  }

  setScale(scale) {
    this._scale = scale
  }
}
```

## 24.2 If the property is boolean, use `isVal()` or `hasVal()`.

```js
// bad
if (!dragon.age()) {
  return false
}

// good
if (!dragon.hasAge()) {
  return false
}
```

## 24.3 `get`/`set` are fine when the computation is cheap, pure, and
genuinely looks like a property from the caller's perspective; reach
for a method when the operation does I/O, is expensive, or has side
effects.

> Why? A `get` that silently makes a network call or mutates state
> violates the caller's expectation that reading a property is free and
> side-effect-free.

```js
// good — cheap, pure, derived value
class Rectangle {
  #width

  #height

  constructor(width, height) {
    this.#width = width
    this.#height = height
  }

  get area() {
    return this.#width * this.#height
  }
}

// good — has real work/side effects, so it's a method, not a getter
class UserRepository {
  async fetchActiveUsers() {
    const response = await fetch('/api/users?status=active')
    return response.json()
  }
}
```

---
