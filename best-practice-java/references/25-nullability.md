<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 25. Nullability

Google's Java Style Guide is silent on `null`. It has nothing to say about
when a reference may be absent, how to say so in a signature, or where to
check. That silence is the reason this chapter exists: nullability is the
single largest source of production failures in Java, and it is the one
major discipline the normative style guide leaves entirely to the reader.

The rules here come from three places. Effective Java, 3rd ed., supplies the
design-level positions — Item 54 ("Return empty collections or arrays, not
nulls"), Item 55 ("Return optionals judiciously"), and Item 49 ("Check
parameters for validity"). The [JDK 21 API
docs](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Objects.html)
supply the mechanics: `Objects.requireNonNull`, `requireNonNullElse`, the
null-tolerant `Objects.equals`/`hashCode`/`toString`, and
`Comparator.nullsFirst`/`nullsLast`. And [JSpecify](https://jspecify.dev/)
supplies the vocabulary for stating nullability in the type system, which
[NullAway](https://github.com/uber/NullAway) then turns into a build
failure.

The chapter runs in that order — design null out first, check what is left
at the boundary second, annotate third, enforce fourth. `Optional`'s own
rules (return type only, never a field, never a parameter, never inside a
collection) are [Chapter 19](19-optional.md); this chapter cites them but
does not restate them. Null handling inside a `switch` is
[Chapter 23, §23.9](23-control-structures-and-switch.md).

**Tool alignment:** NullAway is the primary enforcer here and is what makes
§25.8-§25.10 mechanical rather than aspirational. Checkstyle's
`EqualsAvoidNull` and `UnnecessaryNullCheckWithInstanceOf`, and Error
Prone's `NullOptional`, `ReturnMissingNullable`, `FieldMissingNullable`,
`ParameterMissingNullable`, and `OptionalOfRedundantMethod` cover the rest.
Rules no tool can judge are labeled **Suggestion**.

## 25.1 Design `null` out of the API before you write a single null check.

> Why? Every `null` a method can return becomes a branch in every caller,
> forever. The cheapest null bug is the one the signature makes
> unrepresentable: an empty collection instead of a missing one, an
> `Optional` instead of a maybe-reference, a value type with a validated
> constructor instead of a bag of nullable fields. Null checking is what you
> do at the edges of a system that has already been designed this way — it
> is not a substitute for the design. **Suggestion.**

```java
// bad — three nullable fields; every consumer writes the same guards
public final class SearchResult {
  private List<Hit> hits;      // null means "no hits"
  private String cursor;       // null means "no more pages"
  private Facets facets;       // null means "faceting was off"
}

// good — absence is expressed in the types, not in the values
public record SearchResult(List<Hit> hits, Cursor cursor, Facets facets) {
  public SearchResult {
    hits = List.copyOf(hits);
    Objects.requireNonNull(cursor, "cursor");
    Objects.requireNonNull(facets, "facets");
  }

  /** Result carrying no hits, no further pages, and no faceting. */
  public static SearchResult empty() {
    return new SearchResult(List.of(), Cursor.END, Facets.NONE);
  }
}
```

## 25.2 Never return `null` from a method whose return type is a collection, a map, or an array.

> Why? Effective Java, 3rd ed., Item 54 ("Return empty collections or
> arrays, not nulls") is unambiguous: returning `null` "requires extra code
> in the client to handle the possibly null return value," and the argument
> that allocating an empty collection is expensive does not survive
> contact with `Collections.emptyList()` and `List.of()`, which return
> shared immutable instances at zero cost. The single missed null check is
> a `NullPointerException` in a caller written years later. **Suggestion.**

```java
// bad — every caller must guard, and one of them won't
public List<Order> ordersFor(CustomerId id) {
  List<Order> found = index.getOrDefault(id, List.of());
  return found.isEmpty() ? null : found;
}

// good — an empty list is a valid answer, not an absent one
public List<Order> ordersFor(CustomerId id) {
  return List.copyOf(index.getOrDefault(id, List.of()));
}
```

## 25.3 Never return `null` from a method declared to return `Optional`, and never pass `null` where an `Optional` is expected.

> Why? Effective Java, 3rd ed., Item 55 ("Return optionals judiciously")
> states that "you should never return a null value from a method that
> declares to return `Optional<T>`" — doing so gives callers the worst of
> both worlds, since they now have to null-check the very object whose
> entire purpose was to remove the null check. The symmetric mistake is
> passing a literal `null` to an `Optional` parameter instead of
> `Optional.empty()` — such a parameter should not exist at all
> ([Chapter 19](19-optional.md) forbids it), but third-party APIs have them
> and `Optional.empty()` is the only correct argument. **Violation —
> enforced by Error Prone `NullOptional`** for the argument half ("passing a
> literal null to an `Optional` parameter is almost certainly a mistake").
> The return half is a **Suggestion** — no linter reliably catches it, so it
> is a review obligation.

```java
// bad — an Optional that can itself be null
public Optional<Session> lookup(String token) {
  Session session = sessions.get(token);
  return session == null ? null : Optional.of(session);
}

client.connect(host, null);  // Optional<Credentials> parameter

// good
public Optional<Session> lookup(String token) {
  return Optional.ofNullable(sessions.get(token));
}

client.connect(host, Optional.empty());
```

## 25.4 Null-check every reference parameter of a public constructor with `Objects.requireNonNull`, and assign the result.

> Why? Effective Java, 3rd ed., Item 49 ("Check parameters for validity")
> singles out constructors: "it is critical to check the validity of
> parameters that are to be stored away for later use," because otherwise
> the `NullPointerException` surfaces at some unrelated method call, long
> after the frame that supplied the bad value is gone. Assigning
> `requireNonNull`'s return value rather than calling it as a statement
> keeps the check and the assignment on one line, so neither can be
> deleted without the other. **Suggestion.**

```java
// bad — the NPE arrives on the first send(), with no trace of who
// constructed this client with a null transport
public HttpClient(Transport transport, Duration timeout) {
  this.transport = transport;
  this.timeout = timeout;
}

// good — fails at the construction site, naming the offending parameter
public HttpClient(Transport transport, Duration timeout) {
  this.transport = Objects.requireNonNull(transport, "transport");
  this.timeout = Objects.requireNonNull(timeout, "timeout");
}
```

## 25.5 Validate and normalize record components in the compact constructor.

> Why? A `record` generates a canonical constructor that assigns every
> component verbatim, including `null`. The compact constructor is the only
> hook that runs before those assignments, so it is the single place where
> a record can guarantee its own invariants — and because records are the
> default value carrier in Java 21 (see
> [Chapter 12](12-records.md)), skipping it makes every record in the
> codebase a nullable-field bag. Defensive copying belongs here too.
> **Suggestion.**

```java
// bad — nothing stops new Shipment(null, null, null)
public record Shipment(TrackingId id, Address destination, List<Parcel> parcels) {}

// good — the record cannot exist in an invalid state
public record Shipment(TrackingId id, Address destination, List<Parcel> parcels) {
  public Shipment {
    Objects.requireNonNull(id, "id");
    Objects.requireNonNull(destination, "destination");
    parcels = List.copyOf(parcels);  // also rejects a null list and null elements
  }
}
```

## 25.6 Check nullability at public entry points and trust it internally.

> Why? Effective Java, 3rd ed., Item 49 draws exactly this line: public and
> protected methods must document and enforce their restrictions, but for
> "an unexported method... you, as the package author, control the
> circumstances under which the method is called, so you can and should
> ensure that only valid parameter values are ever passed in." Repeating
> the check in every private helper adds noise that trains reviewers to
> skim past null checks, which is how the one that mattered gets missed.
> **Suggestion.**

```java
// bad — the same check five frames deep, on a value that cannot be null
private BigDecimal lineTotal(LineItem item) {
  if (item == null) {
    return BigDecimal.ZERO;  // silently invents a wrong answer, too
  }
  return item.unitPrice().multiply(BigDecimal.valueOf(item.quantity()));
}

// good — validate once at the boundary...
public Invoice render(Order order) {
  Objects.requireNonNull(order, "order");
  return new Invoice(order.lines().stream().map(this::lineTotal).toList());
}

// ...and trust it inside
private BigDecimal lineTotal(LineItem item) {
  return item.unitPrice().multiply(BigDecimal.valueOf(item.quantity()));
}
```

## 25.7 Use `Objects.requireNonNullElse` and `requireNonNullElseGet` instead of a hand-written default.

> Why? `requireNonNullElse(obj, defaultObj)` returns the first argument if
> non-null and the second otherwise, and — importantly — throws
> `NullPointerException` if *both* are null, so a null default is caught
> rather than propagated. `requireNonNullElseGet` takes a
> `Supplier<? extends T>` and only evaluates it when the value is actually
> absent, which matters when the default is expensive. The ternary form
> evaluates its default eagerly and repeats the expression. **Suggestion.**

```java
// bad — the default is constructed on every call, absent or not
Config config = supplied != null ? supplied : loadDefaultConfig();
String name = raw != null ? raw : "anonymous";

// good
String name = Objects.requireNonNullElse(raw, "anonymous");
Config config = Objects.requireNonNullElseGet(supplied, this::loadDefaultConfig);
```

## 25.8 Mark packages `@NullMarked` and annotate the exceptions with `@Nullable`.

> Why? [JSpecify](https://jspecify.dev/docs/user-guide/) inverts the
> default: inside a `@NullMarked` scope "unannotated types in that scope
> are treated as if they were annotated with `@NonNull`", so the common
> case costs zero annotations and only the genuinely nullable references
> need marking. `@NullMarked` applies to a module, a package, a class or
> interface, or a method — package-level via `package-info.java` is the
> right granularity, because it makes the guarantee a property of the
> package rather than something each new file opts into. Note that package
> scope is not hierarchical: marking `com.foo` does not mark `com.foo.bar`,
> so every package needs its own `package-info.java`. **Violation —
> enforced by NullAway.** Error Prone's `ReturnMissingNullable`,
> `FieldMissingNullable`, and `ParameterMissingNullable` catch the
> annotations you forgot, but all three are experimental and ship at
> `SUGGESTION` severity — enable them explicitly if you want them to bite.

```java
// bad — nullability is undocumented; readers and tools both guess
package com.example.billing;

public interface InvoiceRepository {
  Invoice findById(InvoiceId id);          // returns null when missing?
  void save(Invoice invoice, String note); // is note optional?
}

// good — package-info.java establishes the default for the whole package...
// file: com/example/billing/package-info.java
@NullMarked
package com.example.billing;

import org.jspecify.annotations.NullMarked;

// ...and only the exceptions carry an annotation
// file: com/example/billing/InvoiceRepository.java
package com.example.billing;

import org.jspecify.annotations.Nullable;

public interface InvoiceRepository {
  @Nullable Invoice findById(InvoiceId id);
  void save(Invoice invoice, @Nullable String note);
}
```

## 25.9 Standardize on JSpecify's annotations; retire the historic alternatives.

> Why? Java accumulated at least five incompatible `@Nullable`
> annotations — `javax.annotation` (JSR-305, abandoned),
> `jakarta.annotation`, `org.checkerframework.checker.nullness.qual`,
> `org.springframework.lang`, and `edu.umd.cs.findbugs.annotations` — that
> differ in retention, in `@Target` (whether they annotate a *declaration*
> or a *type use*), and in whether they apply to generic type arguments at
> all. JSpecify exists precisely to end that fragmentation: it is a
> multi-vendor group, led by Google "by consent of the member
> organizations," whose participants include JetBrains, Oracle, Uber,
> Square, Microsoft, Meta, Sonar, Spring, Broadcom, and the EISOP team, and
> it is the annotation set NullAway's `JSpecifyMode` is built around. Mixing
> annotation families in one codebase means each tool sees a different
> subset of your intent. **Suggestion.**

```java
// bad — a declaration annotation that cannot describe the type argument;
// "the list is nullable" and "the elements are nullable" are the same
// annotation here
import javax.annotation.Nullable;

@Nullable
List<String> tags();

// good — a type-use annotation, so the position carries the meaning
import org.jspecify.annotations.Nullable;

@Nullable List<String> tags();          // the list may be absent
List<@Nullable String> tagsWithHoles(); // the list is present, elements may be null
```

## 25.10 Turn the annotations into a build failure with NullAway.

> Why? An annotation nobody checks is a comment. NullAway runs as an Error
> Prone plugin and verifies dereferences, assignments, and overrides
> against the annotations from §25.8. Configure it with
> `-XepOpt:NullAway:AnnotatedPackages` naming your own packages and
> `-XepOpt:NullAway:JSpecifyMode=true` to get JSpecify's generics-aware
> semantics. Two behaviours are worth knowing: NullAway treats *any*
> annotation whose simple name is `@Nullable` as nullable regardless of
> package, and in unannotated packages it makes optimistic assumptions
> (parameters nullable, returns non-null) unless
> `AcknowledgeRestrictiveAnnotations` is on. **Violation — enforced by
> NullAway.**

```java
// bad — the annotation is present but nothing verifies it, so this
// compiles and ships
public @Nullable User currentUser() { ... }

String greeting = "Hello, " + currentUser().displayName();  // NPE at runtime

// good — with NullAway on AnnotatedPackages, the line above fails the
// build: "dereferenced expression currentUser() is @Nullable"
User user = currentUser();
String greeting = user == null ? "Hello" : "Hello, " + user.displayName();
```

```kotlin
// build.gradle.kts — the enforcement half of the rule
import net.ltgt.gradle.errorprone.CheckSeverity
import net.ltgt.gradle.errorprone.errorprone

tasks.withType<JavaCompile>().configureEach {
  options.errorprone {
    check("NullAway", CheckSeverity.ERROR)
    option("NullAway:AnnotatedPackages", "com.example")
    option("NullAway:JSpecifyMode", "true")
  }
}
```

## 25.11 Use `Objects.equals` and `Objects.hashCode` instead of hand-rolling null guards.

> Why? `Objects.equals(a, b)` returns `true` when both are null, `false`
> when exactly one is, and delegates otherwise; `Objects.hashCode(o)`
> returns `0` for null. Writing those branches by hand is three lines of
> boilerplate per field, and the failure mode is asymmetric — the
> hand-written version usually gets `null.equals(null)` right and forgets
> the receiver, which is the case that throws. See
> [Chapter 10](10-equals-hashcode-tostring.md) for the full contract.
> **Suggestion.**

```java
// bad — NPE the moment this.email is null
@Override
public boolean equals(Object o) {
  if (!(o instanceof Contact other)) {
    return false;
  }
  return this.email.equals(other.email) && this.phone.equals(other.phone);
}

// good
@Override
public boolean equals(Object o) {
  if (!(o instanceof Contact other)) {
    return false;
  }
  return Objects.equals(email, other.email) && Objects.equals(phone, other.phone);
}

@Override
public int hashCode() {
  return Objects.hash(email, phone);
}
```

## 25.12 Use `Objects.toString(o, nullDefault)` instead of concatenating a possibly-null reference.

> Why? String concatenation renders `null` as the four characters `null`,
> which then travels into log lines, error messages, and — worst — database
> columns and URLs, where nobody can tell it apart from the literal string.
> `Objects.toString(Object, String)` returns the supplied default when the
> reference is absent, so the absence is rendered as something you chose.
> **Suggestion.**

```java
// bad — the audit row literally reads "actor=null"
audit.record("actor=" + currentUser + " action=" + action);

// good
audit.record(
    "actor=" + Objects.toString(currentUser, "<system>") + " action=" + action);
```

## 25.13 Sort nullable keys with `Comparator.nullsFirst` or `nullsLast`, not with null branches inside the comparator.

> Why? A hand-written comparator that guards for null has four cases and
> must stay antisymmetric and transitive across all of them, or `Arrays.sort`
> throws `IllegalArgumentException: Comparison method violates its general
> contract!` on some inputs and not others. `Comparator.nullsFirst(cmp)`
> and `nullsLast(cmp)` are specified to treat null as less than (or greater
> than) non-null and equal to another null, delegating everything else —
> the contract is correct by construction. **Suggestion.**

```java
// bad — four hand-written branches that a reviewer has to re-verify for
// antisymmetry and transitivity every time one of them is edited
users.sort(
    (a, b) -> {
      if (a.nickname() == null && b.nickname() == null) {
        return 0;
      }
      if (a.nickname() == null) {
        return 1;
      }
      if (b.nickname() == null) {
        return -1;
      }
      return a.nickname().compareTo(b.nickname());
    });

// good
users.sort(
    Comparator.comparing(User::nickname, Comparator.nullsLast(Comparator.naturalOrder())));
```

## 25.14 Put the operand you know is non-null on the left of `equals`.

> Why? Checkstyle's rationale is the whole argument: "calling the
> `equals()` method on String literals will avoid a potential
> `NullPointerException`. Also, it is pretty common to see null checks
> right before equals comparisons but following this rule such checks are
> not required." A literal, an enum constant, or an already-validated field
> on the left removes the null check entirely rather than adding one.
> **Violation — enforced by `checkstyle/EqualsAvoidNull`** for the case it
> can recognise mechanically, which is String literals (it "checks that any
> combination of String literals is on the left side of an `equals()`
> comparison"). The enum-constant and validated-field cases are the same
> idea but are a review obligation, not a check.

```java
// bad — NPE if the header is absent, or a redundant guard to prevent it
if (contentType != null && contentType.equals("application/json")) {
  parseJson(body);
}

// good — the literal cannot be null, so neither can the receiver
if ("application/json".equals(contentType)) {
  parseJson(body);
}

// also good when neither side is a literal
if (Objects.equals(contentType, expectedType)) {
  parseJson(body);
}
```

## 25.15 Don't null-check before `instanceof` or a type pattern.

> Why? `instanceof` is specified to evaluate to `false` for a null left
> operand, so `x != null && x instanceof Foo` is `x instanceof Foo` with a
> redundant clause. The redundancy is not harmless: it implies to the next
> reader that `instanceof` is null-*unsafe*, which is exactly the confusion
> that produces the same guard everywhere else. **Violation — enforced by
> `checkstyle/UnnecessaryNullCheckWithInstanceOf`.**

```java
// bad
if (payload != null && payload instanceof TextFrame frame) {
  handle(frame.text());
}

// good
if (payload instanceof TextFrame frame) {
  handle(frame.text());
}
```

## 25.16 Replace get-then-null-check with `getOrDefault` or `computeIfAbsent` — and know what each one actually does with a null value.

> Why? Both methods remove a branch, but they answer different questions
> and neither is a general null eraser. `getOrDefault` returns the default
> only when "this map contains no mapping for the key" — a key explicitly
> mapped to `null` still returns `null`, which is the trap. `computeIfAbsent`
> treats absent and mapped-to-null the same, and "if the mapping function
> returns `null`, no mapping is recorded," so it will not pollute the map
> with nulls. Use `getOrDefault` for reads with a fallback and
> `computeIfAbsent` for lazily populating a multimap or cache.
> **Suggestion.**

```java
// bad — three lines and a mutable local to express one lookup
List<Handler> handlers = registry.get(event);
if (handlers == null) {
  handlers = List.of();
}

// bad — repeats the key expression three times and is not atomic on a
// concurrent map
List<Handler> forEvent = registry.get(event);
if (forEvent == null) {
  forEvent = new ArrayList<>();
  registry.put(event, forEvent);
}
forEvent.add(handler);

// good — read with a fallback
List<Handler> handlers = registry.getOrDefault(event, List.of());

// good — lazily populate
registry.computeIfAbsent(event, key -> new ArrayList<>()).add(handler);
```

## 25.17 Know which factories reject `null` — and don't pipe possibly-null data through them.

> Why? The JDK is deliberately inconsistent here, and the inconsistency is
> a runtime `NullPointerException` rather than a compile error. `List.of`,
> `Set.of`, `Map.of`, and `Map.entry` all "disallow null keys and values"
> and throw `NullPointerException`; so does `Collectors.toUnmodifiableList`,
> which "disallows null values and will throw `NullPointerException` if it
> is presented with a null value." Meanwhile `Arrays.asList`,
> `Collections.unmodifiableList`, and `Stream.toList` all permit nulls —
> `Stream.toList` is specified as `Collections.unmodifiableList(new
> ArrayList<>(Arrays.asList(this.toArray())))`. Filter nulls *before* the
> collector, not after the NPE. See
> [Chapter 20](20-collections.md). **Suggestion.**

```java
// bad — one null email and the whole request fails inside the collector
List<String> emails =
    users.stream().map(User::email).collect(Collectors.toUnmodifiableList());

// bad — Map.of throws if any lookup misses
Map<String, Region> byCode = Map.of("us", regions.get("us"), "eu", regions.get("eu"));

// good — the absent values are removed where the intent is visible
List<String> emails =
    users.stream().map(User::email).filter(Objects::nonNull).toList();
```

## 25.18 Never let a nullable boxed value reach a primitive context.

> Why? Unboxing a `null` `Integer`, `Long`, or `Boolean` throws
> `NullPointerException` at a site that contains no visible dereference, so
> the stack trace points at an arithmetic expression and the reader spends
> ten minutes looking for the method call that wasn't there. The nastiest
> variant is the conditional operator: if one arm is a primitive and the
> other is a boxed type, the whole expression's type is the primitive, so
> the boxed arm is unboxed unconditionally — `flag ? boxedValue : 0` throws
> when `boxedValue` is null even though `0` looks like a safe fallback.
> **Suggestion.**

```java
// bad — a cache miss unboxes null and throws in the middle of arithmetic
Map<String, Integer> counts = new HashMap<>();
int total = counts.get("widgets") + 1;

// bad — the ternary's type is int, so stored is unboxed before the test
Integer stored = counts.get("widgets");
int value = useCache ? stored : 0;

// good — absence is resolved before any unboxing happens
int total = counts.getOrDefault("widgets", 0) + 1;
int value = useCache ? Objects.requireNonNullElse(stored, 0) : 0;
```

## 25.19 Use a Null Object instead of a nullable collaborator field.

> Why? A nullable dependency pushes the same `if (x != null)` guard into
> every method that uses it, and the cost of forgetting one is a
> `NullPointerException` on a path that only runs when the optional
> collaborator is absent — which is precisely the path with the least test
> coverage. A do-nothing implementation moves the decision to one place:
> the construction site. **Suggestion.**

```java
// bad — every call site guards, and the guards drift apart over time
public final class Uploader {
  private final ProgressListener listener;  // may be null

  public void upload(Path file) {
    if (listener != null) {
      listener.started(file);
    }
    transfer(file);
    listener.finished(file);  // the guard someone forgot
  }
}

// good — a no-op implementation removes every guard
public interface ProgressListener {
  /** Listener that discards every event. */
  ProgressListener NO_OP =
      new ProgressListener() {
        @Override
        public void started(Path file) {}

        @Override
        public void finished(Path file) {}
      };

  void started(Path file);

  void finished(Path file);
}

public final class Uploader {
  private final ProgressListener listener;

  public Uploader(ProgressListener listener) {
    this.listener = Objects.requireNonNull(listener, "listener");
  }

  public void upload(Path file) {
    listener.started(file);
    transfer(file);
    listener.finished(file);
  }
}
```

## 25.20 Don't round-trip a value through `Optional` only to hand back `null`.

> Why? `Optional.ofNullable(x).orElse(null)` is `x`, with two allocations
> and a false advertisement: the intermediate `Optional` makes a reader
> believe the null was handled somewhere. The same applies to
> `.map(...).orElse(null)` used as a null-safe navigation operator — the
> result is still nullable, so nothing was gained except the illusion that
> it wasn't. Either commit to `Optional` all the way to the caller (see
> [Chapter 19](19-optional.md)) or use a plain guard and annotate the
> result `@Nullable` (§25.8). **Suggestion.**

```java
// bad — an Optional that exists for two statements and changes nothing
public String displayName(UserId id) {
  return Optional.ofNullable(repository.find(id)).map(User::displayName).orElse(null);
}

// good — commit to Optional...
public Optional<String> displayName(UserId id) {
  return Optional.ofNullable(repository.find(id)).map(User::displayName);
}

// ...or stay nullable and say so
public @Nullable String displayName(UserId id) {
  User user = repository.find(id);
  return user == null ? null : user.displayName();
}
```
