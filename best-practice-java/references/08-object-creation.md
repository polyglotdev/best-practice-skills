<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 8. Object Creation

Every object in a Java program comes into existence through a constructor, but
almost none of them should be *reached* through one. This chapter is about the
API you put in front of construction: static factories, builders, records as
parameter carriers, noninstantiable utility holders, and the discipline of
validating and defensively copying whatever a caller hands you.

The rules here come almost entirely from **Effective Java, 3rd Edition
(Joshua Bloch), Items 1–8**, with Items 49, 50, and 63 supplying the
validation, defensive-copying, and string-building rules — the design-level
territory that the
[Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
deliberately leaves open. Where Google *does* legislate, it is cited: the
[§6.4 finalizer prohibition](https://google.github.io/styleguide/javaguide.html#s6.4-finalizers)
and the [§6.3 static-member](https://google.github.io/styleguide/javaguide.html#s6.3-static-members)
qualification rule both land in this chapter.

Three neighbouring topics are deliberately deferred. **Cleanup** — how an
object releases what it acquired, `try`-with-resources, `AutoCloseable`, and
the legitimate uses of `Cleaner` — is [Chapter 9](09-object-lifecycle-and-resources.md).
**Record semantics** — canonical versus compact constructors, component
accessors, and when a record is the right shape at all — is
[Chapter 12](12-records.md). **Spring's flavour of dependency injection**,
including constructor injection and `@ConfigurationProperties` binding, is
[Chapter 32](32-spring-beans-and-di.md); §8.7 states the language-level
principle that chapter builds on.

**Tool alignment:** several rules below are mechanically enforced. Error Prone's
`BoxedPrimitiveConstructor`, `Finalize`, `StaticAssignmentInConstructor`, and
`UnnecessaryCheckNotNull` fire at compile time; Checkstyle's `NoFinalizer`,
`HideUtilityClassConstructor`, `FinalClass`, and `IllegalInstantiation` fire in
the same build. Rules a named check actually enforces are marked **Violation**;
the rest are **Suggestion**, even where a related check covers an adjacent
symptom.

## 8.1 Prefer a static factory method to a public constructor when the factory can carry a name, control which instance you get, or return a subtype.

> Why? Effective Java, 3rd ed., Item 1: "Consider static factory methods instead
> of constructors." A constructor's name is fixed by the class, so two
> constructors that differ only in the *meaning* of their parameters are
> indistinguishable at the call site. A factory names the operation, may return
> a cached instance instead of allocating, and may return a private
> implementation subtype — none of which a constructor can do. The JDK is built
> this way: `List.of`, `Integer.valueOf`, `Instant.ofEpochMilli`,
> `EnumSet.noneOf`. **Suggestion.**

```java
// bad — two constructors with the same signature is a compile error, so the
// API is forced into one ambiguous shape
public final class Money {
  private final long minorUnits;

  public Money(long minorUnits) {
    this.minorUnits = minorUnits;
  }
  // Cannot also offer Money(long majorUnits) — same signature.
}

// good — each factory names what its argument means
public final class Money {
  private final long minorUnits;

  private Money(long minorUnits) {
    this.minorUnits = minorUnits;
  }

  public static Money ofMinorUnits(long minorUnits) {
    return new Money(minorUnits);
  }

  public static Money ofMajorUnits(long majorUnits) {
    return new Money(Math.multiplyExact(majorUnits, 100L));
  }
}
```

## 8.2 Name static factories with the conventional vocabulary: `of`, `valueOf`, `from`, `getInstance`, `newInstance`, `create`, `copyOf`, `parse`.

> Why? Effective Java, 3rd ed., Item 1 catalogues these names, and the JDK
> follows them without exception: `List.of`, `Integer.valueOf`, `Instant.from`,
> `Duration.parse`, `List.copyOf`, `Calendar.getInstance`. Each name is a
> promise. `of` and `valueOf` say "cheap, possibly cached, no I/O".
> `newInstance` and `create` say "you get a fresh object every call". `from`
> says "type conversion". `parse` says "may throw on malformed input". Inventing
> `makeAMoney` or `buildFrom` discards a signal every Java reader already has.
> **Suggestion.**

```java
// bad — reader cannot tell whether this allocates, caches, or validates
public static Currency currencyFor(String code) { ... }
public static Currency constructCurrency(String code) { ... }

// good — names carry their conventional guarantees
public static Currency of(String code) { ... }          // cheap, may be cached
public static Currency parse(String text) { ... }       // may throw on bad input
public static Currency from(Locale locale) { ... }      // type conversion
public static List<Currency> copyOf(Collection<Currency> src) { ... }
```

## 8.3 Never write a telescoping constructor chain.

> Why? Effective Java, 3rd ed., Item 2 names the telescoping constructor pattern
> as the failure mode builders exist to fix: "the telescoping constructor pattern
> works, but it is hard to write client code when there are many parameters, and
> harder still to read it." A call site like `new Pizza(12, true, false, false,
> true)` cannot be reviewed — a reviewer has to count positions against the
> declaration, and swapping two adjacent `boolean`s compiles silently.
> **Suggestion.**

```java
// bad — telescoping chain; the call site is unreadable and swapping two
// adjacent booleans compiles cleanly
public final class Pizza {
  public Pizza(int sizeInches) {
    this(sizeInches, false);
  }

  public Pizza(int sizeInches, boolean extraCheese) {
    this(sizeInches, extraCheese, false);
  }

  public Pizza(int sizeInches, boolean extraCheese, boolean thinCrust) {
    this(sizeInches, extraCheese, thinCrust, false);
  }

  public Pizza(int sizeInches, boolean extraCheese, boolean thinCrust, boolean glutenFree) {
    // ...
  }
}

Pizza pizza = new Pizza(12, true, false, true); // which flag is which?

// good — one canonical constructor, reached through a builder (see 8.4)
Pizza pizza = Pizza.builder(12).extraCheese().glutenFree().build();
```

## 8.4 Use a builder when construction has more than a handful of parameters and several of them are optional.

> Why? Effective Java, 3rd ed., Item 2: "The Builder pattern simulates named
> optional parameters as found in Python and Scala." Java has no named or default
> arguments, so a builder is the only construct that lets a caller set the three
> fields they care about out of eleven, and lets the class validate the whole
> combination in one place — `build()` — rather than field by field. Make the
> builder produce an immutable object and keep the target's constructor private.
> **Suggestion.**

```java
// bad — optional parameters expressed as nulls the caller must count out
HttpClientConfig config = new HttpClientConfig("https://api.example.com", null, null, 30, null, true);

// good
public final class HttpClientConfig {
  private final URI baseUri;
  private final Duration connectTimeout;
  private final int maxRetries;

  private HttpClientConfig(Builder builder) {
    this.baseUri = builder.baseUri;
    this.connectTimeout = builder.connectTimeout;
    this.maxRetries = builder.maxRetries;
  }

  public static Builder builder(URI baseUri) {
    return new Builder(baseUri);
  }

  /** Mutable builder for {@link HttpClientConfig}; not thread-safe. */
  public static final class Builder {
    private final URI baseUri;
    private Duration connectTimeout = Duration.ofSeconds(10);
    private int maxRetries = 3;

    private Builder(URI baseUri) {
      this.baseUri = Objects.requireNonNull(baseUri, "baseUri");
    }

    public Builder connectTimeout(Duration connectTimeout) {
      this.connectTimeout = Objects.requireNonNull(connectTimeout, "connectTimeout");
      return this;
    }

    public Builder maxRetries(int maxRetries) {
      this.maxRetries = maxRetries;
      return this;
    }

    public HttpClientConfig build() {
      if (maxRetries < 0) {
        throw new IllegalArgumentException("maxRetries must be >= 0, was " + maxRetries);
      }
      return new HttpClientConfig(this);
    }
  }
}
```

## 8.5 Prefer a record — or a plain parameter object — to a builder when every component is required.

> Why? A builder buys you optionality and staged validation. If nothing is
> optional, you have paid for a mutable intermediate object, a `build()` method
> that can be forgotten, and roughly forty lines of boilerplate, in exchange for
> nothing. A [record](12-records.md) gives you the same named-field readability
> at the call site with a compact constructor for validation, and the compiler
> makes it a compile error to omit a component. Reach for the builder only when
> the parameter list is genuinely optional or genuinely long.
> **Suggestion.**

```java
// bad — builder for three mandatory components; build() can silently omit one
ShipmentRequest request =
    ShipmentRequest.builder().orderId(orderId).destination(address).weightGrams(1_200).build();

// good — record; omitting a component does not compile
public record ShipmentRequest(OrderId orderId, Address destination, int weightGrams) {
  public ShipmentRequest {
    Objects.requireNonNull(orderId, "orderId");
    Objects.requireNonNull(destination, "destination");
    if (weightGrams <= 0) {
      throw new IllegalArgumentException("weightGrams must be positive, was " + weightGrams);
    }
  }
}

ShipmentRequest request = new ShipmentRequest(orderId, address, 1_200);
```

## 8.6 Enforce noninstantiability of a utility class with a `private` constructor that throws, and make the class `final`.

> Why? Effective Java, 3rd ed., Item 4: "Enforce noninstantiability with a
> private constructor." A class with only static members that has no declared
> constructor gets a public no-arg default, which reads to a caller as an
> invitation to instantiate it. Making the constructor private removes it from
> the API; making it throw stops the class's own members from calling it by
> accident. **Violation — enforced by `checkstyle/HideUtilityClassConstructor`
> and `checkstyle/FinalClass`.**

```java
// bad — javac supplies a public no-arg constructor, and the class is subclassable
public class StringUtils {
  public static String truncate(String value, int maxLength) { ... }
}

// good
public final class StringUtils {
  private StringUtils() {
    throw new AssertionError("no instances");
  }

  public static String truncate(String value, int maxLength) { ... }
}
```

## 8.7 Inject a class's dependencies through its constructor; never hardwire a resource the class does not own.

> Why? Effective Java, 3rd ed., Item 5: "Prefer dependency injection to hardwiring
> resources." A class that constructs its own collaborator has one behaviour
> forever — you cannot swap the implementation for a test double, for a different
> environment, or for a second tenant. Constructor injection also makes the
> dependency `final`, so the object is fully initialised the moment it exists.
> For the Spring-specific form of this rule, see
> [Chapter 32](32-spring-beans-and-di.md). **Suggestion.**

```java
// bad — the dictionary is welded in; SpellChecker can never be tested offline
public final class SpellChecker {
  private final Lexicon dictionary = new EnglishLexicon(Path.of("/usr/share/dict/words"));

  public boolean isValid(String word) {
    return dictionary.contains(word);
  }
}

// good
public final class SpellChecker {
  private final Lexicon dictionary;

  public SpellChecker(Lexicon dictionary) {
    this.dictionary = Objects.requireNonNull(dictionary, "dictionary");
  }

  public boolean isValid(String word) {
    return dictionary.contains(word);
  }
}
```

## 8.8 Do not reach for a singleton; if a type genuinely must have exactly one instance, use a single-element enum.

> Why? Effective Java, 3rd ed., Item 3: "a single-element enum type is often the
> best way to implement a singleton" — it is serialization-safe and
> reflection-proof for free. But Item 3 also warns that "making a class a
> singleton can make it difficult to test its clients", and the mutable-static
> variant is the worst of both: global state that no test can reset and no caller
> can substitute. Prefer §8.7's injection and let the container (or `main`) own
> the single instance. Note that
> [Google Java Style §6.3](https://google.github.io/styleguide/javaguide.html#s6.3-static-members)
> requires static members to be qualified by class name, not by an instance
> reference. **Suggestion.**

```java
// bad — mutable static state; two tests running in the same JVM interfere
public final class MetricsRegistry {
  private static final Map<String, Long> COUNTERS = new ConcurrentHashMap<>();

  public static void increment(String name) {
    COUNTERS.merge(name, 1L, Long::sum);
  }
}

// good — inject the registry, so a test can hand in its own
public final class MetricsRegistry {
  private final Map<String, Long> counters = new ConcurrentHashMap<>();

  public void increment(String name) {
    counters.merge(name, 1L, Long::sum);
  }
}

// good — when one instance is genuinely a domain invariant, use an enum
public enum ClockSource {
  SYSTEM;

  public Instant now() {
    return Instant.now();
  }
}
```

## 8.9 Hoist an expensive immutable object out of the method that uses it and into a `private static final` field.

> Why? Effective Java, 3rd ed., Item 6: "Avoid creating unnecessary objects."
> `Pattern.compile` builds a finite state machine every call; `String.matches`
> compiles and discards one *per invocation*. The same applies to
> `DateTimeFormatter` and to any object whose construction cost dwarfs its use.
> Hoist to a `static` field only when the type is documented immutable and
> thread-safe — `Pattern` and `DateTimeFormatter` both are. A type that is
> merely expensive is not automatically shareable: `java.text` formatters are
> documented as "generally not synchronized", and a Jackson `ObjectMapper` is
> safe to share only once configuration is complete. **Suggestion.**

```java
// bad — String.matches compiles a fresh Pattern on every call and throws it away
static boolean isRomanNumeral(String value) {
  return value.matches("^(?=.)M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})$");
}

// good — compiled once at class initialization
public final class RomanNumerals {
  private static final Pattern ROMAN =
      Pattern.compile("^(?=.)M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})$");

  private RomanNumerals() {
    throw new AssertionError("no instances");
  }

  public static boolean isRomanNumeral(String value) {
    return ROMAN.matcher(value).matches();
  }
}
```

## 8.10 Never let a boxed primitive be the accumulator in a loop.

> Why? Effective Java, 3rd ed., Item 6 closes with exactly this example: a `Long`
> accumulator over `int` values "constructs about 2^31 superfluous `Long`
> instances." Autoboxing is invisible at the call site — the only clue is the
> declared type — so this is one of the few performance bugs that is genuinely
> hard to see in review. Declare the accumulator as the primitive. **Suggestion.**

```java
// bad — every += unboxes, adds, and boxes a fresh Long
private static long sum() {
  Long sum = 0L;
  for (long i = 0; i <= Integer.MAX_VALUE; i++) {
    sum += i;
  }
  return sum;
}

// good
private static long sum() {
  long sum = 0L;
  for (long i = 0; i <= Integer.MAX_VALUE; i++) {
    sum += i;
  }
  return sum;
}
```

## 8.11 Never call a boxed-primitive constructor; use `valueOf`, a literal, or autoboxing.

> Why? `new Integer(1)`, `new Boolean(true)`, and every other boxed-primitive
> constructor carry `@Deprecated(since = "9", forRemoval = true)` in JDK 21 —
> the Javadoc renders this as "Deprecated, for removal: This API element is
> subject to removal in a future version." Beyond the deprecation, they defeat
> the JDK's instance cache: two `new Integer(1)` values are never `==`, whereas
> `Integer.valueOf(1)` returns the same cached object for small values. Code
> that mixes the two produces reference comparisons that pass in tests and fail
> in production.
> **Violation — enforced by `error-prone/BoxedPrimitiveConstructor`.**
> `checkstyle/IllegalInstantiation` also covers this, but only if the boxed
> types are listed in its `classes` property; its default configuration names no
> classes and therefore flags nothing.

```java
// bad — deprecated for removal, and allocates where the cache would have served
Integer count = new Integer(1);
Boolean enabled = new Boolean("true");

// good
Integer count = 1;                          // autoboxing routes through valueOf
Boolean enabled = Boolean.parseBoolean("true");
Integer explicit = Integer.valueOf(1);
```

## 8.12 Never build a string with `+=` inside a loop.

> Why? Effective Java, 3rd ed., Item 63: "Using the string concatenation operator
> repeatedly to concatenate n strings requires time quadratic in n." Each `+=`
> allocates a new `String` and copies every character accumulated so far. Use
> `StringBuilder` when you are assembling incrementally, or `String.join` /
> `Collectors.joining` when you are joining a known collection. **Suggestion.**

```java
// bad — O(n^2) copying; allocates one throwaway String per iteration
String statement(List<LineItem> items) {
  String result = "";
  for (LineItem item : items) {
    result += item.description() + "\n";
  }
  return result;
}

// good — single buffer, linear time
String statement(List<LineItem> items) {
  StringBuilder result = new StringBuilder(items.size() * 32);
  for (LineItem item : items) {
    result.append(item.description()).append('\n');
  }
  return result.toString();
}

// good — when you are simply joining, say so
String csv(List<String> names) {
  return String.join(",", names);
}
```

## 8.13 Validate every constructor and factory argument eagerly, and name the offending parameter in the message.

> Why? Effective Java, 3rd ed., Item 49: "Check parameters for validity." A
> `null` stored in a field surfaces as a `NullPointerException` in an unrelated
> method, minutes or hours later, with a stack trace that points nowhere near the
> caller who supplied it. `Objects.requireNonNull(x, "x")` fails at the boundary
> with the parameter name in the message. Use `IllegalArgumentException` for
> range and format violations, and put the rejected value in the message.
> **Suggestion** — no check can tell that a validation is *missing*. The nearby
> tooling runs the other way: `error-prone/UnnecessaryCheckNotNull` flags a null
> check on an expression that "can never be null", and NullAway flags a
> `@NonNull` field left uninitialized. Neither one will notice an unvalidated
> parameter.

```java
// bad — a null customerId surfaces hours later, in a method that never saw the
// caller who supplied it
public Subscription(CustomerId customerId, Period billingPeriod, int seats) {
  this.customerId = customerId;
  this.billingPeriod = billingPeriod;
  this.seats = seats;
}

// good — fails at the boundary, naming the parameter and the rejected value
public Subscription(CustomerId customerId, Period billingPeriod, int seats) {
  this.customerId = Objects.requireNonNull(customerId, "customerId");
  this.billingPeriod = Objects.requireNonNull(billingPeriod, "billingPeriod");
  if (seats < 1) {
    throw new IllegalArgumentException("seats must be >= 1, was " + seats);
  }
  this.seats = seats;
}
```

## 8.14 Defensively copy every mutable argument on the way in, and every mutable field on the way out — and validate the copy, not the original.

> Why? Effective Java, 3rd ed., Item 50: "Make defensive copies when needed."
> If you store the caller's `List` or `Date` directly, the caller keeps a live
> handle to your internals and can mutate your object after construction, past
> every invariant you checked. The copy must be made *before* validation, not
> after: otherwise a hostile or merely concurrent caller can change the value in
> the window between the check and the assignment — a time-of-check/time-of-use
> hole. `List.copyOf` and friends both copy and freeze in one call.
> **Suggestion.**

```java
// bad — caller retains a live reference to the list, and the check races the store
public final class Itinerary {
  private final List<Leg> legs;

  public Itinerary(List<Leg> legs) {
    if (legs.isEmpty()) {
      throw new IllegalArgumentException("legs must not be empty");
    }
    this.legs = legs;
  }

  public List<Leg> legs() {
    return legs;
  }
}

// good — copy first, validate the copy, hand out an unmodifiable view
public final class Itinerary {
  private final List<Leg> legs;

  public Itinerary(List<Leg> legs) {
    this.legs = List.copyOf(legs); // copyOf rejects null elements and freezes
    if (this.legs.isEmpty()) {
      throw new IllegalArgumentException("legs must not be empty");
    }
  }

  public List<Leg> legs() {
    return legs; // already unmodifiable
  }
}
```

## 8.15 Do not let `this` escape from a constructor.

> Why? Until a constructor returns, the object's `final` fields are not
> guaranteed visible to other threads, and any subclass constructor body has not
> run. Registering a listener, starting a thread, or assigning `this` to a static
> field from inside the constructor publishes a half-built object that another
> thread may observe with `null` fields. Move the publication into a static
> factory that constructs first and registers second. Escape via a listener
> registration is invisible to static analysis, so that half is a
> **Suggestion**; the static-field variant is a **Violation — enforced by
> `error-prone/StaticAssignmentInConstructor`**, whose rationale is the same:
> "Mutating static state from a constructor is highly error-prone."

```java
// bad — `this` escapes twice: into a static field, and into a listener registry
// that may call back before the constructor finishes
public final class PriceWatcher implements TickListener {
  private static PriceWatcher latest;

  private final Threshold threshold;

  public PriceWatcher(EventBus bus, Threshold threshold) {
    latest = this;      // static assignment from a constructor
    bus.register(this); // escapes before `threshold` is assigned
    this.threshold = threshold;
  }

  @Override
  public void onTick(Tick tick) {
    if (threshold.exceededBy(tick)) { ... }
  }
}

// good — construct fully, then publish
public final class PriceWatcher implements TickListener {
  private final Threshold threshold;

  private PriceWatcher(Threshold threshold) {
    this.threshold = Objects.requireNonNull(threshold, "threshold");
  }

  public static PriceWatcher attach(EventBus bus, Threshold threshold) {
    PriceWatcher watcher = new PriceWatcher(threshold);
    bus.register(watcher);
    return watcher;
  }

  @Override
  public void onTick(Tick tick) {
    if (threshold.exceededBy(tick)) { ... }
  }
}
```

## 8.16 Never override `Object.finalize`, and never treat a `Cleaner` as the primary cleanup path.

> Why?
> [Google Java Style §6.4](https://google.github.io/styleguide/javaguide.html#s6.4-finalizers)
> is two sentences long: "Do not override `Object.finalize`. Finalization
> support is scheduled for removal." Effective Java,
> 3rd ed., Item 8 explains the cost — finalizers and cleaners are
> "unpredictable, often dangerous, and generally unnecessary", the JVM offers no
> guarantee they ever run, and an exception thrown from a finalizer is swallowed
> silently. As of JDK 18 finalization is deprecated for removal and can be
> disabled outright with `--finalization=disabled`, so a finalizer-based release
> path is a latent production failure. Use `AutoCloseable` and
> `try`-with-resources instead — see [Chapter 9](09-object-lifecycle-and-resources.md)
> for the full treatment, including the narrow case where a `Cleaner` is a
> legitimate *safety net*.
> **Violation — enforced by `checkstyle/NoFinalizer` and `error-prone/Finalize`.**

```java
// bad — may never run; exceptions from it vanish; deprecated for removal
public class NativeBuffer {
  private long address;

  @Override
  protected void finalize() throws Throwable {
    free(address);
    super.finalize();
  }
}

// good — deterministic release the caller controls
public final class NativeBuffer implements AutoCloseable {
  private long address;

  @Override
  public void close() {
    if (address != 0L) {
      free(address);
      address = 0L;
    }
  }
}
```
