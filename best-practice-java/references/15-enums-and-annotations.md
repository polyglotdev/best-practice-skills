<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 15. Enums & Annotations

Enums and annotations are the two ways Java lets you add vocabulary to the type
system without adding behavior-bearing subclasses. An enum names a fixed set of
values and gives them a type; an annotation names a fact about a declaration and
gives tools something to read. This chapter covers both, drawing on *Effective
Java, 3rd ed.*, Items 34–41, and on Google Java Style
[§4.8.1](https://google.github.io/styleguide/javaguide.html#s4.8.1-enum-classes),
[§4.8.4.3](https://google.github.io/styleguide/javaguide.html#s4.8.4.3-switch-default),
[§4.8.4.4](https://google.github.io/styleguide/javaguide.html#s4.8.4.4-switch-expressions),
and [§4.8.5](https://google.github.io/styleguide/javaguide.html#s4.8.5-annotations).

This chapter is about *closed sets of values*. When your alternatives carry
genuinely different shapes of state rather than different data for the same
shape, the right tool is a sealed hierarchy, not an enum — see
[Chapter 13](13-sealed-types.md). Destructuring those alternatives is
[Chapter 14](14-pattern-matching.md), and general `switch` form is
[Chapter 23](23-control-structures-and-switch.md). Naming rules for enum
constants and annotation types are [Chapter 3](03-naming.md); Javadoc
requirements are [Chapter 4](04-javadoc.md); the full rationale for `@Override`
is [Chapter 7](07-programming-practices.md).

**Tool alignment:** Checkstyle contributes `MissingDeprecated`,
`AnnotationLocation`, and a narrow `MissingOverride` (it fires only where the
`{@inheritDoc}` Javadoc tag is present, so it is not a substitute for the
general rule in 15.14); Error Prone contributes `ImmutableEnumChecker`,
`MissingCasesInEnumSwitch`, and its own, broader `MissingOverride`;
`javac -Xlint:deprecation,removal` flags use sites of deprecated API. Where a
rule is enforced, it is marked **Violation** rather than **Suggestion**.

## 15.1 Use an enum type instead of a group of `int` or `String` constants.

> Why? *Effective Java*, 3rd ed., Item 34: "Use enums instead of int
> constants." An `int` constant provides no type safety and no namespace — any
> `int` passes where an apple was expected — and the constant's name vanishes at
> compile time, so a log line shows `2` instead of `BLOOD_ORANGE`. `int`
> constants are also inlined into client class files, so changing a value
> requires recompiling every caller. An enum gives you a distinct type, a
> printable name, and reference equality that means something.

```java
// bad — addFruit(APPLE_FUJI, 3) and addFruit(3, APPLE_FUJI) both compile
public static final int APPLE_FUJI = 0;
public static final int ORANGE_NAVEL = 0;

public void addFruit(int apple, int count) { /* ... */ }

// good
public enum Apple {
  FUJI,
  PIPPIN,
  GRANNY_SMITH
}

public void addFruit(Apple apple, int count) { /* ... */ }
```

## 15.2 Store data associated with a constant in a `final` instance field, never derive it from `ordinal()`.

> Why? *Effective Java*, 3rd ed., Item 35: "Use instance fields instead of
> ordinals." `ordinal()` exists to support `EnumSet` and `EnumMap`; it is a
> positional accident, not a value. Reordering constants for readability
> silently changes every derived number, you cannot skip a value, and you cannot
> give two constants the same associated value. An instance field survives
> reordering, insertion, and deletion.

```java
// bad — reordering the constants silently changes every returned value
public enum Ensemble {
  SOLO,
  DUET,
  TRIO;

  public int numberOfMusicians() {
    return ordinal() + 1;
  }
}

// good — the number is data, declared next to the constant it belongs to
public enum Ensemble {
  SOLO(1),
  DUET(2),
  TRIO(3),
  DOUBLE_QUARTET(8);

  private final int numberOfMusicians;

  Ensemble(int numberOfMusicians) {
    this.numberOfMusicians = numberOfMusicians;
  }

  public int numberOfMusicians() {
    return numberOfMusicians;
  }
}
```

## 15.3 Keep every enum field `final` and deeply immutable.

> Why? Enum constants are process-wide singletons reachable from any thread with
> no synchronization, so a mutable field on an enum is shared mutable state with
> no owner and no lock. Error Prone's `ImmutableEnumChecker` exists precisely
> because this is a common and expensive mistake. Store collections as immutable
> copies, and put per-request state where it belongs — in the request.
> **Violation — enforced by Error Prone `ImmutableEnumChecker`.**

```java
// bad — a shared, unsynchronized, process-lifetime mutable field
public enum Region {
  EU,
  US;

  private List<String> activeZones = new ArrayList<>();
}

// good — the field is final and the collection is immutable
public enum Region {
  EU(List.of("eu-west-1", "eu-central-1")),
  US(List.of("us-east-1", "us-west-2"));

  private final List<String> zones;

  Region(List<String> zones) {
    this.zones = List.copyOf(zones);
  }

  public List<String> zones() {
    return zones;
  }
}
```

## 15.4 Give a constant its own behavior with a constant-specific method body, not a `switch` on `this`.

> Why? *Effective Java*, 3rd ed., Item 34 shows the failure directly: a `switch`
> over `this` compiles fine when you add a constant, then throws the first time
> that constant reaches the method. An abstract method with constant-specific
> bodies makes omitting the implementation a compile error, and keeps each
> constant's behavior next to the constant.

```java
// bad — adding a constant compiles, then throws in production
public enum Operation {
  PLUS,
  MINUS;

  public double apply(double x, double y) {
    return switch (this) {
      case PLUS -> x + y;
      case MINUS -> x - y;
      default -> throw new AssertionError("unknown operation: " + this);
    };
  }
}

// good — a constant without an apply body will not compile
public enum Operation {
  PLUS {
    @Override
    public double apply(double x, double y) {
      return x + y;
    }
  },
  MINUS {
    @Override
    public double apply(double x, double y) {
      return x - y;
    }
  };

  public abstract double apply(double x, double y);
}
```

## 15.5 When several constants share behavior, delegate to a nested strategy enum instead of duplicating constant bodies.

> Why? *Effective Java*, 3rd ed., Item 34 names this the *strategy enum*
> pattern. Constant-specific bodies (15.4) stop scaling once most constants want
> the same implementation: you either copy the body into every constant, or add
> a `switch` and reintroduce the failure mode 15.4 fixed. A nested strategy enum
> makes each new constant *choose* a strategy in its constructor — a compile-time
> obligation rather than a review comment.

```java
// bad — a new day that forgets to be listed silently gets the weekday rule
public enum PayrollDay {
  MONDAY,
  SATURDAY;

  public int overtimePay(int minutesWorked, int payRate) {
    return switch (this) {
      case SATURDAY -> minutesWorked * payRate / 2;
      default -> 0;
    };
  }
}

// good — the constructor makes choosing a pay type mandatory
public enum PayrollDay {
  MONDAY(PayType.WEEKDAY),
  SATURDAY(PayType.WEEKEND);

  private final PayType payType;

  PayrollDay(PayType payType) {
    this.payType = payType;
  }

  public int pay(int minutesWorked, int payRate) {
    return payType.pay(minutesWorked, payRate);
  }

  private enum PayType {
    WEEKDAY {
      @Override
      int overtimePay(int minutesWorked, int payRate) {
        return Math.max(0, minutesWorked - MINS_PER_SHIFT) * payRate / 2;
      }
    },
    WEEKEND {
      @Override
      int overtimePay(int minutesWorked, int payRate) {
        return minutesWorked * payRate / 2;
      }
    };

    private static final int MINS_PER_SHIFT = 8 * 60;

    abstract int overtimePay(int minutesWorked, int payRate);

    int pay(int minutesWorked, int payRate) {
      return minutesWorked * payRate + overtimePay(minutesWorked, payRate);
    }
  }
}
```

## 15.6 Represent a set of enum values with `EnumSet`, never with an `int` bit field.

> Why? *Effective Java*, 3rd ed., Item 36: "Use EnumSet instead of bit fields."
> `EnumSet` is a `Set` — it prints legibly, iterates, and interoperates with
> every collection API — while internally using a single `long` bit vector for
> enums of 64 or fewer constants, so it costs what the bit field cost. A bit
> field is an untyped `int`: it prints as `3`, cannot be iterated, and silently
> accepts a constant from an unrelated enum. In JDK 21 `EnumSet` is declared
> `public abstract sealed class EnumSet<E extends Enum<E>>`, so it has no public
> constructor; its static factories — `noneOf`, `allOf`, `of`, `range`,
> `copyOf`, and `complementOf` — are the only way to build one.

```java
// bad — untyped, unprintable, and silently accepts unrelated bits
public static final int STYLE_BOLD = 1 << 0;
public static final int STYLE_ITALIC = 1 << 1;

public void applyStyles(int styles) { /* ... */ }

// text.applyStyles(STYLE_BOLD | STYLE_ITALIC);

// good — accept Set<Style>, not EnumSet<Style>, so callers may pass any Set
public enum Style {
  BOLD,
  ITALIC,
  UNDERLINE
}

public void applyStyles(Set<Style> styles) { /* ... */ }

// text.applyStyles(EnumSet.of(Style.BOLD, Style.ITALIC));
```

## 15.7 Index by an enum with `EnumMap`, never with an array or list indexed by `ordinal()`.

> Why? *Effective Java*, 3rd ed., Item 37: "Use EnumMap instead of ordinal
> indexing." An `ordinal()`-indexed array needs an unchecked cast to create,
> gives no bounds safety, and silently corrupts when the enum is reordered — it
> is 15.2's bug wearing a different hat. `EnumMap` is array-backed internally, so
> it is as fast, and it is type-safe and prints its keys by name.

```java
// bad — unchecked cast, manual sizing, and reordering shuffles the buckets
Set<Plant>[] byLifeCycle = (Set<Plant>[]) new Set[LifeCycle.values().length];
for (int i = 0; i < byLifeCycle.length; i++) {
  byLifeCycle[i] = new HashSet<>();
}
for (Plant plant : garden) {
  byLifeCycle[plant.lifeCycle().ordinal()].add(plant);
}

// good
Map<LifeCycle, List<Plant>> byLifeCycle =
    garden.stream()
        .collect(
            Collectors.groupingBy(
                Plant::lifeCycle, () -> new EnumMap<>(LifeCycle.class), Collectors.toList()));
```

## 15.8 Emulate an extensible enum by having the enum implement an interface.

> Why? *Effective Java*, 3rd ed., Item 38: "Emulate extensible enums with
> interfaces." Enum types cannot be extended, and that is usually correct — but
> operation codes are the standard exception, where a client needs operations the
> library never knew about. Publishing an interface that the library's enum
> implements lets callers write their own enum, and lets every API accept
> `Collection<? extends Operation>` instead of one concrete enum type.

```java
// bad — clients cannot add an operation; they end up with a parallel
// if/else chain keyed off the enum
public enum Operation {
  PLUS,
  MINUS
}

// good — the interface is the type; the enums are two implementations
public interface Operation {
  double apply(double x, double y);
}

public enum BasicOperation implements Operation {
  PLUS {
    @Override
    public double apply(double x, double y) {
      return x + y;
    }
  }
}

public enum ExtendedOperation implements Operation {
  REMAINDER {
    @Override
    public double apply(double x, double y) {
      return x % y;
    }
  }
}

// Both enums are usable through one API.
public static void runAll(Collection<? extends Operation> operations, double x, double y) {
  for (Operation operation : operations) {
    System.out.printf("%f %f -> %f%n", x, y, operation.apply(x, y));
  }
}
```

## 15.9 Switch over an enum with an exhaustive `switch` expression that lists every constant, and do not add a `default` label.

> Why? Google Java Style
> [§4.8.4.3](https://google.github.io/styleguide/javaguide.html#s4.8.4.3-switch-default)
> requires "every switch to be exhaustive, even those where the language itself
> does not require it," and
> [§4.8.4.4](https://google.github.io/styleguide/javaguide.html#s4.8.4.4-switch-expressions)
> requires switch expressions to be new-style (arrow) switches. Google accepts
> either route to exhaustiveness — it explicitly allows "adding a `default`
> label, even if it contains no code" — but for an enum selector the two routes
> are not equally safe, and that is this rule's own recommendation rather than
> Google's. Listing every constant makes the compiler reject the switch when a
> constant is added; a `default` label makes the switch exhaustive *by
> construction* and silently absorbs every future constant into the fallback
> branch. Because a switch expression must be exhaustive
> ([JLS 21 §15.28.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.28.1)),
> listing every constant and omitting `default` turns "someone added a constant"
> from a production incident into a build failure. A *statement* switch over an
> enum with only constant labels is not required by the language to be
> exhaustive, which is exactly why the expression form is the default here.
> **Violation — the switch-expression form is enforced by `javac` itself, which
> rejects a non-exhaustive switch expression. Error Prone
> `MissingCasesInEnumSwitch` covers only the remaining gap, an enum *statement*
> switch that neither lists every constant nor has a `default`; it does not flag
> the `default` label this rule asks you to drop.**

```java
public enum Severity {
  INFO,
  WARNING,
  ERROR,
  FATAL
}

// bad — default swallows any constant added later; a new CRITICAL silently
// gets priority 2
static int priorityOf(Severity severity) {
  switch (severity) {
    case INFO:
      return 0;
    case WARNING:
      return 1;
    default:
      return 2;
  }
}

// good — adding a constant to Severity fails the build here
static int priorityOf(Severity severity) {
  return switch (severity) {
    case INFO -> 0;
    case WARNING -> 1;
    case ERROR -> 2;
    case FATAL -> 3;
  };
}
```

## 15.10 Build a lookup table once in a static field rather than calling `values()` on every invocation.

> Why? The compiler-generated `values()` method returns a *fresh clone* of the
> backing array on every call, so scanning `values()` in a request path
> allocates a garbage array per lookup and is `O(n)` besides. A static field
> initialized from `values()` pays both costs once. The trap: enum static
> initializers run *after* all constants are constructed, so a constant's
> constructor must never read such a field — populate it from `values()` at
> class-initialization time instead of registering from the constructor.

```java
// bad — clones the constant array and scans it linearly on every call
public static Optional<Currency> fromNumericCode(String code) {
  return Arrays.stream(values()).filter(c -> c.numericCode.equals(code)).findFirst();
}

// good — one array clone and one map build, at class-initialization time
public enum Currency {
  USD("840"),
  EUR("978");

  private static final Map<String, Currency> BY_NUMERIC_CODE =
      Arrays.stream(values())
          .collect(Collectors.toUnmodifiableMap(c -> c.numericCode, Function.identity()));

  private final String numericCode;

  Currency(String numericCode) {
    this.numericCode = numericCode;
  }

  public static Optional<Currency> fromNumericCode(String code) {
    return Optional.ofNullable(BY_NUMERIC_CODE.get(code));
  }
}
```

## 15.11 Put each constant on its own line once the enum has a body or per-constant documentation.

> Why? Google Java Style
> [§4.8.1](https://google.github.io/styleguide/javaguide.html#s4.8.1-enum-classes)
> notes that "after the comma that follows an enum constant, a line break is
> optional," and permits an enum with no methods and no per-constant
> documentation to be laid out like an array initializer. This is one of the few
> layout decisions `google-java-format` leaves to the author — it preserves your
> choice — so it is worth stating: the array-initializer form is fine for a bare
> list of names, but once a constant takes arguments, carries a body, or needs
> Javadoc, one-per-line is the only readable option, and it keeps the diff for
> "added a constant" to a single line.

```java
// bad — arguments and bodies crammed onto shared lines
public enum Status { ACTIVE(1), SUSPENDED(2), CLOSED(3); private final int code;
  Status(int code) { this.code = code; } }

// good — a bare name list may stay inline
private enum Suit { CLUBS, HEARTS, SPADES, DIAMONDS }

// good — constants with arguments get a line each
public enum Status {
  ACTIVE(1),
  SUSPENDED(2),
  CLOSED(3);

  private final int code;

  Status(int code) {
    this.code = code;
  }
}
```

## 15.12 Use an annotation, not a naming convention, to mark a declaration for a tool.

> Why? *Effective Java*, 3rd ed., Item 39: "Prefer annotations to naming
> patterns." A naming convention has no compiler behind it: a typo (`tsetSum`
> for `testSum`) produces silently skipped work rather than an error, the
> convention cannot be restricted to the right kind of declaration, and it has
> nowhere to put parameters. An annotation type is checked at compile time via
> `@Target`, is discoverable by IDEs, and can carry structured data. This is why
> JUnit moved from `testXxx` methods to `@Test`.

```java
// bad — a typo just means the method never runs
public class OrderTests {
  public void tsetTotalIncludesTax() { /* never discovered */ }
}

// good
public class OrderTests {
  @Test
  void totalIncludesTax() { /* ... */ }
}
```

## 15.13 Give every annotation type you define an explicit `@Retention` and `@Target`.

> Why? *Effective Java*, 3rd ed., Item 39. Both meta-annotations have defaults
> that are almost never what you want. Omitting
> [`@Retention`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/annotation/Retention.html)
> gives you `RetentionPolicy.CLASS`: the annotation is written into the class
> file but is invisible to reflection, so a framework scanning for it at run time
> finds nothing and the failure is a silent no-op. Omitting
> [`@Target`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/annotation/Target.html)
> leaves the annotation applicable in every declaration context and no type
> context: as the Java 21 Javadoc puts it, it "may be written as a modifier for
> any declaration." Nothing then stops a method-only annotation from landing on
> a field, and it can never be used as a type-use annotation. Add `@Documented`
> when the annotation is part of the contract a reader needs to see in the
> Javadoc.

```java
// bad — retained only in the class file, and legal almost anywhere
public @interface RetryOnFailure {
  int maxAttempts();
}

// good
@Documented
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface RetryOnFailure {
  int maxAttempts() default 3;

  Class<? extends Exception>[] retryOn() default {IOException.class};
}
```

## 15.14 Put `@Override` on every method where it is legal.

> Why? Google Java Style
> [§6.1](https://google.github.io/styleguide/javaguide.html#s6.1-override-annotation) is
> unconditional: "A method is marked with the `@Override` annotation whenever it
> is legal," with the single exception that it "may be omitted when the parent
> method is `@Deprecated`." *Effective Java*, 3rd ed., Item 40 gives the reason:
> without it, a method that *intends* to override but gets the signature subtly
> wrong — the classic being `equals(MyType)` instead of `equals(Object)` —
> compiles as a new overload and is never called. `@Override` makes that a
> compile error. It applies to interface implementations too, not just class
> overrides. Full treatment in [Chapter 7](07-programming-practices.md).
> **Violation — enforced by Error Prone `MissingOverride`, which flags any
> method that overrides a supertype method without the annotation. Checkstyle
> also ships a `MissingOverride`, but it fires only when the `{@inheritDoc}`
> Javadoc tag is present, so it catches a small subset of this rule.**

```java
// bad — this overloads Object.equals rather than overriding it, so HashSet
// never calls it and duplicates appear
public final class Bigram {
  private final char first;
  private final char second;

  public boolean equals(Bigram other) {
    return other.first == first && other.second == second;
  }
}

// good — @Override makes the mistake a compile error
public final class Bigram {
  private final char first;
  private final char second;

  @Override
  public boolean equals(Object other) {
    return other instanceof Bigram bigram && bigram.first == first && bigram.second == second;
  }

  @Override
  public int hashCode() {
    return Objects.hash(first, second);
  }
}
```

## 15.15 Use a marker interface, not a marker annotation, when the marker should define a type.

> Why? *Effective Java*, 3rd ed., Item 41: "Use marker interfaces to define
> types." A marker interface is a type, so the compiler catches a misuse at the
> call site; a marker annotation is not, so the same misuse becomes a run-time
> reflection check inside the framework. `Serializable` is the canonical example.
> Reach for a marker annotation instead when the target is not a type at all (a
> method, a field, a package), or when you expect to add elements later.

```java
// bad — nothing prevents passing an unmarked type; the failure is a run-time
// reflection check deep inside the serializer
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Persistable {}

public void save(Object entity) {
  if (!entity.getClass().isAnnotationPresent(Persistable.class)) {
    throw new IllegalArgumentException("not persistable: " + entity.getClass().getName());
  }
}

// good — the compiler rejects a non-Persistable argument
public interface Persistable {
  String storageKey();
}

public void save(Persistable entity) { /* ... */ }
```

## 15.16 Annotate an interface intended for lambdas with `@FunctionalInterface`.

> Why?
> [`@FunctionalInterface`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/FunctionalInterface.html)
> makes the compiler verify the interface has exactly one abstract method.
> Without it, adding a second abstract method is legal at the declaration site
> and instead breaks every lambda implementing the interface — possibly in
> another module, always far from the change that caused it. The annotation also
> documents intent: adding an abstract method here is a breaking change. See
> [Chapter 17](17-lambdas-and-method-references.md) for lambda usage.

```java
// bad — adding a second abstract method compiles here and breaks callers
public interface EventFilter {
  boolean accepts(Event event);

  boolean acceptsBatch(List<Event> events);
}

// good — the compiler rejects a second abstract method at the declaration
@FunctionalInterface
public interface EventFilter {
  boolean accepts(Event event);

  default EventFilter and(EventFilter other) {
    return event -> accepts(event) && other.accepts(event);
  }
}
```

## 15.17 Deprecate with `@Deprecated(since = ..., forRemoval = ...)` and always pair it with a Javadoc `@deprecated` tag naming the replacement.

> Why? The annotation and the tag do different jobs and you need both. The
> [annotation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Deprecated.html)
> is what `javac` reads: `forRemoval = true` upgrades use-site warnings from
> "deprecation" to "removal," a much louder signal that callers *must* migrate
> rather than merely ought to, and `since` tells a reader how long the migration
> window has been open. The Javadoc `@deprecated` tag is what a *human* reads,
> and a deprecation without a stated replacement is just an insult — the caller
> now knows the method is wrong but not what to call instead. Google Java Style
> [§7.1.3](https://google.github.io/styleguide/javaguide.html#s7.1.3-javadoc-block-tags)
> requires that block tags "never appear with an empty description."
> **Violation — enforced by Checkstyle `MissingDeprecated`; use sites are flagged
> by `javac -Xlint:deprecation,removal`.**

```java
// bad — no version, no removal intent, no replacement
@Deprecated
public void setTimeout(int millis) { /* ... */ }

// good
/**
 * Sets the read timeout in milliseconds.
 *
 * @param millis the timeout, in milliseconds
 * @deprecated Use {@link #setTimeout(Duration)} instead. This overload cannot express
 *     sub-millisecond precision and silently truncates values below 1 ms to zero.
 */
@Deprecated(since = "4.2", forRemoval = true)
public void setTimeout(int millis) {
  setTimeout(Duration.ofMillis(millis));
}
```

## 15.18 Place annotations per Google Java Style §4.8.5 — one per line on types and methods, inline on fields, immediately before the type for type-use annotations.

> Why? Google Java Style
> [§4.8.5.2](https://google.github.io/styleguide/javaguide.html#s4.8.5.2-class-annotation-style)
> requires that annotations on a class, package, or module declaration "appear
> immediately after the documentation block, and each annotation is listed on a
> line of its own";
> [§4.8.5.3](https://google.github.io/styleguide/javaguide.html#s4.8.5.3-method-annotation-style)
> applies the same rule to methods and constructors, with an explicit exception
> allowing a *single parameterless* annotation to share the signature's first
> line;
> [§4.8.5.4](https://google.github.io/styleguide/javaguide.html#s4.8.5.4-field-annotation-style)
> permits multiple field annotations on one line; and
> [§4.8.5.1](https://google.github.io/styleguide/javaguide.html#s4.8.5.1-type-use-annotation-style)
> requires a type-use annotation — one meta-annotated
> `@Target(ElementType.TYPE_USE)` — to "appear immediately before the annotated
> type." That last rule is the one that bites: a `TYPE_USE` annotation such as
> JSpecify's `@Nullable` written before the modifiers reads as a declaration
> annotation and qualifies the wrong thing inside a nested generic type. See
> [Chapter 25](25-nullability.md) for nullability itself. **Violation — enforced
> by Checkstyle `AnnotationLocation`.**

```java
// bad — type annotations sharing a line; @Nullable placed before the modifiers
@FunctionalInterface @Deprecated(since = "3.1") public interface Callback {
  void onEvent(String payload);
}

public final class Session {
  @Nullable private final String tenantId;

  @Override public String toString() { return "Session"; }
}

// good
@FunctionalInterface
@Deprecated(since = "3.1")
public interface Callback {
  void onEvent(String payload);
}

public final class Session {
  // Type-use annotation sits immediately before the type it qualifies.
  private final @Nullable String tenantId;

  // Multiple field annotations may share a line. @JsonProperty is a plain
  // declaration annotation; @NotNull is meta-annotated TYPE_USE, so it still
  // has to sit immediately before the type.
  @JsonProperty("expires_at") private final @NotNull Instant expiresAt;

  @Override
  public String toString() {
    return "Session[tenantId=" + tenantId + "]";
  }
}
```
