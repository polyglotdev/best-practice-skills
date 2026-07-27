<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 12. Records

A record class is, in the words of the
[`java.lang.Record` API docs](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Record.html),
"a shallowly immutable, transparent carrier for a fixed set of values, called
the record components." Records were finalized in Java 16 by
[JEP 395](https://openjdk.org/jeps/395), so in a Java 21 codebase they are the
default shape for every value carrier. This chapter covers when a record is
the right type, how to constrain one, and the places where the
compiler-generated members are not quite what you want.

Records were the answer to several problems raised in
[Chapter 11](11-classes-and-interfaces.md) — immutability (§11.4), accessors
over public fields (§11.2), tagged classes (§11.14). The `equals`, `hashCode`,
and `toString` contracts a record automatically satisfies are
[Chapter 10](10-equals-hashcode-tostring.md); this chapter does not restate
them. Using records as the permitted subtypes of a `sealed` interface is
[Chapter 13](13-sealed-types.md), and destructuring them with record patterns
is [Chapter 14](14-pattern-matching.md). Builders are
[Chapter 8](08-object-creation.md), and Javadoc form is
[Chapter 4](04-javadoc.md).

The rules below rely on the record semantics fixed by JEP 395 and JLS §8.10,
and on Google Java Style
[§7.3](https://google.github.io/styleguide/javaguide.html#s7.3-javadoc-where-required),
which requires Javadoc on "every visible class, member, or record component."

**Tool alignment:** Error Prone's `RecordAccessorInCompactConstructor` (ERROR),
`ArrayRecordComponent` (WARNING), and `RecordComponentOverride` (WARNING) bug
patterns, Checkstyle's `RedundantModifier`, and `javac -Xlint:serial` enforce
several of these rules. The rest are marked **Suggestion**.

## 12.1 Use a record when the type is a transparent, immutable carrier for a fixed set of values.

> Why? A record's contract is that its state *is* its components: the JLS
> requires that `new R(r.c1(), ..., r.cn()).equals(r)`. When that holds, the
> generated constructor, accessors, `equals`, `hashCode`, and `toString` are
> exactly the code you would have written, and hand-writing them only
> introduces the chance of getting one of them wrong.
> **Suggestion.**

```java
// bad — 40 lines of boilerplate that a reviewer must read to confirm it is
// the obvious thing, plus a hashCode that will drift when a field is added
public final class Coordinate {
  private final double latitude;
  private final double longitude;

  public Coordinate(double latitude, double longitude) {
    this.latitude = latitude;
    this.longitude = longitude;
  }

  public double latitude() {
    return latitude;
  }
  // longitude(), equals, hashCode, toString ...
}

// good
public record Coordinate(double latitude, double longitude) {}
```

## 12.2 Do not use a record when instances need identity, mutable state, or a superclass.

> Why? A record is implicitly `final` with `Record` as its direct superclass,
> so it can never extend anything, and `javac` rejects any instance field
> outside the component list with `field declaration must be static`. Value
> equality is also mandatory: two records with equal components are `equal`,
> which is wrong for anything the system tracks by identity rather than by
> content.
> **Suggestion.**

```java
// bad — a stateful, identity-bearing service is not a value
public record ConnectionPool(String url, int maxSize) {
  private int leased; // does not compile: "field declaration must be static"
}

// bad — two distinct in-flight jobs with the same arguments would be equal
public record Job(String queue, String payload) {}

// good — an ordinary class carries the mutable state and the identity
public final class ConnectionPool {
  private final String url;
  private int leased;
  // ...
}

// good — the record carries the immutable description, the class the identity
public record JobSpec(String queue, String payload) {}
```

## 12.3 Do not use a record when the components you would declare are not the API you want to publish.

> Why? A record is *transparent* by design — every component gets a public
> accessor, appears in `toString`, and participates in `equals`. That is a
> feature for a value type and a leak for anything else. If you would want to
> hide a component, derive it, rename its accessor, or keep it out of
> `toString`, the type is not a record.
> **Suggestion.**

```java
// bad — token() is public, and toString() prints the secret in every log line
public record ApiCredentials(String clientId, String token) {}

// good — an ordinary class keeps the secret out of the exported surface
public final class ApiCredentials {
  private final String clientId;
  private final String token;

  public String clientId() {
    return clientId;
  }

  @Override
  public String toString() {
    return "ApiCredentials[clientId=" + clientId + ", token=***]";
  }
}
```

## 12.4 Validate and normalize in a compact canonical constructor.

> Why? Every path that creates a record — `new`, a static factory,
> deserialization, a framework binder — runs the canonical constructor, so it
> is the only place an invariant can be enforced once and for all. The compact
> form declares no parameter list and assigns the fields implicitly at the end
> of its body, so it contains nothing but the checks and the normalization.
> **Suggestion.**

```java
// bad — the invariant lives at every call site instead of in the type
public record DateRange(LocalDate start, LocalDate end) {}

// good — no DateRange can exist in an invalid state
public record DateRange(LocalDate start, LocalDate end) {
  public DateRange {
    Objects.requireNonNull(start, "start");
    Objects.requireNonNull(end, "end");
    if (start.isAfter(end)) {
      throw new IllegalArgumentException("start %s is after end %s".formatted(start, end));
    }
  }
}

// good — normalization, so equals() compares canonical values
public record EmailAddress(String value) {
  public EmailAddress {
    value = value.strip().toLowerCase(Locale.ROOT);
  }
}
```

## 12.5 In a compact constructor, read and reassign the parameter — never the accessor, never `this.field`.

> Why? The compact constructor body runs *before* the compiler's implicit
> field assignments, so an accessor call inside it reads an uninitialized
> field and silently returns `null`, `0`, or `false`. Assigning to
> `this.field` does not work either — the field is blank `final` at that
> point, and `javac` reports `cannot assign a value to final variable`.
> Reassigning the parameter is the supported way to normalize a component.
> **Violation — enforced by
> `errorprone/RecordAccessorInCompactConstructor`.**

```java
// bad — name() reads the not-yet-assigned field, so isEmpty() throws NPE
public record User(String name) {
  public User {
    if (name().isEmpty()) {
      throw new IllegalArgumentException("name is blank");
    }
  }
}

// bad — does not compile: "cannot assign a value to final variable name"
public record User(String name) {
  public User {
    this.name = name.strip();
  }
}

// good — read and reassign the parameter; the field is assigned from it at
// the end of the body
public record User(String name) {
  public User {
    name = name.strip();
    if (name.isEmpty()) {
      throw new IllegalArgumentException("name is blank");
    }
  }
}
```

## 12.6 Prefer the compact canonical constructor; write the explicit form only when the compact one cannot express what you need.

> Why? An explicit canonical constructor must repeat the full parameter list
> and assign every field by hand, which reintroduces exactly the boilerplate
> the record removed — and the chance of assigning the wrong parameter to a
> field of the same type. Reach for it only when a parameter needs an
> annotation the component declaration cannot carry, or when the assignments
> genuinely differ from the parameters.
> **Suggestion.**

```java
// bad — three lines of ceremony for one normalization, and nothing stops
// "this.width = height"
public record Size(int width, int height) {
  public Size(int width, int height) {
    this.width = Math.max(0, width);
    this.height = height;
  }
}

// good — compact form; the fields are assigned implicitly
public record Size(int width, int height) {
  public Size {
    width = Math.max(0, width);
  }
}
```

## 12.7 Reach for a static factory, not a narrowed constructor — the canonical constructor can never be less accessible than the record.

> Why? The JLS requires the canonical constructor to "provide at least as much
> access as the record class," so declaring it `private` on a public record
> fails to compile with `attempting to assign stronger access privileges; was
> public`. The record's raw constructor is therefore always reachable. When
> you need a named or fallible entry point, add a static factory beside it
> rather than trying to hide the constructor — see
> [Chapter 8](08-object-creation.md).
> **Suggestion.**

```java
// bad — does not compile on a public record
public record Percentage(double fraction) {
  private Percentage(double fraction) { // stronger access privileges
    this.fraction = fraction;
  }
}

// good — the canonical constructor enforces the invariant; the factories name
// the units and handle the fallible parse
public record Percentage(double fraction) {
  public Percentage {
    if (fraction < 0 || fraction > 1) {
      throw new IllegalArgumentException("fraction out of range: " + fraction);
    }
  }

  public static Percentage ofPercent(double percent) {
    return new Percentage(percent / 100);
  }

  public static Optional<Percentage> parse(String text) {
    try {
      return Optional.of(ofPercent(Double.parseDouble(text)));
    } catch (IllegalArgumentException e) { // covers NumberFormatException too
      return Optional.empty();
    }
  }
}
```

## 12.8 Prefer an immutable collection component to an array component.

> Why? Arrays defeat every guarantee a record makes. The generated `equals`
> and `hashCode` use `Object` identity on the array, so two records with
> identical contents are never equal; `toString` prints `[B@723279cf`; and the
> array itself is mutable, so the record is not.
> **Violation — enforced by `errorprone/ArrayRecordComponent`.**

```java
// bad — Frame(1, new byte[] {1}).equals(Frame(1, new byte[] {1})) is false
public record Frame(int sequence, byte[] payload) {}

// good — an unmodifiable List has both value equality and a stable hashCode
public record Frame(int sequence, List<Integer> samples) {
  public Frame {
    samples = List.copyOf(samples);
  }
}

// good — for opaque binary data, use a type that already has value semantics.
// Error Prone's own suggestions are Guava's ImmutableList / ImmutableIntArray
// or protobuf's ByteString; on a plain JDK classpath, a hex or Base64 String
// is often the honest representation.
public record Frame(int sequence, String payloadBase64) {}
```

## 12.9 Copy a mutable collection component in the compact constructor.

> Why? A record is only *shallowly* immutable: `final` freezes the reference,
> not the object behind it. Without a copy, the caller keeps a live handle to
> the list inside your record and can mutate it after construction,
> invalidating both your validation and the `hashCode` any map already stored.
> `List.copyOf` copies and returns an unmodifiable list, so the generated
> accessor is then safe to hand back as-is.
> **Suggestion.**

```java
// bad — the caller can clear() the list after the record is in a HashMap
public record Order(String id, List<String> lineItems) {}

// good
public record Order(String id, List<String> lineItems) {
  public Order {
    Objects.requireNonNull(id, "id");
    lineItems = List.copyOf(lineItems); // throws NPE on a null element
  }
}
```

Note that `List.copyOf` rejects `null` elements, which is usually what you
want; if the component legitimately admits nulls, use
`Collections.unmodifiableList(new ArrayList<>(lineItems))` instead.

## 12.10 If a component must be an array, clone it in the compact constructor **and** override the accessor.

> Why? Copying on the way in is only half the job. The compiler-generated
> accessor returns the field directly, so it hands every caller a writable
> reference to your private array — the record leaks its own state on every
> read. A collection component does not have this problem because
> `List.copyOf` returns an unmodifiable view; an array has no such form, so
> the accessor must clone too. Prefer §12.8 and avoid the situation.
> **Suggestion.**

```java
// bad — copied in, but payload() hands the internal array straight out
public record Packet(int id, byte[] payload) {
  public Packet {
    payload = payload.clone();
  }
}

// good — copy on both sides
public record Packet(int id, byte[] payload) {
  public Packet {
    payload = payload.clone();
  }

  @Override
  public byte[] payload() {
    return payload.clone();
  }
}
```

## 12.11 Override an accessor only to preserve the record invariant, never to change what it returns — and never annotate the component with `@Override`.

> Why? The JLS states the invariant that `new R(r.c1(), ..., r.cn())` must
> equal `r`. An accessor that returns a different value than the one the
> canonical constructor stored breaks it, and every consumer that round-trips
> the record — serialization, `with`-style copying, record patterns — silently
> produces the wrong object. Defensive copying (§12.10) is the legitimate
> case, because a clone is still `equals` to what was stored. Separately,
> `@Override` on a component in the record header is inert: it must go on the
> accessor method in the body.
> **Violation for the `@Override`-on-a-component case — enforced by
> `errorprone/RecordComponentOverride` ("@Override annotations on record
> components don't do anything"). No checker catches an accessor that returns
> something other than what was stored, so treat that half as a Suggestion.**

```java
// bad — the record no longer round-trips: new Temp(t.celsius()) != t
public record Temp(double celsius) {
  @Override
  public double celsius() {
    return Math.round(celsius);
  }
}

// bad — @Override on the component does nothing
public record Temp(@Override double celsius) {}

// good — normalize once in the constructor, so the accessor stays honest
public record Temp(double celsius) {
  public Temp {
    celsius = Math.round(celsius);
  }
}
```

## 12.12 Let records implement interfaces; never reach for class inheritance.

> Why? A record cannot extend a class, and that restriction is a feature: it
> keeps the component list the whole state. Interfaces supply everything
> inheritance would have — shared contracts, `Comparable`, and membership in a
> `sealed` hierarchy, which is where records do their best work (see
> [Chapter 13](13-sealed-types.md)).
> **Suggestion.**

```java
// bad — does not compile; records have no extends clause
public record Circle(double radius) extends AbstractShape {}

// good — the interface supplies the contract, the record supplies the state
public sealed interface Shape permits Circle, Square {
  double area();
}

public record Circle(double radius) implements Shape {
  @Override
  public double area() {
    return Math.PI * radius * radius;
  }
}
```

## 12.13 Declare a record locally when it exists only to carry a tuple through one method.

> Why? Local records (final since Java 16) let an intermediate result have
> real names and real types without adding a type to the package's namespace
> or the file's imports. The alternatives — an `Object[]`, a
> `Map.Entry<A, B>`, or a top-level class nobody else uses — are all worse for
> the reader.
> **Suggestion.**

```java
// bad — getKey()/getValue() tell the reader nothing about what they hold
public List<String> longestFirst(List<String> names) {
  return names.stream()
      .map(n -> Map.entry(n, n.length()))
      .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
      .map(Map.Entry::getKey)
      .toList();
}

// good — the tuple is named, and the record never escapes the method
public List<String> longestFirst(List<String> names) {
  record Ranked(String name, int length) {}
  return names.stream()
      .map(n -> new Ranked(n, n.length()))
      .sorted(Comparator.comparingInt(Ranked::length).reversed())
      .map(Ranked::name)
      .toList();
}
```

## 12.14 Never write `static` on a nested record, or `final` on any record.

> Why? Both modifiers are implicit. JLS §8.1.3 lists member and local record
> classes among the nested classes that are "implicitly `static`, so are not
> inner classes," and §8.10 states that "a record class is implicitly `final`"
> and that "a nested record class is implicitly `static`" — in both cases
> adding that the modifier may be specified "redundantly." Writing either
> modifier adds noise and suggests to the reader that the alternative was
> available.
> **Violation — enforced by `checkstyle/RedundantModifier`.**

```java
// bad — both modifiers are already implied
public final record Money(long amountMinor, String currency) {}

public final class Invoice {
  static record LineItem(String sku, int quantity) {}
}

// good
public record Money(long amountMinor, String currency) {}

public final class Invoice {
  record LineItem(String sku, int quantity) {}
}
```

## 12.15 Rely on the canonical constructor to police deserialization — and know that `readObject` will not run.

> Why? The
> [Java Object Serialization Specification, §1.13](https://docs.oracle.com/en/java/javase/21/docs/specs/serialization/serial-arch.html)
> states that a record is reconstructed "by invoking the record's *canonical*
> constructor with the component values as arguments," so the validation in
> §12.4 runs on every deserialization — unlike an ordinary class, where a
> crafted stream bypasses every constructor. The flip side: "any class-specific
> `writeObject`, `readObject`, `readObjectNoData`, `writeExternal`, and
> `readExternal` methods defined by record classes are ignored." Only
> `writeReplace` and `readResolve` are honored. **Violation — enforced by
> `javac -Xlint:serial`, which reports "serialization-related method
> readObject is not effective in a record class."**

```java
// bad — this method compiles, looks like a guard, and never runs; a stream
// carrying number = -1 deserializes to an invalid Port unchallenged
public record Port(int number) implements Serializable {
  private void readObject(ObjectInputStream in) throws IOException {
    if (number < 1 || number > 65535) {
      throw new InvalidObjectException("port out of range");
    }
  }
}

// good — the compact constructor is the single enforcement point, and
// deserialization goes through it
public record Port(int number) implements Serializable {
  public Port {
    if (number < 1 || number > 65535) {
      throw new IllegalArgumentException("port out of range: " + number);
    }
  }
}
```

## 12.16 Bind JSON straight onto records — Jackson uses the canonical constructor.

> Why? [Jackson 2.12](https://github.com/FasterXML/jackson/wiki/Jackson-Release-2.12)
> added explicit `java.lang.Record` support: it discovers the components from
> the class file and binds through the canonical constructor, so no
> `@JsonCreator`, no `@JsonProperty` per parameter, and no `-parameters`
> compiler flag are needed — the component names come from the class file's
> `Record` attribute via `Class.getRecordComponents()`, not from debug
> metadata. Adding those annotations by reflex is noise. 2.12 also changed
> single-component records to default to properties-style binding; per the same
> release notes, `@JsonCreator(mode = JsonCreator.Mode.DELEGATING)` is what
> restores the older delegating behavior, so reach for it only when you
> genuinely want a bare scalar on the wire. Otherwise annotate only when the
> wire name differs from the component name.
> **Suggestion.**

```java
// bad — every annotation here is redundant on Jackson 2.12+
public record CreateUserRequest(
    @JsonProperty("email") String email, @JsonProperty("displayName") String displayName) {}

// good
public record CreateUserRequest(String email, String displayName) {}

// good — annotate only the component whose wire name differs
public record CreateUserRequest(String email, @JsonProperty("display_name") String displayName) {}
```

## 12.17 Do not model a JPA `@Entity` as a record — use records for projections and DTOs.

> Why? The Jakarta Persistence specification requires that an entity class
> "must have a no-arg constructor," that it "must not be final," and that "no
> methods or persistent instance variables of the entity class may be final."
> A record violates all three, and a persistence provider also needs to mutate
> managed state for dirty checking and lazy loading. Records are, however, the
> Spring Data recommendation for class-based projections: "Java Records are
> ideal to define DTO types since they adhere to value semantics"
> ([Spring Data JPA: Projections](https://docs.spring.io/spring-data/jpa/reference/repositories/projections.html)).
> **Suggestion.**

```java
// bad — will not work as a JPA entity
@Entity
public record Customer(@Id UUID id, String name) {}

// good — a mutable entity, and a record for everything that leaves the
// persistence layer
@Entity
public class Customer {
  @Id private UUID id;
  private String name;
  // ...
}

public record CustomerSummary(UUID id, String name) {}

public interface CustomerRepository extends Repository<Customer, UUID> {
  List<CustomerSummary> findByNameStartingWith(String prefix);
}
```

## 12.18 When most components are optional, use a class with a builder, not a record with a wall of nulls.

> Why? A record has exactly one constructor shape, so every optional component
> becomes a `null` the caller must pass positionally. Past three or four such
> components, call sites become unreadable and a transposed pair of same-typed
> arguments compiles silently. That is precisely the problem the Builder
> pattern solves — *Effective Java*, Item 2, and
> [Chapter 8](08-object-creation.md). A record with two or three optional
> components is fine; one with eight is not.
> **Suggestion.**

```java
// bad — the call site is unreadable, and transposing userAgent and referer
// compiles without a murmur
public record ReportRequest(
    URI target, String format, String title, String userAgent, String referer, String locale) {}

var request = new ReportRequest(target, "pdf", null, null, null, null);

// good — a builder names each optional value at the call site
var request = ReportRequest.builder(target).format("pdf").locale("en-IE").build();
```

## 12.19 Document record components with `@param` on the record declaration, not on the accessors.

> Why? Google Java Style
> [§7.3](https://google.github.io/styleguide/javaguide.html#s7.3-javadoc-where-required)
> requires Javadoc for "every visible class, member, or record component."
> A component has no declaration site a doc comment can attach to, so `@param`
> on the record class is the only way to document one; the standard doclet
> renders those descriptions in the *Record Components* section of the
> generated class page. It does not copy them onto the generated accessors —
> those get the doclet's own "Returns the value of the *x* record component"
> text — so the only way to document an accessor directly is to write it out by
> hand, reintroducing the boilerplate the record removed. The summary must be a
> fragment, per
> [§7.2](https://google.github.io/styleguide/javaguide.html#s7.2-summary-fragment).
> **Suggestion.**

```java
// bad — no component documentation, and the class summary is a complete
// sentence rather than the noun phrase §7.2 requires
/** This class represents a postal address. */
public record Address(String street, String postalCode) {}

// good — fragment summary, one @param per component
/**
 * Postal address within a single country.
 *
 * @param street street line, never blank
 * @param postalCode country-specific postal code, already normalized to upper
 *     case with no internal whitespace
 */
public record Address(String street, String postalCode) {}
```
