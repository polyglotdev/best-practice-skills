<!-- Part of the `best-practice-js` skill. See SKILL.md for the index. -->

# 9b. Constructors

This chapter covers the constructor-specific rules Airbnb splits out from
the general "Classes and Constructors" section — patterns that apply to the
`constructor` method itself and to the `super`/`this` handshake inside it.
Rules about the surrounding class body (methods, `#private` fields, static
members) live in [`09-classes-and-constructors.md`](./09-classes-and-constructors.md).

## 9b.1 Always call `super(...)` first in a subclass constructor, before touching `this`.

> Why? `this` is uninitialized until `super()` returns. Accessing or
> assigning to `this` before `super()` throws a `ReferenceError`, and
> passing arguments after touching `this` is a common source of subtle
> initialization bugs.

```js
// bad
class Doge extends Animal {
  constructor(name) {
    this.name = name
    super()
  }
}

// good
class Doge extends Animal {
  constructor(name) {
    super()
    this.name = name
  }
}
```

## 9b.2 Do not write an empty `constructor` or one that only forwards its arguments to `super`.

> Why? Classes have a default constructor that does exactly this. Writing
> it by hand is noise — and worse, it invites drift when the parent's
> signature changes.

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

## 9b.3 Never reassign `this` inside a constructor.

> Why? Assigning to `this` (`this = something`) is a syntax error; the
> older workaround `const self = this` is unnecessary in ES2022+ because
> arrow functions, class fields, and `#private` methods already close over
> `this` correctly.

```js
// bad
class Foo {
  constructor() {
    const self = this
    this.on('click', function () {
      self.handle()
    })
  }
}

// good
class Foo {
  constructor() {
    this.on('click', () => this.handle())
  }
}
```

## 9b.4 Do initialization in the constructor, not as side effects at module load.

> Why? Side effects at module load run once at import time in an order the
> caller can't control and break tree-shaking. Constructors run when the
> caller decides to instantiate, which is the point of a class.

```js
// bad
const cache = new Map()
loadFromDisk(cache) // runs at import time

class UserCache {
  get(id) {
    return cache.get(id)
  }
}

// good
class UserCache {
  #cache = new Map()

  constructor({ loader } = {}) {
    if (loader) loader(this.#cache)
  }

  get(id) {
    return this.#cache.get(id)
  }
}
```

## 9b.5 Prefer class fields over assigning defaults in the constructor.

> Why? Class fields declare the object's shape at the top of the class —
> readable by humans, tools, and V8's hidden-class optimizer. Constructor
> assignment scatters the shape across a procedural body.

```js
// bad
class Counter {
  constructor(start = 0) {
    this.value = start
    this.max = Infinity
    this.step = 1
  }
}

// good
class Counter {
  value = 0
  max = Infinity
  step = 1

  constructor(start = 0) {
    this.value = start
  }
}
```

## 9b.6 Use `#private` fields for real privacy; do not rely on the `_leadingUnderscore` convention.

> Why? `#private` is enforced by the engine — access from outside the
> class is a `SyntaxError` at parse time. `_foo` is a convention that
> nothing checks. In a constructor, prefer initializing `#private` fields
> directly.

```js
// bad
class Session {
  constructor(token) {
    this._token = token
  }
}

// good
class Session {
  #token

  constructor(token) {
    this.#token = token
  }

  isValid() {
    return this.#token != null
  }
}
```

## 9b.7 Validate constructor arguments; throw early on invalid input.

> Why? A constructor that accepts garbage produces objects that fail
> unpredictably later. Failing at construction time gives a stack trace at
> the actual point of misuse.

```js
// bad
class Interval {
  constructor(ms) {
    this.ms = ms
  }
}

// good
class Interval {
  constructor(ms) {
    if (!Number.isFinite(ms) || ms < 0) {
      throw new TypeError(
        `Interval: ms must be a non-negative finite number, got ${ms}`
      )
    }
    this.ms = ms
  }
}
```

## 9b.8 A constructor returns the new instance implicitly; never `return` a different value.

> Why? Returning a non-object from a constructor is silently ignored, and
> returning a different object silently substitutes it, breaking `instanceof`
> and any downstream code relying on the class's shape.

```js
// bad
class UserId {
  constructor(raw) {
    return String(raw)
  }
}

// good
class UserId {
  #value

  constructor(raw) {
    this.#value = String(raw)
  }

  toString() {
    return this.#value
  }
}
```

## 9b.9 Prefer static factory methods over overloaded constructors.

> Why? A single `constructor` with many argument shapes is hard to read
> and type. Named static factories document intent at the call site.

```js
// bad
class Duration {
  constructor(input) {
    if (typeof input === 'number') this.ms = input
    else if (typeof input === 'string') this.ms = parseIso(input)
    else if (input instanceof Date) this.ms = input.getTime()
    else throw new TypeError('bad input')
  }
}

// good
class Duration {
  #ms

  constructor(ms) {
    this.#ms = ms
  }

  static fromMs(ms) {
    return new Duration(ms)
  }

  static fromIso(str) {
    return new Duration(parseIso(str))
  }

  static fromDate(d) {
    return new Duration(d.getTime())
  }
}
```

## 9b.10 Do not do heavy or asynchronous work in a constructor.

> Why? Constructors cannot be `async`, and callers expect construction to
> be cheap and synchronous. Expose an async `init()`/`open()` or a static
> `async create()` factory instead.

```js
// bad
class DbClient {
  constructor(url) {
    this.conn = connectSync(url) // blocks the event loop
  }
}

// good
class DbClient {
  #conn

  constructor(conn) {
    this.#conn = conn
  }

  static async create(url) {
    const conn = await connect(url)
    return new DbClient(conn)
  }

  query(sql) {
    return this.#conn.query(sql)
  }
}
```
