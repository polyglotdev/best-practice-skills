<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 10. `equals`, `hashCode`, `toString`, `Comparable`

Four methods decide whether your type works with the rest of Java. `equals` and
`hashCode` decide whether it can be a `HashMap` key or a `HashSet` element.
`compareTo` decides whether it can live in a `TreeSet` or come out of
`Collections.sort` in a defined order. `toString` decides whether a production
log line is diagnosable. All four are contracts, not conventions — a violation
does not produce a compile error or an exception, it produces a `Set` that
contains the same element twice.

This chapter is grounded in the JDK 21 API contracts for
[`Object.equals`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html#equals(java.lang.Object)),
[`Object.hashCode`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html#hashCode()),
and
[`Comparable.compareTo`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Comparable.html#compareTo(T)),
together with **Effective Java, 3rd Edition, Items 10–14**. Google's guide
contributes the
[§6.1 `@Override`](https://google.github.io/styleguide/javaguide.html#s6.1-override-annotation)
rule that every method here depends on.

One large shortcut is deferred to [Chapter 12](12-records.md): a `record`
generates `equals`, `hashCode`, and `toString` from its components,
contract-correct, and none of the rules in §10.2 through §10.16 need to be
hand-checked for one. If the type you are writing is a transparent aggregate of
its components, stop reading and write a record. Everything below is for the
cases where you cannot. Ordering-adjacent collection choices — `TreeMap` versus
`HashMap`, `EnumMap`, `SequencedCollection` — are
[Chapter 20](20-collections.md). Comparator-shaped lambdas are
[Chapter 17](17-lambdas-and-method-references.md).

**Tool alignment:** this is the best-instrumented area in the Java toolchain.
Error Prone's `EqualsHashCode`, `MissingOverride`, `ReferenceEquality`,
`NonOverridingEquals`, `SelfEquals`, `EqualsGetClass`, `EqualsUnsafeCast`,
`EqualsUsingHashCode`, `BoxedPrimitiveEquality`, `ArrayEquals`, `ArrayHashCode`,
`ArrayToString`, `ObjectToString`,
`ComparableType`, `ComparableAndComparator`, `SelfComparison`, and
`CompareToZero` all fire at compile time, as do Checkstyle's `EqualsHashCode`,
`CovariantEquals`, `EqualsAvoidNull`, and `StringLiteralEquality`. Rules a named
check actually enforces are marked **Violation**; the rest are **Suggestion**,
even where a related check covers an adjacent symptom.

## 10.1 Do not override `equals` at all unless instances have a value identity distinct from object identity.

> Why? Effective Java, 3rd ed., Item 10 opens by listing when *not* to: each
> instance is inherently unique (a `Thread`, a running task), there is no need
> for logical equality (a service class), a superclass already implements it
> correctly, or the class is package-private and nothing ever calls it. The
> inherited `Object.equals` is identity comparison, which is right far more often
> than people assume, and every hand-written override is a contract you now have
> to maintain and test. **Suggestion.**

```java
// bad — a stateless service is not a value; this override adds risk and no meaning
public final class PaymentGateway {
  @Override
  public boolean equals(Object o) {
    return o instanceof PaymentGateway;
  }

  @Override
  public int hashCode() {
    return 1;
  }
}

// good — identity semantics inherited from Object are exactly right
public final class PaymentGateway {
  private final HttpClient client;

  public PaymentGateway(HttpClient client) {
    this.client = Objects.requireNonNull(client, "client");
  }
}
```

## 10.2 When you do override `equals`, satisfy all five clauses of the contract: reflexive, symmetric, transitive, consistent, and `false` for `null`.

> Why? The JDK 21 `Object.equals` docs state the contract in full: it must be
> reflexive ("`x.equals(x)` should return `true`"), symmetric ("`x.equals(y)`
> should return `true` if and only if `y.equals(x)` returns `true`"), transitive,
> consistent across repeated invocations "provided no information used in
> `equals` comparisons on the objects is modified", and "`x.equals(null)` should
> return `false`". Collections assume every clause. Break one and `HashSet.add`
> will admit a duplicate, or `List.remove` will fail to find an element you can
> see in the debugger. **Suggestion.**

```java
// bad — asymmetric (String never equals a UserId) and NPEs instead of returning
// false for null
@Override
public boolean equals(Object o) {
  return value.equals(o.toString());
}

// good — the instanceof pattern handles null and the wrong type in one test
@Override
public boolean equals(Object o) {
  return o instanceof UserId other && value.equals(other.value);
}
```

## 10.3 Never make `equals` interoperate with a foreign type — it destroys symmetry.

> Why? Effective Java, 3rd ed., Item 10 uses `CaseInsensitiveString` for this:
> once your `equals` accepts a `String`, `cis.equals(s)` is `true` while
> `s.equals(cis)` is `false`, because `String.equals` has never heard of your
> class. The contract is violated, and the consequence is not theoretical —
> `list.contains(s)` gives different answers on different `List` implementations,
> because each one picks a different argument order. **Suggestion.**

```java
// bad — cis.equals(s) is true but s.equals(cis) is false
public final class CaseInsensitiveString {
  private final String value;

  @Override
  public boolean equals(Object o) {
    if (o instanceof CaseInsensitiveString other) {
      return value.equalsIgnoreCase(other.value);
    }
    if (o instanceof String s) { // the symmetry-breaking clause
      return value.equalsIgnoreCase(s);
    }
    return false;
  }
}

// good — only ever equal to another CaseInsensitiveString
public final class CaseInsensitiveString {
  private final String value;

  @Override
  public boolean equals(Object o) {
    return o instanceof CaseInsensitiveString other && value.equalsIgnoreCase(other.value);
  }

  @Override
  public int hashCode() {
    return value.toLowerCase(Locale.ROOT).hashCode();
  }
}
```

## 10.4 Do not add a value component in a subclass of an instantiable class; use composition instead.

> Why? Effective Java, 3rd ed., Item 10: "There is no way to extend an
> instantiable class and add a value component while preserving the `equals`
> contract." Comparing with `instanceof` in the superclass makes the relation
> asymmetric or intransitive; comparing with `getClass()` makes a `ColorPoint`
> unequal to an equal `Point`, which violates the Liskov substitution principle.
> The workaround Bloch gives is composition: hold the superclass value as a
> private field and expose a view. **Suggestion.**

```java
// bad — transitivity fails: p1.equals(p2) && p2.equals(p3), but !p1.equals(p3)
public class ColorPoint extends Point {
  private final Color color;

  @Override
  public boolean equals(Object o) {
    if (!(o instanceof Point)) {
      return false;
    }
    if (!(o instanceof ColorPoint other)) {
      return o.equals(this); // colour-blind comparison in one direction only
    }
    return super.equals(o) && color.equals(other.color);
  }
}

// good — composition; ColorPoint is not a Point, and exposes one on request
public record ColorPoint(Point point, Color color) {
  public ColorPoint {
    Objects.requireNonNull(point, "point");
    Objects.requireNonNull(color, "color");
  }

  /** Returns the point part of this colour point, discarding the colour. */
  public Point asPoint() {
    return point;
  }
}
```

## 10.5 Test the argument with a pattern-matching `instanceof`, not `getClass()`, and make the class `final` so the distinction cannot bite.

> Why? `getClass()` equality means a subclass instance is never equal to a
> superclass instance even when every field matches, which breaks substitutability
> and surprises anyone using a proxy, a Hibernate entity, or a Mockito spy.
> `instanceof` preserves substitutability but is only safe if no subclass adds a
> value component (§10.4) — and declaring the class `final` makes that
> guaranteed rather than hoped for. Java 21's pattern form also removes the
> separate cast, which is where `EqualsUnsafeCast` bugs come from.
> **Violation — enforced by `error-prone/EqualsGetClass` and
> `error-prone/EqualsUnsafeCast`.**

```java
// bad — getClass() rules out subclasses; the cast is separate and unchecked
@Override
public boolean equals(Object o) {
  if (o == null || getClass() != o.getClass()) {
    return false;
  }
  PhoneNumber other = (PhoneNumber) o;
  return areaCode == other.areaCode && lineNumber == other.lineNumber;
}

// good
@Override
public boolean equals(Object o) {
  return o instanceof PhoneNumber other
      && areaCode == other.areaCode
      && lineNumber == other.lineNumber;
}
```

## 10.6 Short-circuit on `this == o`, then compare the cheapest and most-discriminating fields first.

> Why? Effective Java, 3rd ed., Item 10's recipe. The identity check is a single
> instruction and is the common case in a hash bucket after a hash hit. Field
> order matters because `&&` short-circuits: comparing a 4-byte `int` before a
> long `String` means most unequal pairs are rejected without touching the
> string. Never compare a derived field when the fields it derives from are
> already compared — that is pure cost. **Suggestion.**

```java
// bad — the expensive String comparison runs first, and there is no identity
// fast path
@Override
public boolean equals(Object o) {
  return o instanceof Invoice other
      && description.equals(other.description)
      && total.equals(other.total)
      && id == other.id;
}

// good
@Override
public boolean equals(Object o) {
  if (this == o) {
    return true;
  }
  return o instanceof Invoice other
      && id == other.id
      && total.equals(other.total)
      && description.equals(other.description);
}
```

## 10.7 Give `equals` the parameter type `Object`, and always annotate it `@Override`.

> Why? `equals(MyType other)` is an *overload*, not an override. It compiles, it
> passes the unit test that calls it directly, and it is never invoked by
> `HashMap`, `List.contains`, or `Objects.equals`, all of which dispatch through
> `equals(Object)`. Google Java Style
> [§6.1](https://google.github.io/styleguide/javaguide.html#s6.1-override-annotation)
> requires `@Override` "whenever it is legal", which turns this exact mistake
> into a compile error.
> **Violation — enforced by `error-prone/NonOverridingEquals`,
> `checkstyle/CovariantEquals`, and `error-prone/MissingOverride`.**

```java
// bad — an overload; HashMap will never call it
public boolean equals(PhoneNumber other) {
  return areaCode == other.areaCode && lineNumber == other.lineNumber;
}

// good
@Override
public boolean equals(Object o) {
  return o instanceof PhoneNumber other
      && areaCode == other.areaCode
      && lineNumber == other.lineNumber;
}
```

## 10.8 Always override `hashCode` when you override `equals`.

> Why? The JDK 21 `Object.hashCode` contract: "If two objects are equal according
> to the `equals` method, then calling the `hashCode` method on each of the two
> objects must produce the same integer result." Effective Java, 3rd ed., Item 11
> puts the consequence plainly: a class that violates it "will not function
> properly in collections such as `HashMap` and `HashSet`". Two equal objects
> with different hashes land in different buckets, so `map.get(equalKey)` returns
> `null` for a key that is provably present.
> **Violation — enforced by `error-prone/EqualsHashCode` and
> `checkstyle/EqualsHashCode`.**

```java
// bad — inherits Object.hashCode, so two equal PhoneNumbers hash differently
// and map.get(equalKey) returns null
public final class PhoneNumber {
  @Override
  public boolean equals(Object o) {
    return o instanceof PhoneNumber other
        && areaCode == other.areaCode
        && lineNumber == other.lineNumber;
  }
}

// good — add the matching hashCode over the same two fields
@Override
public int hashCode() {
  return Objects.hash(areaCode, lineNumber);
}
```

## 10.9 Derive `hashCode` from exactly the fields `equals` uses — no more, no fewer.

> Why? A field used by `hashCode` but not `equals` breaks the contract directly:
> two equal objects can differ in that field and therefore hash differently. A
> field used by `equals` but not `hashCode` is legal but degenerate — it pushes
> distinguishable objects into the same bucket, turning `HashMap` lookups from
> constant time into linear scans. Effective Java, 3rd ed., Item 11 also warns
> against excluding a significant field "to improve performance". The inverse
> shortcut — implementing `equals` by comparing `hashCode` values — is worse
> still, because hashes collide: roughly 77,000 randomly distributed objects
> give a 50% chance of a collision, and every collision is a false `true`.
> **Suggestion** — no check can compare the field sets of your `equals` and your
> `hashCode`. Only the degenerate inverse is mechanical: implementing `equals`
> by comparing `hashCode` values is a **Violation — enforced by
> `error-prone/EqualsUsingHashCode`**, which calls it "fragile".

```java
// bad — `version` is in hashCode but not equals, so equal invoices hash differently
@Override
public boolean equals(Object o) {
  return o instanceof Invoice other && id == other.id;
}

@Override
public int hashCode() {
  return Objects.hash(id, version);
}

// good — same fields, both directions
@Override
public boolean equals(Object o) {
  return o instanceof Invoice other && id == other.id;
}

@Override
public int hashCode() {
  return Long.hashCode(id);
}
```

## 10.10 Use `Objects.hash` for readability; drop to the explicit `31 *` accumulation only on a measured hot path.

> Why? `Objects.hash(Object...)` allocates a varargs array on every call and
> boxes every primitive argument. Effective Java, 3rd ed., Item 11 says so
> directly: "it is slower because it entails array creation … and boxing and
> unboxing if any of the arguments are of primitive type. … not for use in
> performance-critical situations." For a class that is a hash key in a hot loop,
> the hand-written form costs nothing and allocates nothing; for everything else,
> the readability wins. **Suggestion.**

```java
// good — the default: readable, and the allocation does not matter here
@Override
public int hashCode() {
  return Objects.hash(areaCode, prefix, lineNumber);
}

// good — measured hot path: no varargs array, no boxing, optional caching for
// an immutable type
private int hash; // 0 means "not yet computed"

@Override
public int hashCode() {
  int result = hash;
  if (result == 0) {
    result = Short.hashCode(areaCode);
    result = 31 * result + Short.hashCode(prefix);
    result = 31 * result + Short.hashCode(lineNumber);
    hash = result;
  }
  return result;
}
```

## 10.11 Never pass an array to `Objects.hash` or compare arrays with `equals`.

> Why? Arrays inherit identity `equals` and `hashCode` from `Object`, so
> `a.equals(b)` on two arrays with identical contents is `false`, and
> `Objects.hash(array)` hashes the *reference*, not the contents. Both compile
> silently and both produce a class whose equal instances land in different
> buckets. Use `Arrays.equals` / `Arrays.hashCode`, or `Arrays.deepEquals` /
> `Arrays.deepHashCode` for nested arrays.
> **Violation — enforced by `error-prone/ArrayEquals` and
> `error-prone/ArrayHashCode`.**

```java
// bad — reference comparison and reference hashing
@Override
public boolean equals(Object o) {
  return o instanceof Payload other && bytes.equals(other.bytes);
}

@Override
public int hashCode() {
  return Objects.hash(bytes);
}

// good
@Override
public boolean equals(Object o) {
  return o instanceof Payload other && Arrays.equals(bytes, other.bytes);
}

@Override
public int hashCode() {
  return Arrays.hashCode(bytes);
}
```

## 10.12 Compare object references with `equals` (or `Objects.equals`), never with `==`.

> Why? `==` on reference types compares identity, which is almost never what the
> code means. `String` makes this actively dangerous: interned literals compare
> `true` with `==`, so the bug passes every test written with literals and fails
> the first time the value arrives from a socket or a database. `Objects.equals`
> additionally handles a `null` on either side.
> **Violation — enforced by `error-prone/ReferenceEquality`,
> `error-prone/BoxedPrimitiveEquality`, and `checkstyle/StringLiteralEquality`;
> `checkstyle/EqualsAvoidNull` additionally requires the literal on the left of
> the `equals` call.**

```java
// bad — passes with literals in tests, fails with parsed input in production
if (status == "ACTIVE") { ... }
if (cachedId == incomingId) { ... }   // Long boxes: == is identity above 127

// good
if ("ACTIVE".equals(status)) { ... }  // constant first: null-safe
if (Objects.equals(cachedId, incomingId)) { ... }
```

## 10.13 Never derive `equals` or `hashCode` from a mutable field of an object used as a map key.

> Why? The JDK 21 `hashCode` contract only holds "provided no information used in
> `equals` comparisons on the object is modified". Mutate such a field after
> insertion and the entry is stranded: it sits in the bucket for its old hash, so
> `map.containsKey(theSameObject)` returns `false` while iteration still yields
> it. There is no exception and no warning. Make key types immutable, or key the
> map on an immutable identifier instead of the whole object. No static analysis
> can see a post-insertion mutation, which is exactly why this one keeps
> shipping. **Suggestion.**

```java
// bad — mutable name participates in equals/hashCode
public final class Employee {
  private String name;

  public void rename(String name) {
    this.name = name;
  }

  @Override
  public boolean equals(Object o) {
    return o instanceof Employee other && Objects.equals(name, other.name);
  }

  @Override
  public int hashCode() {
    return Objects.hash(name);
  }
}

Map<Employee, Role> roles = new HashMap<>();
roles.put(employee, Role.ENGINEER);
employee.rename("Ada Lovelace");
roles.get(employee); // null — the entry is stranded in the old bucket

// good — key on an immutable identifier
public record EmployeeId(UUID value) {}

Map<EmployeeId, Role> roles = new HashMap<>();
roles.put(employee.id(), Role.ENGINEER);
```

## 10.14 Always override `toString`, and include every field a reader would want in a log line.

> Why? Effective Java, 3rd ed., Item 12: "Providing a good `toString`
> implementation makes your class much more pleasant to use and makes systems
> using the class easier to debug." The inherited form —
> `com.example.PhoneNumber@163b91` — is the single most common reason a
> production log line is useless. `toString` is called implicitly by string
> concatenation, by `Formatter`, and by every logging framework, so it is on the
> diagnostic path whether you wrote it or not.
> **Suggestion** — nothing flags a missing `toString`. Three adjacent misuses
> *are* mechanical, and all three are **Violations**:
> `error-prone/ObjectToString` flags "calling `toString` on Objects that don't
> override `toString()`", and `error-prone/ArrayToString` and
> `error-prone/StreamToString` flag the same call on an array or a `Stream`. All
> three match an actual `toString` call site, so none of them sees an object
> handed to an SLF4J `{}` placeholder — the log line below compiles clean and
> ships.

```java
// bad — the log line reads "rejected: com.example.PhoneNumber@163b91", and no
// check sees it: the object reaches toString through an SLF4J placeholder
log.warn("rejected: {}", phoneNumber);

// good
@Override
public String toString() {
  return "PhoneNumber[areaCode=%03d, prefix=%03d, lineNumber=%04d]"
      .formatted(areaCode, prefix, lineNumber);
}
```

## 10.15 Never put a secret, a credential, or unbounded data in `toString`.

> Why? `toString` output ends up in logs, in exception messages, in APM traces,
> and in bug reports. A `toString` that prints a password, a bearer token, a card
> number, or a full request body has moved that data into every system that
> touches your logs. Records are the common trap here, because the generated
> `toString` prints every component — override it when any component is
> sensitive. Unbounded fields (a byte array, a full result list) are the same
> problem in a different currency: they turn one log line into a megabyte.
> **Suggestion.**

```java
// bad — the generated record toString prints the secret verbatim
public record ApiCredential(String clientId, String clientSecret) {}

// good — override so the secret never reaches a log
public record ApiCredential(String clientId, String clientSecret) {
  public ApiCredential {
    Objects.requireNonNull(clientId, "clientId");
    Objects.requireNonNull(clientSecret, "clientSecret");
  }

  @Override
  public String toString() {
    return "ApiCredential[clientId=" + clientId + ", clientSecret=***]";
  }
}
```

## 10.16 Document whether `toString`'s format is specified, and give a matching factory when it is.

> Why? Effective Java, 3rd ed., Item 12: "you should document your intentions"
> — specifying the format commits you to it forever, because callers will parse
> it, but leaving it unspecified without saying so means callers will parse it
> *anyway* and you will break them. If you do specify a format, provide a static
> factory or `parse` method (see [§8.2](08-object-creation.md)) so nobody has to
> reverse-engineer it. **Suggestion.**

```java
// bad — no statement either way; callers will parse it and you will break them
@Override
public String toString() {
  return areaCode + "-" + prefix + "-" + lineNumber;
}

// good
/**
 * Returns a string representation of this phone number, in the form
 * {@code "XXX-YYY-ZZZZ"}, where {@code XXX} is the area code, {@code YYY} the
 * prefix, and {@code ZZZZ} the line number. This format is part of this class's
 * contract; {@link #parse(String)} accepts exactly the strings it produces.
 */
@Override
public String toString() {
  return "%03d-%03d-%04d".formatted(areaCode, prefix, lineNumber);
}

/** Parses a phone number in the format produced by {@link #toString()}. */
public static PhoneNumber parse(String text) { ... }
```

## 10.17 Implement `Comparable` only when the type has a single obvious natural ordering, and parameterise it with the class itself.

> Why? Effective Java, 3rd ed., Item 14: implement `Comparable` for "value
> classes that have an obvious natural ordering, such as alphabetical order,
> numerical order, or chronological order". When a type has several equally
> reasonable orderings — employees by salary, by hire date, by surname — none of
> them is natural, and a `Comparator` per ordering is the honest design.
> Parameterising `Comparable` with anything other than the implementing class
> produces a type that `Collections.sort` cannot use.
> **Violation — enforced by `error-prone/ComparableType`; a type that is both
> `Comparable` and its own `Comparator` is enforced by
> `error-prone/ComparableAndComparator`.**

```java
// bad — parameterised with Object rather than Version, so compareTo casts
// blindly and Collections.sort cannot use the natural ordering
public final class Version implements Comparable<Object> {
  @Override
  public int compareTo(Object o) {
    Version other = (Version) o;
    return Integer.compare(major, other.major);
  }
}

// good
public final class Version implements Comparable<Version> {
  @Override
  public int compareTo(Version other) {
    return Integer.compare(major, other.major);
  }
}
```

## 10.18 Obey the `compareTo` contract: signum symmetry, transitivity, and consistency of equal elements.

> Why? The JDK 21 `Comparable` docs require "`signum(x.compareTo(y)) ==
> -signum(y.compareTo(x))` for all `x` and `y`" and that "the relation is
> transitive". A comparator that violates either can make `Collections.sort`
> throw `IllegalArgumentException: Comparison method violates its general
> contract!` — the `Arrays.sort` javadoc documents that exception as
> "(optional) if the natural ordering of the array elements is found to violate
> the `Comparable` contract", so detection is best-effort and the message text
> is a TimSort implementation detail — or, worse, silently produce an order that
> depends on input permutation. Compare fields
> most-significant first, and return from the first non-zero result. One corner
> of the contract is mechanically checkable: `x.compareTo(x)` must be `0`.
> **Violation — a literal self-comparison is enforced by
> `error-prone/SelfComparison`.**

```java
// bad — the minor comparison overwrites the major one, so ordering is wrong and
// intransitive
@Override
public int compareTo(Version other) {
  int result = Integer.compare(major, other.major);
  result = Integer.compare(minor, other.minor);
  return result;
}

// good — return as soon as a field discriminates
@Override
public int compareTo(Version other) {
  int result = Integer.compare(major, other.major);
  if (result != 0) {
    return result;
  }
  result = Integer.compare(minor, other.minor);
  if (result != 0) {
    return result;
  }
  return Integer.compare(patch, other.patch);
}
```

## 10.19 Never implement `compareTo` by subtracting.

> Why? Effective Java, 3rd ed., Item 14 names this explicitly: "do not use the
> `<` and `>` operators … use the static `compare` methods". `a - b` overflows
> whenever the operands are far apart — `Integer.MIN_VALUE - 1` is positive — so
> the comparator reports that a very negative value is *greater* than a positive
> one, and the resulting sort order is silently wrong for exactly the inputs
> nobody tests. The floating-point variant is worse: subtraction cannot express
> `NaN` ordering at all. `Integer.compare`, `Long.compare`, and `Double.compare`
> are correct for the full range. **Suggestion.**

```java
// bad — overflows for distant operands; wrong order, no exception
@Override
public int compareTo(Account other) {
  return (int) (balanceMinorUnits - other.balanceMinorUnits);
}

// good
@Override
public int compareTo(Account other) {
  return Long.compare(balanceMinorUnits, other.balanceMinorUnits);
}
```

## 10.20 Build multi-key orderings with `Comparator.comparing(...).thenComparing(...)`, using the primitive-specialised factories for primitive keys.

> Why? The chained form states the sort keys in priority order on one line, which
> is both what the reader wants and what is hardest to get wrong by hand — there
> is no place to forget an early return (§10.18). Use `comparingInt`,
> `comparingLong`, and `comparingDouble` where the key is a primitive, because
> the generic `comparing` boxes every key on every comparison. Add
> `Comparator.nullsFirst` / `nullsLast` rather than writing null checks inline.
> **Suggestion.**

```java
// bad — hand-rolled chain: verbose, and one missing early return is a silent
// ordering bug
public int compare(Employee a, Employee b) {
  int result = a.department().compareTo(b.department());
  if (result != 0) {
    return result;
  }
  return Integer.compare(b.salary(), a.salary());
}

// good
private static final Comparator<Employee> BY_DEPARTMENT_THEN_SALARY =
    Comparator.comparing(Employee::department)
        .thenComparing(Comparator.comparingInt(Employee::salary).reversed())
        .thenComparing(Employee::surname, Comparator.nullsLast(String::compareTo));
```

## 10.21 Compare the result of `compareTo` against zero, never against `1` or `-1`.

> Why? The `Comparable` contract only specifies the *sign* of the returned
> integer, not its magnitude. `String.compareTo` returns the difference between
> character values, so `"b".compareTo("a")` is `1` but `"z".compareTo("a")` is
> `25`. Code written as `if (x.compareTo(y) == 1)` is therefore correct only by
> accident, and breaks the first time the implementation changes.
> **Violation — enforced by `error-prone/CompareToZero`.**

```java
// bad — "z".compareTo("a") is 25, so this branch never runs
if (a.compareTo(b) == 1) {
  return a;
}

// good
if (a.compareTo(b) > 0) {
  return a;
}
```

## 10.22 Keep `compareTo` consistent with `equals`, or document the inconsistency in the class Javadoc.

> Why? The JDK 21 `Comparable` docs: "It is strongly recommended, but *not*
> strictly required that `(x.compareTo(y)==0) == (x.equals(y))`. Generally
> speaking, any class that implements the `Comparable` interface and violates
> this condition should clearly indicate this fact. The recommended language is
> 'Note: this class has a natural ordering that is inconsistent with equals.'"
> The consequence is concrete: sorted collections use `compareTo` and hash
> collections use `equals`, so `BigDecimal("1.0")` and `BigDecimal("1.00")` are
> two elements in a `HashSet` and one element in a `TreeSet`. If your class has
> the same split, the Javadoc has to say so. **Suggestion.**

```java
// bad — BigDecimal.equals compares scale but compareTo does not, so a HashSet
// and a TreeSet of the same two values have different sizes, and nothing says so
public final class Money implements Comparable<Money> {
  private final BigDecimal amount;

  public Money(BigDecimal amount) {
    this.amount = Objects.requireNonNull(amount, "amount");
  }

  @Override
  public int compareTo(Money other) {
    return amount.compareTo(other.amount);
  }
}

// good — normalise the scale on construction, so equals and compareTo agree
/**
 * A monetary amount, normalised to two-decimal scale on construction so that
 * its natural ordering is consistent with {@code equals}.
 */
public final class Money implements Comparable<Money> {
  private final BigDecimal amount;

  public Money(BigDecimal amount) {
    this.amount = Objects.requireNonNull(amount, "amount").setScale(2, RoundingMode.HALF_EVEN);
  }

  @Override
  public boolean equals(Object o) {
    return o instanceof Money other && amount.equals(other.amount);
  }

  @Override
  public int hashCode() {
    return amount.hashCode();
  }

  @Override
  public int compareTo(Money other) {
    return amount.compareTo(other.amount);
  }
}
```

## 10.23 Prefer a `record` and let the compiler generate all three methods.

> Why? A record's generated `equals`, `hashCode`, and `toString` are derived from
> the record components, are contract-correct by construction, and stay correct
> when you add a component — which is the failure mode every hand-written version
> eventually hits. Every rule from §10.2 through §10.16 is satisfied for free.
> Write them by hand only when you need behaviour a record cannot express: a
> mutable field, a superclass, an ordering-sensitive `equals`, or a redacted
> `toString` (§10.15). See [Chapter 12](12-records.md) for the full treatment.
> **Suggestion.**

```java
// bad — three hand-written methods that must be re-audited every time a field
// is added, and silently go stale when someone forgets
public final class PhoneNumber {
  private final short areaCode;
  private final short prefix;
  private final short lineNumber;

  @Override
  public boolean equals(Object o) { ... }

  @Override
  public int hashCode() { ... }

  @Override
  public String toString() { ... }
}

// good — all three generated; adding a component updates all three
public record PhoneNumber(short areaCode, short prefix, short lineNumber) {
  public PhoneNumber {
    checkRange(areaCode, "areaCode");
    checkRange(prefix, "prefix");
  }

  private static void checkRange(short value, String name) {
    if (value < 0 || value > 999) {
      throw new IllegalArgumentException(name + " must be in [0, 999], was " + value);
    }
  }
}
```
