<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 11. Classes & Interfaces

This chapter covers the design of reference types: how much of a class to
expose, whether it should be mutable, whether it should be extensible, and
whether it should be a class at all. It draws from *Effective Java, 3rd ed.*,
Items 4, 15–25, and 50, and from the Google Java Style Guide sections that
constrain class structure —
[§3.4.1 Exactly one top-level class declaration](https://google.github.io/styleguide/javaguide.html#s3.4.1-one-top-level-class),
[§3.4.2 Ordering of class contents](https://google.github.io/styleguide/javaguide.html#s3.4.2-ordering-class-contents),
[§4.8.7 Modifiers](https://google.github.io/styleguide/javaguide.html#s4.8.7-modifiers),
and [§6.1 `@Override`](https://google.github.io/styleguide/javaguide.html#s6.1-override-annotation).

It deliberately defers its neighbours. Static factories and builders are
[Chapter 8](08-object-creation.md); `AutoCloseable` and cleanup are
[Chapter 9](09-object-lifecycle-and-resources.md); the `equals`/`hashCode`
contracts a value class must satisfy are
[Chapter 10](10-equals-hashcode-tostring.md). Record classes — the right
answer to several problems below — are [Chapter 12](12-records.md). Closing a
hierarchy with `sealed` is [Chapter 13](13-sealed-types.md) and dispatching
over one is [Chapter 14](14-pattern-matching.md). Generic variance is
[Chapter 16](16-generics.md), and Javadoc obligations for exported members
are [Chapter 4](04-javadoc.md).

**Tool alignment:** Checkstyle's `VisibilityModifier`, `FinalClass`,
`DesignForExtension`, `HideUtilityClassConstructor`, `InterfaceIsType`, and
`OneTopLevelClass` checks, plus Error Prone's `ClassCanBeStatic` and
`MutablePublicArray` bug patterns, mechanically enforce a good share of this
chapter. Enforced rules are marked **Violation**; design-judgment rules are
marked **Suggestion**.

## 11.1 Make every class and member as inaccessible as its callers allow.

> Why? *Effective Java*, Item 15: information hiding decouples the components
> of a system so they can be developed, tested, and replaced in isolation.
> Accessibility is a one-way ratchet — widening `private` to `public` is
> always safe, narrowing `public` to `private` breaks every caller. A
> `protected` member is part of the exported API for the life of the class,
> so it carries the same documentation and compatibility burden as a public
> one. **Suggestion.**

```java
// bad — the collaborator and the helper are reachable from the whole classpath
public class OrderProcessor {
  public OrderValidator validator;

  public boolean isEligibleForRush(Order order) {
    return order.weightGrams() < 500;
  }
}

// good — only the entry point is public; the rest is an implementation detail
public class OrderProcessor {
  private final OrderValidator validator;

  public Receipt process(Order order) {
    validator.validate(order);
    return Receipt.forOrder(order, isEligibleForRush(order));
  }

  private static boolean isEligibleForRush(Order order) {
    return order.weightGrams() < 500;
  }
}
```

## 11.2 In a public class, expose state through accessor methods, never through public mutable fields.

> Why? *Effective Java*, Item 16: a public field fixes the field
> representation as part of the API forever. You cannot later compute the
> value, validate an assignment, enforce an invariant, add a lock, or lazily
> initialize it without breaking source and binary compatibility. Accessors
> keep every one of those options open at zero runtime cost — the JIT inlines
> them. **Violation — enforced by `checkstyle/VisibilityModifier`.**

```java
// bad — the representation is now the API; no invariant can ever be added
public class Point {
  public double x;
  public double y;
}

// good — the representation is free to change behind the accessors
public class Point {
  private final double x;
  private final double y;

  public Point(double x, double y) {
    this.x = x;
    this.y = y;
  }

  public double x() {
    return x;
  }
  // y() likewise
}
```

When the components genuinely *are* the API, declare a `record` rather than
hand-writing the accessors — see [§12.1](12-records.md).

## 11.3 Never publish a mutable object through a `public static final` field.

> Why? `final` freezes the reference, not the object. A `public static final`
> array or `ArrayList` is a globally writable variable dressed up as a
> constant, and any caller can corrupt it for the whole JVM. It also violates
> Google Java Style
> [§5.2.4](https://google.github.io/styleguide/javaguide.html#s5.2.4-constant-names),
> which reserves `UPPER_SNAKE_CASE` for fields "whose contents are deeply
> immutable." **Violation for the array case — enforced by
> `errorprone/MutablePublicArray`, which flags non-empty `public static final`
> arrays. No checker catches the general case (a `public static final` mutable
> list, map, or date), so treat the broader rule as a Suggestion.**

```java
// bad — SUPPORTED_CURRENCIES[0] = "gone" compiles, and breaks every caller
public static final String[] SUPPORTED_CURRENCIES = {"EUR", "GBP", "USD"};

// good — an immutable list is a real constant
public static final List<String> SUPPORTED_CURRENCIES = List.of("EUR", "GBP", "USD");
```

## 11.4 Make a class immutable unless you have a concrete reason not to.

> Why? *Effective Java*, Item 17: "Classes should be immutable unless there is
> a very good reason to make them mutable." Immutable objects are inherently
> thread-safe, need no defensive copying when shared, can be cached and
> interned freely, and are safe as map keys and set elements. The five rules
> are: (1) provide no mutators, (2) make the class non-extensible, (3) make
> every field `final`, (4) make every field `private`, and (5) ensure
> exclusive access to any mutable component. **Suggestion.**

```java
// bad — every holder of a Money instance can be surprised by a change
public class Money {
  private long amountMinor;
  private Currency currency;

  public void setAmountMinor(long amountMinor) {
    this.amountMinor = amountMinor;
  }
}

// good — mutators become functional "with" methods returning new instances,
// and the class is final so the invariants cannot be subverted
public final class Money {
  private final long amountMinor;
  private final Currency currency;

  public Money plus(Money addend) {
    if (!currency.equals(addend.currency)) {
      throw new IllegalArgumentException("currency mismatch");
    }
    return new Money(amountMinor + addend.amountMinor, currency);
  }
}
```

## 11.5 Copy every mutable component on the way in, and on the way out.

> Why? *Effective Java*, Item 50: without a copy the caller retains a live
> handle to your internal state and can violate your invariants *after*
> construction — including after the constructor has already validated them.
> Copy **before** validating, so the check and the stored value refer to the
> same object and cannot be swapped by another thread. `List.copyOf` both
> copies and returns an unmodifiable list, so the accessor needs no second
> copy; a raw array needs one on both sides. **Suggestion.**

```java
// bad — the caller keeps a writable handle to the internal list, and the
// emptiness check can be defeated by clearing it afterwards
public Itinerary(List<Leg> legs) {
  this.legs = legs;
  if (legs.isEmpty()) {
    throw new IllegalArgumentException("itinerary needs at least one leg");
  }
}

// good — copy first, then validate the copy; the unmodifiable result is safe
// to hand back from legs() directly, with no second copy
public Itinerary(List<Leg> legs) {
  this.legs = List.copyOf(legs);
  if (this.legs.isEmpty()) {
    throw new IllegalArgumentException("itinerary needs at least one leg");
  }
}
```

## 11.6 Favor composition over inheritance when reusing a class you do not own.

> Why? *Effective Java*, Item 18: inheritance across package boundaries
> violates encapsulation, because a subclass depends on the *self-use
> patterns* of its superclass — implementation details the superclass author
> is free to change in any release. `HashSet.addAll` happens to be implemented
> in terms of `add`, so an overriding subclass double-counts. The snippet
> below prints `6` for the subclass and `3` for the composed wrapper.
> **Suggestion.**

```java
// bad — super.addAll calls this.add, so every element is counted twice
public class InstrumentedHashSet<E> extends HashSet<E> {
  private int addCount = 0;

  @Override
  public boolean add(E e) {
    addCount++;
    return super.add(e);
  }

  @Override
  public boolean addAll(Collection<? extends E> c) {
    addCount += c.size();
    return super.addAll(c); // reaches this.add — double count
  }
}

// good — a forwarding class owns a delegate and forwards every Set method;
// the wrapper then overrides only what it instruments
public class ForwardingSet<E> implements Set<E> {
  private final Set<E> delegate;

  public ForwardingSet(Set<E> delegate) {
    this.delegate = Objects.requireNonNull(delegate, "delegate");
  }

  @Override
  public boolean addAll(Collection<? extends E> c) {
    return delegate.addAll(c);
  }
  // ... every other Set method forwards identically
}

public final class CountingSet<E> extends ForwardingSet<E> {
  private int addCount = 0;

  public CountingSet(Set<E> delegate) {
    super(delegate);
  }

  @Override
  public boolean addAll(Collection<? extends E> c) {
    addCount += c.size();
    return super.addAll(c); // reaches delegate.addAll — counted once
  }
}
```

## 11.7 Inherit only when a genuine "is-a" relationship holds and you own both types.

> Why? *Effective Java*, Item 18: the question is "is every B really an A?"
> The JDK carries two famous violations — `Stack` extends `Vector` and
> `Properties` extends `Hashtable` — and both leak superclass operations that
> break the subclass's invariants. Inheriting purely for code reuse
> permanently exports the superclass's entire API from your type.
> **Suggestion.**

```java
// bad — a stack is not a list; add(int, E) and remove(int) let a caller reach
// into the middle and destroy LIFO ordering
public class Stack<E> extends ArrayList<E> {
  public void push(E e) {
    add(e);
  }
}

// good — composition exposes exactly the stack contract, nothing more
public final class Stack<E> {
  private final Deque<E> elements = new ArrayDeque<>();

  public void push(E e) {
    elements.addLast(e);
  }

  public E pop() {
    return elements.removeLast(); // throws NoSuchElementException when empty
  }
}
```

## 11.8 Design and document a class for inheritance, or prohibit inheritance outright.

> Why? *Effective Java*, Item 19: "design and document for inheritance or else
> prohibit it." Designing for inheritance means documenting every self-use
> pattern — which overridable method calls which, in what order — and
> committing to that documentation as API forever. Most classes are not worth
> the cost, so the default should be `final`, or a private constructor plus a
> static factory. **Violation — enforced by `checkstyle/FinalClass`,** which
> flags a class whose constructors are all private but which is not declared
> `final`. The full rule is enforced by `checkstyle/DesignForExtension`, which
> flags any non-final, non-abstract `public` or `protected` method with a body
> in a non-final class. That check is **not** in the shipped ruleset: it fails
> on almost every existing codebase and is worth enabling only on a new
> library where the inheritance contract is being designed deliberately
> (chapter 38).

```java
// bad — extensible by accident; nothing documents what a subclass may
// override or what the superclass calls internally
public class RetryPolicy {
  public Duration backoffFor(int attempt) {
    return baseDelay().multipliedBy(1L << attempt);
  }

  public Duration baseDelay() {
    return Duration.ofMillis(100);
  }
}

// good — either closed with `final`, or open on purpose with the self-use
// contract stated in @implSpec
public abstract class RetryPolicy {
  /**
   * Delay to wait before the given retry attempt.
   *
   * @implSpec Calls {@link #baseDelay()} exactly once and doubles the result
   *     for each attempt; overriding {@code baseDelay} rescales the curve.
   * @param attempt zero-based retry attempt
   * @return the delay before {@code attempt}
   */
  public Duration backoffFor(int attempt) {
    return baseDelay().multipliedBy(1L << attempt);
  }

  protected abstract Duration baseDelay();
}
```

## 11.9 Never invoke an overridable method from a constructor, `clone`, or `readObject`.

> Why? *Effective Java*, Item 19: the superclass constructor runs before the
> subclass constructor body, so an override invoked from it observes the
> subclass's fields in their default state. The snippet below prints
> `instant = null` even though `instant` is `final` and assigned in every
> subclass constructor. `clone` and `readObject` create objects the same way
> and carry the same hazard. **Suggestion.**

```java
// bad — Super's constructor calls the override before Sub is initialized
public class Super {
  public Super() {
    overrideMe();
  }

  public void overrideMe() {}
}

public final class Sub extends Super {
  private final Instant instant;

  public Sub() {
    this.instant = Instant.now();
  }

  @Override
  public void overrideMe() {
    System.out.println("instant = " + instant); // prints "instant = null"
  }
}

// good — the constructor calls only private, static, or final methods, so no
// subclass can intercept it mid-construction
public class Super {
  private final Clock clock;

  public Super(Clock clock) {
    this.clock = Objects.requireNonNull(clock, "clock");
  }

  protected final Clock clock() {
    return clock;
  }
}
```

## 11.10 Prefer an interface to an abstract class when defining a type.

> Why? *Effective Java*, Item 20: Java has single inheritance of state, so an
> abstract class spends the one `extends` slot a class has. An interface can
> be retrofitted onto an existing class, permits mixins, and supports
> non-hierarchical type frameworks. An abstract class is the better choice
> only when the type must carry mutable state or enforce a constructor
> invariant. **Suggestion.**

```java
// bad — any implementation must give up its single superclass slot
public abstract class EventPublisher {
  public abstract void publish(Event event);
}

// good — implementable by any class, and mixable with other types
public interface EventPublisher {
  void publish(Event event);
}

public final class KafkaGateway implements EventPublisher, HealthIndicator {
  @Override
  public void publish(Event event) {
    // ...
  }
}
```

## 11.11 Ship a skeletal implementation alongside any nontrivial interface.

> Why? *Effective Java*, Item 20: an interface plus an `AbstractInterface`
> skeleton gives implementors the choice between the convenience of
> inheritance and the flexibility of composition. The JDK uses the pattern
> throughout `java.util` — `AbstractCollection`, `AbstractList`,
> `AbstractMap`. A class with no free superclass slot composes instead, so the
> skeleton never forces the decision. **Suggestion.**

```java
// bad — interface only; every implementor re-derives the same null checks and
// the same trivial methods over its own map
public interface Cache<K, V> {
  Optional<V> lookup(K key);

  int size();
}

// good — the skeleton derives every operation from one primitive, so an
// implementation supplies only the storage
public abstract class AbstractCache<K, V> implements Cache<K, V> {
  @Override
  public Optional<V> lookup(K key) {
    return Optional.ofNullable(entries().get(Objects.requireNonNull(key, "key")));
  }

  @Override
  public int size() {
    return entries().size();
  }

  protected abstract Map<K, V> entries();
}

public final class HeapCache<K, V> extends AbstractCache<K, V> {
  private final Map<K, V> entries = new HashMap<>();

  @Override
  protected Map<K, V> entries() {
    return entries;
  }
}
```

## 11.12 Use interfaces only to define types — never as a holder for constants.

> Why? *Effective Java*, Item 22: the constant-interface pattern leaks an
> implementation detail into a class's exported API. Implementing an interface
> pulls its constants into the implementing class's namespace, so every
> subclass and every caller sees them, and removing the interface later is a
> binary-incompatible change. Constants belong on the class they describe, on
> an `enum`, or in a noninstantiable utility class.
> **Violation — enforced by `checkstyle/InterfaceIsType`.**

```java
// bad — "implements" now means "borrows a namespace", not "is a"
public interface PhysicalConstants {
  double AVOGADROS_NUMBER = 6.022_140_76e23;
  double BOLTZMANN_CONSTANT = 1.380_649e-23;
}

// good — a noninstantiable utility class; callers static-import what they need
public final class PhysicalConstants {
  public static final double AVOGADROS_NUMBER = 6.022_140_76e23;
  public static final double BOLTZMANN_CONSTANT = 1.380_649e-23;

  private PhysicalConstants() {
    throw new AssertionError("no instances");
  }
}
```

## 11.13 Design interfaces for posterity — a `default` method is permanent and unverifiable.

> Why? *Effective Java*, Item 21: a `default` method is injected into every
> existing implementation without its author's knowledge or consent, and there
> is no way to know whether it preserves that implementation's invariants.
> When `Collection.removeIf` was added in Java 8, Apache Commons Collections'
> `SynchronizedCollection` inherited it and silently lost its synchronization,
> because the default implementation iterates without acquiring the wrapper's
> lock. Commons Collections only closed that hole in 4.4, by declaring an
> overriding `removeIf` that takes the lock. Add a default to close a source
> incompatibility, not to grow an interface. **Suggestion.**

```java
// bad — a default that touches state the interface cannot see; any
// implementation with its own locking or ordering discipline inherits a
// method that ignores it
public interface Registry<K, V> {
  void put(K key, V value);

  default void putAll(Map<? extends K, ? extends V> entries) {
    entries.forEach(this::put); // not atomic; a locking impl loses its lock
  }
}

// good — leave the bulk operation abstract so each implementation states its
// own guarantee, and put the obligation in the interface's Javadoc
public interface Registry<K, V> {
  void put(K key, V value);

  /**
   * Inserts every entry.
   *
   * @implSpec Implementations that make {@link #put} atomic must make this
   *     method atomic too.
   * @param entries entries to insert
   */
  void putAll(Map<? extends K, ? extends V> entries);
}
```

## 11.14 Replace a tagged class with a class hierarchy.

> Why? *Effective Java*, Item 23: a tagged class — one field selecting which of
> several shapes the instance really is — is "verbose, error-prone, and
> inefficient." Every instance carries the fields of every variant, no
> constructor can enforce which fields go with which tag, and adding a variant
> means editing every `switch`. A hierarchy moves the discrimination into the
> type system; sealing it makes exhaustiveness a compile-time property — see
> [Chapter 13](13-sealed-types.md) and [Chapter 14](14-pattern-matching.md).
> **Suggestion.**

```java
// bad — radius is meaningless for a rectangle and vice versa, and nothing
// stops a caller constructing a RECTANGLE that carries a radius
public class Figure {
  private final Shape shape; // RECTANGLE or CIRCLE
  private double length;
  private double width;
  private double radius;

  public double area() {
    return switch (shape) {
      case RECTANGLE -> length * width;
      case CIRCLE -> Math.PI * radius * radius;
    };
  }
}

// good — each variant carries exactly its own state, and the compiler rejects
// any switch that forgets a variant
public sealed interface Figure permits Rectangle, Circle {
  double area();
}

public record Rectangle(double length, double width) implements Figure {
  @Override
  public double area() {
    return length * width;
  }
}

public record Circle(double radius) implements Figure {
  @Override
  public double area() {
    return Math.PI * radius * radius;
  }
}
```

## 11.15 Declare a member class `static` unless it genuinely needs its enclosing instance.

> Why? *Effective Java*, Item 24: a non-static member class holds a hidden
> reference to its enclosing instance. That reference costs time and space to
> construct, and — the real hazard — it keeps the enclosing object reachable
> for as long as the inner instance lives. An iterator, listener, or entry
> object that outlives its container pins the whole container in the heap,
> producing a leak no heap-dump reader expects.
> **Violation — enforced by `errorprone/ClassCanBeStatic`.**

```java
// bad — every BagIterator pins its Bag, including the backing array, for as
// long as any caller holds the iterator
public final class Bag<E> implements Iterable<E> {
  private final Object[] elements;

  private final class BagIterator implements Iterator<E> {
    private int index;

    @Override
    public boolean hasNext() {
      return index < elements.length; // implicit Bag.this.elements
    }
    // ...
  }
}

// good — a static nested class taking exactly what it needs
public final class Bag<E> implements Iterable<E> {
  private final Object[] elements;

  private static final class BagIterator<E> implements Iterator<E> {
    private final Object[] snapshot;
    private int index;

    BagIterator(Object[] snapshot) {
      this.snapshot = snapshot;
    }

    @Override
    public boolean hasNext() {
      return index < snapshot.length;
    }
    // ...
  }

  @Override
  public Iterator<E> iterator() {
    return new BagIterator<>(elements); // holds no reference to this Bag
  }
}
```

Member `record` and member `enum` classes are *implicitly* static — writing
the modifier on them is redundant, not required. See [§12.14](12-records.md).

## 11.16 Put exactly one top-level class in each source file.

> Why? Google Java Style
> [§3.4.1](https://google.github.io/styleguide/javaguide.html#s3.4.1-one-top-level-class)
> requires it, and *Effective Java*, Item 25 explains the failure mode: when
> two files each define the same auxiliary top-level class, which definition
> wins depends on the order the compiler is handed the source files, so the
> program's behavior changes with the build command. Nested classes are the
> supported way to group related types in one file.
> **Violation — enforced by `checkstyle/OneTopLevelClass`.**

```java
// bad — Utensil.java
class Utensil {
  static final String NAME = "pan";
}

class Dessert { // second top-level class; a rival definition may exist
  static final String NAME = "cake";
}

// good — Utensil.java holds one top-level class; Dessert moves to
// Dessert.java, or becomes a nested member if it is truly subordinate
public final class Utensil {
  static final String NAME = "pan";

  static final class Dessert {
    static final String NAME = "cake";
  }
}
```

## 11.17 Make a utility class noninstantiable with a private constructor that throws.

> Why? *Effective Java*, Item 4: a class with no explicit constructor gets a
> public no-arg one, so `new Math()` would compile had `Math` not suppressed
> it. A private constructor blocks both instantiation and subclassing — a
> subclass constructor has no accessible `super()` to call. Throwing from it
> defends against reflective and in-class instantiation, and states the intent
> better than a bare empty body.
> **Violation — enforced by `checkstyle/HideUtilityClassConstructor`.**

```java
// bad — "new StringUtils()" compiles, and StringUtils can be subclassed
public class StringUtils {
  public static boolean isBlank(String s) {
    return s == null || s.isBlank();
  }
}

// good
public final class StringUtils {
  private StringUtils() {
    throw new AssertionError("no instances");
  }

  public static boolean isBlank(String s) {
    return s == null || s.isBlank();
  }
}
```
