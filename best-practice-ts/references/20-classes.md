<!-- Part of the `best-practice-ts` skill. See SKILL.md for the index. -->

# 20. Classes

## 20.1 Use native `#private` fields for true runtime privacy; use the `private` keyword only when the field must still participate in structural typing checks or decorators that require it.

> Why? `private` is erased at compile time — the field is still a plain
> enumerable property at runtime and accessible via bracket notation or
> `JSON.stringify`. `#private` fields are truly inaccessible outside the
> class, matching the intent of "private."

```ts
// bad — accessible at runtime despite `private`
class Account {
  private balance = 0
}
console.log((new Account() as any).balance) // 0 — no actual protection

// good
class Account {
  #balance = 0
  deposit(amount: number) {
    this.#balance += amount
  }
}
```

## 20.2 Use `protected` only for members explicitly designed to be overridden or read by subclasses, and pair every override with `override`.

> Why? `noImplicitOverride` (Chapter 1) requires the `override` keyword on
> any method that overrides a base class member, which prevents accidental
> shadowing when a base class renames or removes a method.

```ts
// bad
class Base {
  greet() {
    return 'Hello'
  }
}
class Derived extends Base {
  greet() {
    return 'Hi'
  }
}

// good
class Base {
  greet() {
    return 'Hello'
  }
}
class Derived extends Base {
  override greet() {
    return 'Hi'
  }
}
```

## 20.3 Use `abstract` classes to share implementation between related subclasses; use an `interface` when there is no shared implementation to provide.

> Why? An `abstract` class can hold shared, non-overridden logic alongside
> the abstract contract; an `interface` cannot hold any implementation at
> all, so forcing shared logic into one adds an unnecessary base class with
> no payoff.

```ts
// good
abstract class Shape {
  abstract area(): number
  describe(): string {
    return `Area: ${this.area()}`
  }
}
class Circle extends Shape {
  constructor(private radius: number) {
    super()
  }
  override area(): number {
    return Math.PI * this.radius ** 2
  }
}
```

## 20.4 Use parameter properties for simple, direct field assignment in a constructor; fall back to explicit field declarations plus manual assignment once the constructor needs extra logic per field.

> Why? Parameter properties eliminate boilerplate for the common case, but
> mixing computed assignment into the same constructor obscures which
> fields are plain copies and which are derived.

```ts
// good — simple, all direct copies
class Point {
  constructor(
    public readonly x: number,
    public readonly y: number
  ) {}
}

// good — one field is derived, so all fields are explicit for clarity
class NormalizedVector {
  readonly x: number
  readonly y: number
  readonly magnitude: number
  constructor(x: number, y: number) {
    this.magnitude = Math.sqrt(x ** 2 + y ** 2)
    this.x = x / this.magnitude
    this.y = y / this.magnitude
  }
}
```

## 20.5 Prefer composition and small classes implementing narrow interfaces over deep inheritance hierarchies.

> Why? This is the same rationale as `best-practice-js`'s class guidance,
> restated for the type layer: a narrow interface is easy to type-check
> against and easy to fake in tests, whereas a deep inheritance chain
> couples every subclass to the full ancestor chain's types.

```ts
// good
interface Logger {
  log(message: string): void
}
class ConsoleLogger implements Logger {
  log(message: string) {
    console.log(message)
  }
}
class Service {
  constructor(private readonly logger: Logger) {}
}
```
