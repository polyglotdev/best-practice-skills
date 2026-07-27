<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 13. Sealed Types

A `sealed` class or interface names, in its own declaration, the complete list
of types permitted to extend or implement it. Sealing was finalized in Java 17
by [JEP 409](https://openjdk.org/jeps/409) and is a normal, non-preview part of
the Java 21 language. This chapter draws from [Oracle's *Sealed Classes and
Interfaces*](https://docs.oracle.com/en/java/javase/21/language/sealed-classes-and-interfaces.html),
[JLS §14.11.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html),
and Google Java Style
[§4.8.4.3](https://google.github.io/styleguide/javaguide.html#s4.8.4.3-switch-default),
which "requires every switch to be exhaustive, even those where the language
itself does not require it."

Sealing exists for one payoff above all others: the compiler gets a closed list
it can reason about, so a `switch` over the hierarchy is provably exhaustive
**without** a `default` label, and adding a permitted subtype later turns every
such `switch` into a compile error. Rules 13.11 through 13.14 are that payoff;
everything before them is how to build a hierarchy that earns it.

This chapter covers the *shape* of a sealed hierarchy. The syntax of matching
over one — type patterns, record patterns, guards, `case null`, dominance — is
[Chapter 14](14-pattern-matching.md). Record design is
[Chapter 12](12-records.md), enum design is
[Chapter 15](15-enums-and-annotations.md), and general inheritance discipline is
[Chapter 11](11-classes-and-interfaces.md). Most examples reuse the `Shape`
hierarchy declared in 13.1.

**Tool alignment:** Checkstyle's `MissingSwitchDefault` check directly
contradicts rule 13.11 and must be **disabled** in any project using sealed
hierarchies — it demands a `default` label on every `switch`, which is exactly
what destroys compile-time exhaustiveness. Error Prone's
`UnnecessaryDefaultInEnumSwitch` makes the equivalent point for `enum`
selectors but does not cover sealed types, so the sealed case is a
**Suggestion** with no shipped check behind it today.

## 13.1 Seal a type hierarchy whenever the set of direct subtypes is fixed and known at compile time.

> Why? [JEP 409](https://openjdk.org/jeps/409) gives as its first goal: "Allow
> the author of a class or interface to control which code is responsible for
> implementing it." An unsealed abstract type says "anyone may add a case," a
> sealed one says "these are all the cases." Without it every `switch` needs a
> defensive `default` arm that can only guess, and no tool can tell you which
> call sites you missed when the hierarchy grows.

```java
// bad — nothing says these are the only shapes
public interface Shape {}

// good — the parent declares the complete list
public sealed interface Shape permits Circle, Rectangle, Triangle {}
public record Circle(double radius) implements Shape {}
public record Rectangle(double width, double height) implements Shape {}
public record Triangle(double base, double height) implements Shape {}
```

## 13.2 Declare the sealed parent as an `interface` unless the subtypes must share implementation state.

> Why? Effective Java, 3rd ed., Item 20 ("Prefer interfaces to abstract
> classes") applies unchanged to sealed types: a sealed interface leaves each
> permitted subtype free to be a `record`, to extend something else, and to pick
> its own representation. A sealed abstract class burns the subtypes' single
> inheritance slot and imposes a constructor contract on all of them for fields
> only some of them need.

```java
// bad — an abstract class blocks the subtypes from being records and consumes
// their one inheritance slot
public abstract sealed class Event permits UserCreated, UserDeleted {
  private final Instant occurredAt;

  protected Event(Instant occurredAt) {
    this.occurredAt = occurredAt;
  }
}

// good — the shared accessor is a contract, not inherited state
public sealed interface Event permits UserCreated, UserDeleted {
  Instant occurredAt();
}

public record UserCreated(String userId, Instant occurredAt) implements Event {}
```

## 13.3 Give every permitted subtype exactly one of `final`, `sealed`, or `non-sealed`, and choose it deliberately.

> Why? The language requires one of the three, but cannot tell you which one you
> meant: `final` closes the branch, `sealed` re-narrows it to another known list,
> `non-sealed` reopens it to the world. Records and enums are implicitly `final`,
> which is why the record idiom in 13.5 needs no modifier at all. Picking
> whichever one makes the error disappear is how a hierarchy designed closed
> silently becomes open.

```java
// bad — no modifier on CreateOrder; this does not compile
public sealed interface Command permits CreateOrder, CancelOrder {}
public class CreateOrder implements Command {}

// good — one deliberate choice per branch
public sealed interface Command permits CreateOrder, CancelOrder, ReportCommand {}
public record CreateOrder(String orderId) implements Command {}
public record CancelOrder(String orderId) implements Command {}
public sealed interface ReportCommand extends Command permits DailyReport, AdHoc {}
```

## 13.4 Use `non-sealed` only where a branch genuinely needs extension by code you do not control.

> Why? `non-sealed` reopens a branch to arbitrary subclasses; exhaustiveness of
> the parent `switch` survives, but every assumption an arm made about that
> subtype's *behaviour* is now at the mercy of code you have never seen.
> Effective Java, 3rd ed., Item 19 applies in full — a `non-sealed` type must be
> designed and documented for inheritance, or be `final`. Reaching for
> `non-sealed` to silence a compiler error is the most common way sealing gets
> thrown away.

```java
// bad — non-sealed applied reflexively to types nobody outside this package
// ever extends, discarding the guarantee sealing was added for
public non-sealed class CreateOrder implements Command {}
public non-sealed class CancelOrder implements Command {}

// good — implicitly final via record where extension is unwanted; non-sealed
// only at the one place that is a real extension point
public record CreateOrder(String orderId) implements Command {}

/** Extension point for third-party command plugins. */
public non-sealed interface PluginCommand extends Command {
  String pluginId();
}
```

## 13.5 Model a closed set of alternatives as a `sealed interface` plus `record` subtypes.

> Why? This pairing is the algebraic data type idiom in Java 21: the sealed
> interface is the sum ("one of these"), each record is the product ("all of
> these fields"). Records are implicitly `final`, so they satisfy 13.3 with no
> extra modifier, and they are deconstructible by record patterns
> ([Chapter 14](14-pattern-matching.md)). A hand-written class in that slot gives
> up both properties and owes you an equality contract that will drift from its
> fields.

```java
// bad — a hand-written carrier: not deconstructible, and its equals/hashCode
// are now your problem
public final class Success implements Result {
  private final String value;

  public Success(String value) {
    this.value = value;
  }

  public String value() {
    return value;
  }
}

// good
public sealed interface Result permits Success, Failure {}
public record Success(String value) implements Result {}
public record Failure(String code, String message) implements Result {}
```

## 13.6 Omit the `permits` clause when every permitted subtype is in the same file; write it explicitly once they are not.

> Why? Oracle's guide states the rule directly: "you can define permitted
> subclasses in the same file as the sealed class. If you do so, then you can
> omit the `permits` clause" — and a list that repeats declarations two lines
> below it is a second copy of the truth that can drift from the first. Once the
> subtypes move into their own files the clause becomes the only place a reader
> sees the complete set, and the thing that makes adding a subtype visible in
> the parent's diff.

```java
// bad — permits restates what the very next lines already declare
public sealed interface Shape permits Shape.Circle, Shape.Rectangle {
  record Circle(double radius) implements Shape {}

  record Rectangle(double width, double height) implements Shape {}
}

// good — same file, so the list is inferred
public sealed interface Shape {
  record Circle(double radius) implements Shape {}

  record Rectangle(double width, double height) implements Shape {}
}

// good — separate files, so the clause is the documented contract
public sealed interface Shape permits Circle, Rectangle, Triangle {}
```

## 13.7 Keep the sealed parent and every permitted subtype in the same package, unless the code is in a named module.

> Why? Oracle's guide states the constraint: permitted subtypes "must be in the
> same module as the sealed class (if the sealed class is in a named module) or
> in the same package (if the sealed class is in the unnamed module)." Most
> application code runs on the classpath, which *is* the unnamed module, so
> scattering a sealed hierarchy across packages there is a compile error rather
> than a style preference.

```java
// bad — on the classpath, permitted subtypes must share the parent's package
package com.example.geometry;

public sealed interface Shape permits com.example.geometry.impl.Circle {}

// good
package com.example.geometry;

public sealed interface Shape permits Circle, Rectangle, Triangle {}
```

## 13.8 Name only *direct* subtypes in `permits`; seal each level of a deeper hierarchy separately.

> Why? Oracle's guide requires permitted subtypes to be "accessible by the
> sealed class at compile time" and to "directly extend the sealed class," so
> naming a grandchild does not compile. The instinct to fix that by flattening
> the hierarchy discards structure the model actually has; sealing is per-level,
> and each sealed type owns exactly its own direct children.

```java
// bad — Rounded extends Rectangle, not Shape; permits requires direct subtypes
public sealed interface Shape permits Rectangle, Rounded {}
public non-sealed class Rectangle implements Shape {}
public final class Rounded extends Rectangle {}

// good — each level owns its own permits clause
public sealed interface Shape permits Rectangle {}
public sealed class Rectangle implements Shape permits Rounded {}
public final class Rounded extends Rectangle {}
```

## 13.9 Use an `enum` when the alternatives are fixed constants with no per-instance data; use a sealed hierarchy when they differ in shape.

> Why? Effective Java, 3rd ed., Item 34 is still right for a fixed set of
> singletons — an enum gives you `values()`, `valueOf`, `EnumMap`, `EnumSet`, and
> free serialization, none of which a sealed hierarchy provides. But an enum has
> *one shape for all constants*, so the moment the alternatives carry different
> data it forces every constant to declare fields only some of them populate: a
> nullable field per unused combination, with no compiler check that you read the
> right one.

```java
// bad — an enum tag plus a bag of fields, only a subset of which is non-null
// for any given constant
public enum PaymentMethodType {
  CARD,
  BANK_TRANSFER,
  STORE_CREDIT
}

public record Payment(
    PaymentMethodType type,
    String panLast4,     // card only
    YearMonth expiry,    // card only
    String iban,         // bank transfer only
    UUID voucherId) {}   // store credit only

// good — each alternative carries exactly its own data
public sealed interface PaymentMethod {
  record Card(String panLast4, YearMonth expiry) implements PaymentMethod {}

  record BankTransfer(String iban) implements PaymentMethod {}

  record StoreCredit(UUID voucherId) implements PaymentMethod {}
}

// good — still an enum: fixed constants, identical shape, no per-instance data
public enum Weekday {
  MONDAY,
  TUESDAY,
  WEDNESDAY,
  THURSDAY,
  FRIDAY
}
```

## 13.10 Replace the visitor pattern with a sealed hierarchy and an exhaustive `switch`.

> Why? Visitor exists to fake exhaustive dispatch over a closed hierarchy in a
> language that has none, and Java 21 has one. Visitor costs an `accept` method
> on every node, a `Visitor` interface that must be edited for every new node,
> and a fresh implementation class per operation — and it still cannot
> deconstruct the node's data. A sealed hierarchy plus a `switch` gets the same
> exhaustiveness check from the compiler with none of the machinery.

```java
// bad — an accept method per node, a Visitor interface every node's name leaks
// into, and one implementation class per operation
public interface Expr {
  <R> R accept(Visitor<R> visitor);

  interface Visitor<R> {
    R visitLiteral(Literal literal);

    R visitAdd(Add add);
  }
}

public record Literal(long value) implements Expr {
  @Override
  public <R> R accept(Expr.Visitor<R> visitor) {
    return visitor.visitLiteral(this);
  }
}

// good — no dispatch machinery at all
public sealed interface Expr {
  record Literal(long value) implements Expr {}

  record Add(Expr left, Expr right) implements Expr {}
}

static long eval(Expr expr) {
  return switch (expr) {
    case Expr.Literal(long value) -> value;
    case Expr.Add(Expr left, Expr right) -> eval(left) + eval(right);
  };
}
```

## 13.11 Switch over a sealed type without a `default` label.

> Why? The JLS permits but does not require a `default` "in the case where the
> switch block exhausts all the permitted direct subclasses and subinterfaces,"
> and Google Java Style §4.8.4.3 is already satisfied because the compiler has
> proved exhaustiveness. Adding `default` anyway converts a future compile error
> into a silently wrong runtime answer: the new subtype lands in the fallback arm
> and nothing tells you. **Suggestion — no shipped check covers the sealed case,
> and Checkstyle's `MissingSwitchDefault` demands the opposite.**

```java
// bad — the default arm absorbs any future Shape and returns a wrong area
static double area(Shape shape) {
  return switch (shape) {
    case Circle c -> Math.PI * c.radius() * c.radius();
    case Rectangle r -> r.width() * r.height();
    default -> 0.0;
  };
}

// good — no default; adding a Shape breaks this method at compile time
static double area(Shape shape) {
  return switch (shape) {
    case Circle(double radius) -> Math.PI * radius * radius;
    case Rectangle(double width, double height) -> width * height;
    case Triangle(double base, double height) -> 0.5 * base * height;
  };
}
```

## 13.12 Never write a catch-all type pattern for the sealed parent — it defeats exhaustiveness exactly like `default`.

> Why? `case Shape s ->` is a total type pattern over the selector, so it covers
> everything the earlier arms missed and the compiler stops asking for the rest.
> It is `default` wearing a type name, and harder to spot in review because it
> looks like a legitimate pattern. If you genuinely cannot handle a subtype, name
> it and throw — that arm still breaks the build when the hierarchy grows.

```java
// bad — a total pattern over the parent silences exhaustiveness checking
static double area(Shape shape) {
  return switch (shape) {
    case Circle(double radius) -> Math.PI * radius * radius;
    case Rectangle(double width, double height) -> width * height;
    case Shape s -> 0.0;
  };
}

// good — every subtype is named; unsupported ones fail loudly
static double area(Shape shape) {
  return switch (shape) {
    case Circle(double radius) -> Math.PI * radius * radius;
    case Rectangle(double width, double height) -> width * height;
    case Triangle t -> throw new UnsupportedOperationException("area of " + t);
  };
}
```

## 13.13 Treat the compile errors that appear when you add a permitted subtype as the feature you paid for.

> Why? Adding a name to `permits` and fixing every `switch` the compiler flags is
> the whole return on sealing: you get the exact, complete work list of call sites
> that need a decision. The failure mode is reaching for `default` — or a
> catch-all pattern — to get the build green again, which converts a list of
> known-incomplete call sites into a set of silently wrong ones you find in
> production instead.

```java
// good — this one-line change is a compile error at every switch over Shape
// until each one handles Hexagon
public sealed interface Shape permits Circle, Rectangle, Triangle, Hexagon {}
public record Hexagon(double sideLength) implements Shape {}

// good — the required follow-up is an explicit arm, never a default
static double area(Shape shape) {
  return switch (shape) {
    case Circle(double radius) -> Math.PI * radius * radius;
    case Rectangle(double width, double height) -> width * height;
    case Triangle(double base, double height) -> 0.5 * base * height;
    case Hexagon(double side) -> 1.5 * Math.sqrt(3.0) * side * side;
  };
}
```

## 13.14 Ship the sealed parent and every permitted subtype together across a module or artifact boundary.

> Why? Exhaustiveness is checked against the hierarchy the consumer can *see*, so
> exporting the parent without its subtypes leaves downstream code able to accept
> a `Shape` but unable to name `Circle` in a case label — forcing it back onto
> `default`. Worse, exhaustiveness is a compile-time judgement: a consumer
> compiled against one version and run against a newer one throws
> `MatchException`, which the
> [Javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/MatchException.html)
> lists as a "separate compilation anomaly."

```java
// bad — Shape is visible downstream but its subtypes are not, so no consumer
// can write an exhaustive switch
module com.example.geometry {
  exports com.example.geometry;         // Shape only
  // com.example.geometry.impl (Circle, Rectangle, Triangle) is not exported
}

// good — the whole closed hierarchy crosses the boundary together
module com.example.geometry {
  exports com.example.geometry;         // Shape, Circle, Rectangle, Triangle
}
```

## 13.15 Do not make a sealed interface a lambda target.

> Why? A lambda or anonymous class produces an implementing type that is not in
> the `permits` list, so it cannot implement a sealed interface at all. A sealed
> single-abstract-method interface therefore looks like a functional interface at
> the declaration site and rejects every lambda at the use site — if callers
> should supply behaviour inline, the type must not be sealed.

```java
// bad — reads as a functional interface, but no lambda can ever implement it
public sealed interface Validator permits NotBlank, MaxLength {
  boolean test(String value);
}

Validator v = s -> !s.isBlank();   // error: Validator is sealed

// good — an open functional interface where inline behaviour is wanted
@FunctionalInterface
public interface Validator {
  boolean test(String value);
}

Validator v = s -> !s.isBlank();
```

## 13.16 Do not dispatch reflectively over `Class.getPermittedSubclasses()`.

> Why? `Class.isSealed()` and `Class.getPermittedSubclasses()` exist for
> frameworks that must introspect a hierarchy they did not write — serializers,
> schema generators, documentation tools. Using them for ordinary dispatch throws
> away everything sealing bought: no exhaustiveness check, no record
> deconstruction, no compile error when a subtype is added, and a runtime failure
> where a `switch` would have given you a build failure.

```java
// bad — a registry keyed by class: nothing checks it is complete, and the gap
// surfaces as an exception in production
static double area(Shape shape) {
  ToDoubleFunction<Shape> fn = AREAS.get(shape.getClass());
  if (fn == null) {
    throw new IllegalStateException("no area function for " + shape.getClass());
  }
  return fn.applyAsDouble(shape);
}

// good
static double area(Shape shape) {
  return switch (shape) {
    case Circle(double radius) -> Math.PI * radius * radius;
    case Rectangle(double width, double height) -> width * height;
    case Triangle(double base, double height) -> 0.5 * base * height;
  };
}
```

## 13.17 Do not give the sealed parent a `default` method that returns a placeholder value.

> Why? A `default` method with a stand-in value is an abstract method with a
> wrong answer pre-loaded: a newly permitted subtype inherits it silently, and
> the failure is a plausible-looking `0`, `""`, or empty list rather than a build
> error — which throws away the guarantee 13.13 depends on. If every subtype must
> supply the behaviour, declare it abstract; if only some have it, it belongs in
> the `switch`, not on the parent.

```java
// bad — a newly permitted subtype silently reports zero area
public sealed interface Shape permits Circle, Rectangle, Triangle {
  default double area() {
    return 0.0;
  }
}

// good — abstract: a new subtype does not compile until it implements area()
public sealed interface Shape permits Circle, Rectangle, Triangle {
  double area();
}
```

## 13.18 Do not seal a type that is genuinely meant to be extended by code you do not own.

> Why? Sealing commits the parent's author to owning the complete subtype list
> forever, which is right for a domain model, a protocol message set, or a parse
> tree. It is wrong for a plugin SPI or a public extension point, where sealing
> is a compatibility trap: every new implementer becomes a change to *your*
> source, in *your* module, on *your* release schedule. Effective Java, 3rd ed.,
> Item 21 is the relevant discipline — sealing an extension point does not make
> it safer, it makes it unusable.

```java
// bad — an SPI that third parties are documented to implement cannot be sealed
/** Implement this to add a storage backend. */
public sealed interface StorageBackend permits S3Backend, LocalDiskBackend {
  InputStream open(String key) throws IOException;
}

// good — the extension point stays open; the closed internal command set is
// sealed on its own
/** Implement this to add a storage backend. */
public interface StorageBackend {
  InputStream open(String key) throws IOException;
}

sealed interface StorageCommand permits Put, Get, Delete {}
```
