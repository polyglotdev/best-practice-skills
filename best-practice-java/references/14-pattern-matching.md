<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 14. Pattern Matching

Java 21 is the first LTS release in which the whole pattern-matching story is
final. Pattern matching for `instanceof` shipped in Java 16; [record
patterns](https://openjdk.org/jeps/440) and [pattern matching for
`switch`](https://openjdk.org/jeps/441) were finalized in Java 21. None of them
need `--enable-preview`. This chapter draws from [Oracle's *Pattern Matching for
switch*](https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch.html),
[Oracle's *Record
Patterns*](https://docs.oracle.com/en/java/javase/21/language/record-patterns.html),
[JLS §6.3.1 (scope for pattern variables in
expressions)](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html),
and [JLS
§14.11.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html).

Two things are deliberately absent because they are **not final in Java 21**:
unnamed patterns and variables (the `_` placeholder,
[JEP 443](https://openjdk.org/jeps/443), preview in 21 and finalized in Java 22
as [JEP 456](https://openjdk.org/jeps/456)) and primitive type patterns, which
did not reach Java at all until the JDK 23 preview
([JEP 455](https://openjdk.org/jeps/455)). Every example below names every
binding, including the ones it does not use.

The other half of the story is [Chapter 13](13-sealed-types.md): pattern
matching earns its keep when the selector is a sealed hierarchy, because that is
when the compiler can prove a `switch` complete. General `switch` formatting and
control flow is [Chapter 23](23-control-structures-and-switch.md); `null` policy
is [Chapter 25](25-nullability.md). Examples reuse the `Shape` hierarchy from
[§13.1](13-sealed-types.md).

**Tool alignment:** Error Prone's `PatternMatchingInstanceof` ("This code can be
simplified to use a pattern-matching instanceof") and
`StatementSwitchToExpressionSwitch` ("This statement switch can be converted to
a new-style arrow switch") are both on by default and enforce rules 14.1 and
14.7, with `FallThrough` — also on by default — backing up 14.7. Error Prone's
`MissingCasesInEnumSwitch` covers exhaustiveness for `enum` selectors only and
says nothing about sealed hierarchies, so it does not enforce 14.16.
Checkstyle's `MissingSwitchDefault` contradicts rule 14.16 and must be disabled.

## 14.1 Replace an `instanceof` test followed by a cast with a type pattern.

> Why? The test-then-cast pair states the type twice and gives the compiler no
> way to relate the two statements, so an edit that changes one line but not the
> other produces a `ClassCastException` at run time. A type pattern binds the
> narrowed value in the same expression that proved the type, so the two can
> never disagree. **Violation — enforced by Error Prone
> `PatternMatchingInstanceof`.**

```java
// bad — the type appears twice and the cast is a separate, unverified step
if (obj instanceof String) {
  String s = (String) obj;
  System.out.println(s.length());
}

// good
if (obj instanceof String s) {
  System.out.println(s.length());
}
```

## 14.2 Let flow scoping own the binding; do not hoist a shadow variable to widen it.

> Why? A pattern variable is in scope exactly where the compiler can prove the
> match succeeded — [JLS
> §6.3.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html) calls
> this being "definitely matched." When the compiler refuses to let you name the
> binding somewhere, it is telling you the match might not have happened there,
> and hoisting a nullable local to escape that scope reintroduces exactly the
> `null` case the pattern was excluding.

```java
// bad — a nullable shadow exists purely to escape the pattern's scope, so
// every later use needs a null check the pattern already made unnecessary
String text = null;
if (obj instanceof String s) {
  text = s;
}
if (text != null) {
  process(text);
}

// good
if (obj instanceof String s) {
  process(s);
}
```

## 14.3 Refine a type pattern with `&&` in the same condition instead of nesting a second `if`.

> Why? [JLS
> §6.3.1.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html) puts
> a pattern variable introduced by the left operand of `&&` in scope for the
> right operand: "a pattern variable introduced by `a` when true is definitely
> matched at `b`." That turns "is it this type, and does it satisfy this
> property" into one readable condition rather than two levels of nesting.

```java
// bad — two nested ifs for one composite condition
if (obj instanceof String s) {
  if (!s.isEmpty()) {
    process(s);
  }
}

// good — the binding is live in the right operand of &&
if (obj instanceof String s && !s.isEmpty()) {
  process(s);
}

// good — the same rule makes a one-expression equals possible
@Override
public boolean equals(Object o) {
  return o instanceof Money other
      && amount.equals(other.amount)
      && currency.equals(other.currency);
}
```

## 14.4 Bind with a negated `instanceof` and an early exit to keep the happy path unindented.

> Why? [JLS
> §6.3.2.2](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html)
> introduces a pattern variable after an `if` when it "is introduced by `e` when
> false and `S` cannot complete normally," so a negated `instanceof` guarding a
> `throw` or `return` binds the variable for the *entire rest of the method*.
> That turns a method whose whole body sits inside a type test into a guard
> clause plus flat code, matching every other guard the method already has.

```java
// bad — the entire method body is indented inside a type test
void handle(Object message) {
  if (message instanceof TextFrame frame) {
    validate(frame.text());
    publish(frame.text());
    audit(frame);
  }
}

// good — the then-block cannot complete normally, so frame is bound below it
void handle(Object message) {
  if (!(message instanceof TextFrame frame)) {
    throw new IllegalArgumentException("expected a text frame: " + message);
  }
  validate(frame.text());
  publish(frame.text());
  audit(frame);
}
```

## 14.5 Know the `||` flow-scoping rule: a binding from a *negated* left operand is live in the right operand.

> Why? [JLS
> §6.3.1.2](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html)
> states it precisely: for `a || b`, "a pattern variable introduced by `a` when
> false is definitely matched at `b`." Because `||` only evaluates its right
> operand when the left was false, the binding that survives is the one
> introduced *when false* — so the useful form is `!(x instanceof T t) || ...`,
> never `x instanceof T t || ...`, and "cannot find symbol" is the only hint the
> compiler gives.

```java
// bad — s is not in scope: the right operand is only reached when the left
// operand was false, i.e. when obj was NOT a String
static boolean isShortText(Object obj) {
  return obj instanceof String s || s.length() <= 10;   // error: cannot find symbol
}

// good — the negation makes the right operand the "match succeeded" branch
static boolean isShortText(Object obj) {
  return !(obj instanceof String s) || s.length() <= 10;
}
```

## 14.6 Replace an `instanceof` ladder of three or more branches with a pattern `switch`.

> Why? An `if`/`else if` chain over types is a hand-rolled dispatch table no tool
> can check: nothing tells you a branch is unreachable because an earlier one
> covers it, and nothing tells you a case is missing. A `switch` gets both checks
> from the compiler — dominance (14.13) and exhaustiveness (14.16) — and over a
> sealed selector it needs no fallback arm at all.

```java
// bad — an unchecked dispatch ladder; the trailing return is the only thing
// standing between you and a missing case
static String describe(Object obj) {
  if (obj instanceof Integer i) {
    return "int " + i;
  } else if (obj instanceof Long l) {
    return "long " + l;
  } else if (obj instanceof String s) {
    return "string " + s;
  }
  return "unknown";
}

// good — Object is not sealed, so default is genuinely required here
static String describe(Object obj) {
  return switch (obj) {
    case Integer i -> "int " + i;
    case Long l -> "long " + l;
    case String s -> "string " + s;
    default -> "unknown";
  };
}
```

## 14.7 Write every pattern `switch` in arrow form, and prefer a `switch` expression to a `switch` statement.

> Why? Google Java Style
> [§4.8.4.2](https://google.github.io/styleguide/javaguide.html#s4.8.4.2-switch-fall-through)
> notes that "there is no fall-through in new-style switches," removing the whole
> class of missing-`break` bugs, while colon form forces a mutable local plus a
> `break` per arm. [JLS
> §14.11.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html) also
> makes it a compile-time error to fall through into a `case` pattern that
> declares pattern variables, so colon form with patterns buys nothing.
> **Violation — enforced by Error Prone `StatementSwitchToExpressionSwitch`.**

```java
// bad — a mutable local, a break per arm, and a default that exists only to
// satisfy definite assignment
static String label(Shape shape) {
  String result;
  switch (shape) {
    case Circle c:
      result = "circle";
      break;
    case Rectangle r:
      result = "rectangle";
      break;
    default:
      throw new AssertionError(shape);
  }
  return result;
}

// good — exhaustive, no default, no mutable local
static String label(Shape shape) {
  return switch (shape) {
    case Circle c -> "circle";
    case Rectangle r -> "rectangle";
    case Triangle t -> "triangle";
  };
}
```

## 14.8 Deconstruct a record with a record pattern instead of calling accessors in the arm body.

> Why? A record pattern names the components in the label, so the arm reads as
> the data it operates on rather than as a chain of getter calls on a binding
> whose only purpose is to be dereferenced. It also removes a name the reader has
> to track: `case Circle(double radius)` puts one thing in scope, `case Circle c`
> puts the record *and* its components in play.

```java
// bad — the type pattern binds a value that exists only to be taken apart
static String render(Shape shape) {
  return switch (shape) {
    case Circle c -> "circle r=" + c.radius();
    case Rectangle r -> "rect " + r.width() + "x" + r.height();
    case Triangle t -> "tri " + t.base() + "x" + t.height();
  };
}

// good
static String render(Shape shape) {
  return switch (shape) {
    case Circle(double radius) -> "circle r=" + radius;
    case Rectangle(double width, double height) -> "rect " + width + "x" + height;
    case Triangle(double base, double height) -> "tri " + base + "x" + height;
  };
}
```

## 14.9 Nest record patterns to reach nested components in a single label.

> Why? Oracle's record patterns guide is explicit: "You can nest a record
> pattern inside another record pattern," with the compiler inferring component
> types at every level. Nesting collapses a chain of accessor calls into one
> declarative shape and eliminates the repeated intermediate dereferences
> (`line.end().x()`, `line.end().y()`) that are easy to get subtly wrong.

```java
public record Point(int x, int y) {}
public record Line(Point start, Point end) {}

// bad — two levels of accessors to reach four ints, each one repeated
static int manhattan(Object obj) {
  if (obj instanceof Line line) {
    return Math.abs(line.end().x() - line.start().x())
        + Math.abs(line.end().y() - line.start().y());
  }
  return -1;
}

// good — one nested pattern names all four components
static int manhattan(Object obj) {
  if (obj instanceof Line(Point(int x1, int y1), Point(int x2, int y2))) {
    return Math.abs(x2 - x1) + Math.abs(y2 - y1);
  }
  return -1;
}
```

## 14.10 Use `var` in a record pattern only when the component's type is irrelevant to the arm.

> Why? Oracle's guide notes that "You can use `var` in the record pattern's
> component list," and that the compiler then "infers that the pattern variables
> `x` and `y` are of type `double`" — but the arm's reader does not have the
> compiler. `var` is right for coordinates and identifiers whose exact type does
> not change the logic, and wrong the moment the arm's behaviour depends on the
> type's semantics, because it hides the one fact a reviewer needs to check.

```java
public record Money(BigDecimal amount, Currency currency) {}

// bad — the arm's correctness depends on BigDecimal scale semantics, and var
// hides which type is in play
case Money(var amount, var currency) ->
    amount.setScale(2, RoundingMode.HALF_UP) + " " + currency.getCurrencyCode();

// good — the type is load-bearing, so spell it
case Money(BigDecimal amount, Currency currency) ->
    amount.setScale(2, RoundingMode.HALF_UP) + " " + currency.getCurrencyCode();

// good — var is right here: the arithmetic is identical whatever the component
// types are, and Point states them one line away
case Line(Point(var x1, var y1), Point(var x2, var y2)) ->
    Math.abs(x2 - x1) + Math.abs(y2 - y1);
```

## 14.11 Express a conditional arm as a `when` guard rather than an `if` inside the arm body.

> Why? A guard is part of the label, so it participates in dispatch: the arm
> either applies or it does not, and the next label gets its chance. An `if`
> inside a block arm has already consumed the case, so every remaining
> possibility must be handled inside that block — which is how a two-line
> `switch` grows a nested `yield` ladder and stops being an expression.

```java
// bad — the condition hides inside the arm, so the label lies: it reads as
// "all Integers" and the real branching happens a level down
static String classify(Object obj) {
  return switch (obj) {
    case Integer i -> {
      if (i < 0) {
        yield "negative";
      }
      yield "non-negative";
    }
    default -> "other";
  };
}

// good
static String classify(Object obj) {
  return switch (obj) {
    case Integer i when i < 0 -> "negative";
    case Integer i -> "non-negative";
    default -> "other";
  };
}
```

## 14.12 Put a guarded label before the unguarded label it refines.

> Why? [JLS
> §14.11.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html)
> makes "a guarded `case` label with a `case` pattern ... dominated by a `case`
> label with the same pattern but without the guard," so the unguarded arm first
> is a compile error for the *same* pattern. Across *different* patterns the
> compiler cannot help — Oracle's guide states that "Guarded patterns aren't
> checked for dominance because they're generally undecidable," and recommends
> constant labels first, then guarded pattern labels, then nonguarded pattern
> labels. Get it wrong there and you get a silently unreachable arm, not an
> error.

```java
// bad — the unguarded String arm dominates the guarded one; does not compile
static String classify(Object obj) {
  return switch (obj) {
    case String s -> "string";
    case String s when s.isEmpty() -> "empty string";
    default -> "other";
  };
}

// good — most constrained first
static String classify(Object obj) {
  return switch (obj) {
    case String s when s.isEmpty() -> "empty string";
    case String s -> "string";
    default -> "other";
  };
}
```

## 14.13 Order type patterns most specific first — a dominated label is a compile error.

> Why? [JLS
> §14.11.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html)
> defines a label as dominated when "for every value that it applies to, it can
> be determined that one of the preceding switch labels would also apply," and
> "it is a compile-time error if any switch label in a switch block is
> dominated." A supertype pattern above a subtype pattern does not merely make
> the lower arm dead, it fails the build; reading the arms top-to-bottom as a
> narrowing sequence is the habit that prevents it.

```java
// bad — CharSequence dominates String, so the String arm is unreachable and
// the switch does not compile
static String describe(Object obj) {
  return switch (obj) {
    case CharSequence cs -> "text";
    case String s -> "string";
    default -> "other";
  };
}

// good
static String describe(Object obj) {
  return switch (obj) {
    case String s -> "string";
    case CharSequence cs -> "text";
    default -> "other";
  };
}
```

## 14.14 Handle `null` inside the `switch` with a `case null` label, not with a check before it.

> Why? Before Java 21 a `switch` always threw `NullPointerException` on a null
> selector, and that is unchanged when no `null` label is present — [JLS
> §14.11.3](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html) says
> that if no switch label applies and "the value of the selector expression is
> null, then a `NullPointerException` is thrown." A `case null` label is the only
> thing that changes it, and folding the null branch into the `switch` keeps
> every outcome of one dispatch in one construct rather than in a guard clause a
> later edit can drop.

```java
// bad — the null branch lives outside the dispatch; delete the guard clause in
// a refactor and the switch starts throwing NullPointerException
static String describe(Object obj) {
  if (obj == null) {
    return "nothing";
  }
  return switch (obj) {
    case String s -> "string";
    default -> "other";
  };
}

// good
static String describe(Object obj) {
  return switch (obj) {
    case null -> "nothing";
    case String s -> "string";
    default -> "other";
  };
}
```

## 14.15 Collapse a shared null-and-fallback outcome into `case null, default`.

> Why? [JLS
> §14.11.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html)
> permits exactly one combination with the `null` literal: "a `case` label with
> a `null` literal may have an optional `default`." When null and "anything else"
> genuinely deserve the same answer, `case null, default` says so in one place;
> two arms with identical bodies at opposite ends of the `switch` invite a fix to
> one that misses the other.

```java
// bad — two arms with the same body, far apart
static Level levelOf(Object obj) {
  return switch (obj) {
    case null -> Level.UNKNOWN;
    case Integer i when i > 90 -> Level.HIGH;
    case Integer i -> Level.LOW;
    default -> Level.UNKNOWN;
  };
}

// good
static Level levelOf(Object obj) {
  return switch (obj) {
    case Integer i when i > 90 -> Level.HIGH;
    case Integer i -> Level.LOW;
    case null, default -> Level.UNKNOWN;
  };
}
```

## 14.16 Omit `default` from a pattern `switch` over a sealed hierarchy.

> Why? Over a sealed selector the compiler already proves exhaustiveness — [JLS
> §14.11.1.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html)
> says a `default` label is "permitted, but not required, in the case where the
> switch block exhausts all the permitted direct subclasses and subinterfaces."
> Adding one anyway converts the compile error you would get when a subtype is
> added into a silently wrong runtime answer. This restates
> [§13.11](13-sealed-types.md) because this is where most people break it.
> **Suggestion — no shipped check covers the sealed case, and Checkstyle's
> `MissingSwitchDefault` demands the opposite.**

```java
// bad — a newly permitted Shape lands in default and reports zero
static double area(Shape shape) {
  return switch (shape) {
    case Circle(double radius) -> Math.PI * radius * radius;
    case Rectangle(double width, double height) -> width * height;
    default -> 0.0;
  };
}

// good — adding a Shape breaks this method at compile time
static double area(Shape shape) {
  return switch (shape) {
    case Circle(double radius) -> Math.PI * radius * radius;
    case Rectangle(double width, double height) -> width * height;
    case Triangle(double base, double height) -> 0.5 * base * height;
  };
}
```

## 14.17 Remember that a record pattern never matches `null`, but a nested type pattern binds it.

> Why? Oracle's record patterns guide is explicit: "The `null` value does not
> match any record pattern," and [JLS
> §14.30.3](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html) adds
> that "no record pattern is unconditional because the null reference does not
> match any record pattern." A nested *type* pattern does the opposite: [JLS
> §14.30.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html) calls
> such a pattern "null matching" when it is unconditional for the component's
> declared type, and §14.30.2 then says the null reference matches it. So in
> `Order(String id, Customer(String name))` a null `customer` drops the arm
> entirely, while a null `name` matches and binds to `null` — two opposite
> outcomes one line apart. The
> [`MatchException` Javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/MatchException.html)
> spells out the same pair: a nested record pattern "does not match against the
> result of `new R(null)` (whereas it does match against the result of
> `new R(new S(null))`)". Only a guard separates a binding that *is* `null` from
> a match that never happened; a `null` literal is not a pattern and cannot
> appear as a component.

```java
public record Customer(String name) {}
public record Order(String id, Customer customer) {}

// bad — an Order whose customer is null drops silently to the default, while
// an Order whose customer has a null name takes this arm and prints
// "hello null"; neither outcome is what the label appears to promise
static String greet(Object obj) {
  return switch (obj) {
    case Order(String id, Customer(String name)) -> "hello " + name;
    default -> "unrecognised input";
  };
}

// good — the guard separates a name bound to null from a match that never
// happened, and the last Order arm's nested type pattern is null matching, so
// it is the arm that catches a null customer
static String greet(Object obj) {
  return switch (obj) {
    case Order(String id, Customer(String name)) when name != null ->
        "hello " + name;
    case Order(String id, Customer(String name)) ->
        "order " + id + ": customer is unnamed";
    case Order(String id, Customer customer) ->
        "order " + id + ": no customer";
    default -> "unrecognised input";
  };
}
```

## 14.18 Do not pattern-match on behaviour the type hierarchy already owns.

> Why? A `switch` externalises an operation; a virtual method internalises it,
> and Effective Java, 3rd ed., Item 20 still applies — behaviour that is part of
> a type's own contract and lives in the same module as the types is a method.
> Switching on it spreads one type's logic across every call site, so adding a
> subtype means editing code that has nothing to do with the new type. Reach for
> a `switch` when the operation is *about* the data rather than *part of* it:
> rendering, serialising, routing, reporting.

```java
// bad — pricing is intrinsic to a Product, but it is implemented three
// packages away and every new Product means editing this method
static BigDecimal grossPrice(Product product) {
  return switch (product) {
    case Book b -> b.basePrice().multiply(REDUCED_VAT);
    case Ebook e -> e.basePrice().multiply(STANDARD_VAT);
    case Software s -> s.basePrice().multiply(STANDARD_VAT);
  };
}

// good — the operation belongs to the type, so a new Product cannot forget it
public sealed interface Product permits Book, Ebook, Software {
  BigDecimal basePrice();

  BigDecimal vatRate();

  default BigDecimal grossPrice() {
    return basePrice().multiply(vatRate());
  }
}

// good — presentation is not the model's job and lives in the web module, so
// this one genuinely belongs in a switch
static String renderRow(Product product) {
  return switch (product) {
    case Book(String title, BigDecimal basePrice) -> "BOOK " + title;
    case Ebook(String title, BigDecimal basePrice) -> "EPUB " + title;
    case Software(String name, BigDecimal basePrice) -> "APP " + name;
  };
}
```

## 14.19 Do not use pattern matching to recover types an `Object`-typed API threw away.

> Why? An API that accepts `Object` and then pattern-matches its way back to the
> three types it actually supports has moved a compile-time check to run time for
> no benefit — the signature is the documentation, and `Object` documents
> nothing. Fix the parameter type, a sealed interface if the set is closed
> ([Chapter 13](13-sealed-types.md)) or a bounded generic if it is open, and the
> `switch` either disappears or becomes exhaustive.

```java
// bad — the signature accepts anything, so every caller mistake is a runtime
// discovery and the fallback arm is untestable
void publish(Object payload) {
  if (payload instanceof OrderCreated e) {
    topic.send("orders.created", e);
  } else if (payload instanceof OrderCancelled e) {
    topic.send("orders.cancelled", e);
  } else {
    throw new IllegalArgumentException("unsupported payload: " + payload);
  }
}

// good — the type says what is accepted, and the switch is exhaustive
public sealed interface OrderEvent permits OrderCreated, OrderCancelled {}

void publish(OrderEvent payload) {
  String topicName =
      switch (payload) {
        case OrderCreated e -> "orders.created";
        case OrderCancelled e -> "orders.cancelled";
      };
  topic.send(topicName, payload);
}
```
