<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 9. Classes & Constructors

## 9.1 Always use `class`; never manipulate `prototype` directly.

> Why? `class` syntax is shorter and easier to reason about than manual
> prototype wiring.

```js
// bad
function Queue(contents = []) {
  this.queue = [...contents]
}
Queue.prototype.pop = function () {
  const value = this.queue[0]
  this.queue.splice(0, 1)
  return value
}

// good
class Queue {
  constructor(contents = []) {
    this.queue = [...contents]
  }

  pop() {
    const value = this.queue[0]
    this.queue.splice(0, 1)
    return value
  }
}
```

## 9.2 Use `extends` for inheritance.

> Why? It's the built-in mechanism for inheriting prototype behavior
> without breaking `instanceof`.

```js
// bad
function PeekableQueue(contents) {
  Queue.apply(this, contents)
}
PeekableQueue.prototype.peek = function () {
  return this.queue[0]
}

// good
class PeekableQueue extends Queue {
  peek() {
    return this.queue[0]
  }
}
```

## 9.3 Methods may `return this` to enable chaining.

```js
// bad
class Jedi {
  jump() {
    this.jumping = true
    return true
  }

  setHeight(height) {
    this.height = height
  }
}

const luke = new Jedi()
luke.jump()
// => true
luke.setHeight(20)
// => undefined

// good
class Jedi {
  jump() {
    this.jumping = true
    return this
  }

  setHeight(height) {
    this.height = height
    return this
  }
}

const luke = new Jedi()

luke.jump().setHeight(20)
```

## 9.4 A custom `toString()` is fine as long as it's pure and
side-effect-free.

```js
class Jedi {
  constructor(options = {}) {
    this.name = options.name || 'no name'
  }

  getName() {
    return this.name
  }

  toString() {
    return `Jedi - ${this.getName()}`
  }
}
```

## 9.5 Omit constructors that add nothing beyond the default.

> Why? A default constructor already exists; an empty one, or one that
> only forwards to `super`, adds noise without adding behavior.

```js
// bad
class Jedi {
  constructor() {}

  getName() {
    return this.name
  }
}

// bad
class Rey extends Jedi {
  constructor(...args) {
    super(...args)
  }
}

// good
class Rey extends Jedi {
  constructor(...args) {
    super(...args)
    this.name = 'Rey'
  }
}
```

## 9.6 Never duplicate class member names.

> Why? A duplicate silently wins over the earlier one — almost always a
> copy-paste bug, not an intentional override.

```js
// bad
class Foo {
  bar() {
    return 1
  }

  bar() {
    return 2
  }
}

// good
class Foo {
  bar() {
    return 2
  }
}
```

## 9.7 An instance method should use `this`; otherwise make it `static`.

> Why? Being an instance method signals "this behaves differently
> depending on the receiver." A method that ignores `this` is really a
> static utility wearing an instance-method costume.

```js
// bad
class Foo {
  bar() {
    console.log('bar')
  }
}

// good — this is used
class Foo {
  bar() {
    console.log(this.bar)
  }
}

// good — static methods aren't expected to use this
class Foo {
  static bar() {
    console.log('bar')
  }
}
```

## 9.8 Use private fields (`#field`) for state that is not part of the
public API.

> Why? Native private fields are enforced by the engine, not just by
> convention — unlike an `_underscored` name, code outside the class
> literally cannot read or write a `#field`.

```js
// bad — convention only, not enforced
class Counter {
  constructor() {
    this._count = 0
  }

  increment() {
    this._count += 1
    return this._count
  }
}

// good — enforced by the engine
class Counter {
  #count = 0

  increment() {
    this.#count += 1
    return this.#count
  }
}
```

## 9.9 Use a `static` initialization block for one-time setup that
depends on multiple static members.

> Why? A static block runs once at class definition time and can freely
> reference other private statics, which a field initializer alone often
> cannot express cleanly.

```js
class Config {
  static #defaults

  static {
    const base = { retries: 3, timeoutMs: 5000 }
    Config.#defaults = Object.freeze(base)
  }

  static get defaults() {
    return Config.#defaults
  }
}
```

## 9.10 Prefer composition over deep inheritance chains.

> Why? More than one level of `extends` tends to couple unrelated
> behavior and makes it hard to reason about which ancestor defines what.
> A small object made of composed behaviors is easier to test and reuse.

```js
// bad — forces every subclass through a rigid hierarchy
class Animal {}
class Pet extends Animal {}
class HouseDog extends Pet {}

// good — compose the behaviors a given object actually needs
function withBark(target) {
  return { ...target, bark: () => 'Woof!' }
}

function withLeash(target) {
  return { ...target, leash: true }
}

const houseDog = withLeash(withBark({ name: 'Fido' }))
```

---
