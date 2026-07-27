<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 19. `Optional`

`Optional<T>` is a container for zero or one non-null value. It exists to
give a method a return type that says "there may be no answer, and that is
normal" without handing the caller a `null` they will forget to check. It
was not designed as a general-purpose replacement for `null`, and the JDK
team said so in the class documentation: `Optional` "is primarily intended
for use as a method return type where there is a clear need to represent 'no
result,' and where using `null` is likely to cause errors."

That single sentence generates almost every rule in this chapter. This
chapter covers **Effective Java, 3rd ed., Item 55** ("Return optionals
judiciously"), Item 54 ("Return empty collections or arrays, not nulls"),
and the
[`Optional`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html)
/
[`OptionalInt`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/OptionalInt.html)
API contracts.

Nullability annotations, JSpecify, and the null-checking discipline for
everything that is *not* a return value are
[Chapter 25](25-nullability.md). Throwing instead of returning empty is
[Chapter 24](24-exceptions.md). `Optional.stream()` and the collectors that
produce optionals are [Chapter 18](18-streams.md).

**Tool alignment:** Error Prone ships a dense cluster of checks here —
`OptionalNotPresent`, `NullOptional`, `OptionalOfRedundantMethod`,
`OptionalMapToOptional`, `UnnecessaryOptionalGet`, `OptionalEquality`, and
`OptionalMapUnusedValue`. Rules that map to one are labeled **Violation**;
the rest are **Suggestion**.

## 19.1 Return `Optional<T>` when the absence of a result is a normal, expected outcome the caller must handle.

> Why? Effective Java, Item 55: "if a method might not be able to return a
> value and clients will have to perform special processing if no value is
> returned, you should probably return an optional." The type makes the empty
> case visible in the signature, so the caller cannot skip it by accident the
> way they can skip a `null` check. Reserve exceptions
> ([Chapter 24](24-exceptions.md)) for the cases that are genuinely
> exceptional — Item 55 notes that "exceptions should be reserved for
> exceptional conditions" and that creating one with a full stack trace is not
> free.

```java
// bad — a null the caller will forget to check, with no hint in the signature
public User findByEmail(String email) {
  return index.get(email); // null when absent
}

// bad — absence is normal here, so an exception is the wrong signal
public User findByEmail(String email) {
  User user = index.get(email);
  if (user == null) {
    throw new NoSuchElementException(email);
  }
  return user;
}

// good
public Optional<User> findByEmail(String email) {
  return Optional.ofNullable(index.get(email));
}
```

## 19.2 Never return `null` from a method whose return type is `Optional`.

> Why? The `Optional` API documentation is unambiguous: "A variable whose type
> is `Optional` should never itself be `null`; it should always point to an
> `Optional` instance." A null `Optional` defeats the entire purpose of the
> type — the caller's `result.isPresent()` throws a `NullPointerException` on
> a value they were told they did not need to null-check. Error Prone treats
> passing a literal `null` where an `Optional` is expected as a bug: "Passing a
> literal null to an Optional parameter is almost certainly a mistake. Did you
> mean to provide an empty Optional?" **Violation — enforced by Error Prone
> `NullOptional`.**

```java
// bad — the one null the caller will never guard against
public Optional<Session> current() {
  if (context == null) {
    return null;
  }
  return Optional.of(context.session());
}

// good
public Optional<Session> current() {
  return Optional.ofNullable(context).map(Context::session);
}
```

## 19.3 Never declare a field of type `Optional`.

> Why? Three independent reasons. `java.util.Optional` does not implement
> `Serializable`, so an `Optional` field makes the enclosing class
> unserializable and breaks most serialization frameworks that reflect over
> fields. Every instance pays an extra object header and an extra pointer hop
> for information a plain nullable field already carries. And it produces the
> absurdity of a two-state check becoming three-state: the field itself can be
> `null`, so readers must check `field != null && field.isPresent()`. Model
> optional state with a nullable field plus an accessor that returns
> `Optional`, or — better — with a type that makes the state explicit.

```java
// bad — unserializable, extra allocation, and still needs a null check
public final class Order {
  private Optional<Discount> discount; // can be null, empty, or present
}

// good — nullable field, Optional at the API boundary
public final class Order {
  private final @Nullable Discount discount;

  public Optional<Discount> discount() {
    return Optional.ofNullable(discount);
  }
}
```

## 19.4 Never declare a parameter of type `Optional`.

> Why? An `Optional` parameter forces every caller to wrap a value they
> already have — `save(Optional.of(name))` is strictly worse than
> `save(name)` — and it does not actually prevent `null`, because the caller
> can still pass a null `Optional`. Overloads, or a nullable parameter with an
> explicit annotation ([Chapter 25](25-nullability.md)), express the same
> thing without the ceremony. Error Prone flags the literal-null case
> directly. **Violation — enforced by Error Prone `NullOptional`.**

```java
// bad — every caller wraps, and null is still possible
public Report build(Range range, Optional<Filter> filter) { ... }

build(range, Optional.empty());
build(range, Optional.of(filter));
build(range, null); // still compiles

// good — overloads
public Report build(Range range) {
  return build(range, Filter.NONE);
}

public Report build(Range range, Filter filter) { ... }
```

## 19.5 Never use `Optional` as a record component.

> Why? A record component becomes a field ([19.3](#193-never-declare-a-field-of-type-optional))
> *and* a canonical-constructor parameter
> ([19.4](#194-never-declare-a-parameter-of-type-optional)) *and* an accessor
> return type, so an `Optional` component inherits every problem at once —
> plus the record's generated `equals`, `hashCode`, and `toString` now operate
> on the wrapper rather than the value. Keep the component nullable and add a
> non-canonical accessor if callers want an `Optional`.

```java
// bad — Optional.empty() and a null Optional are different records
public record Shipment(TrackingId id, Optional<Instant> deliveredAt) {}

// good — nullable component, Optional-returning accessor
public record Shipment(TrackingId id, @Nullable Instant deliveredAt) {

  public Optional<Instant> delivery() {
    return Optional.ofNullable(deliveredAt);
  }
}
```

## 19.6 Never put an `Optional` in a collection, an array, or a map key or value.

> Why? Effective Java, Item 55: "it is almost never appropriate to use an
> optional as a key, value, or element in a collection or array." A
> `Map<String, Optional<V>>` has two ways to say "no value" — the key is
> absent, or the key maps to an empty `Optional` — and every consumer must
> handle both. Item 55 calls this out as needless complexity that "invites
> confusing behavior." The same applies to `List<Optional<T>>`: filter the
> empties out at the point of construction.

```java
// bad — absent key and present-but-empty mean the same thing
Map<Sku, Optional<Price>> prices = new HashMap<>();
prices.put(sku, Optional.empty());

// bad — a list whose elements each need unwrapping
List<Optional<User>> users = ids.stream().map(this::findById).toList();

// good — absence is the absence of an entry
Map<Sku, Price> prices = new HashMap<>();

// good — flatten with Optional.stream()
List<User> users = ids.stream().map(this::findById).flatMap(Optional::stream).toList();
```

## 19.7 Never wrap a collection, map, array, or stream in `Optional` — return the empty one instead.

> Why? Effective Java, Item 54 ("Return empty collections or arrays, not
> nulls") and Item 55 together: "container types, including collections, maps,
> streams, arrays, and optionals, should not be wrapped in optionals."
> `Optional<List<T>>` gives the caller two empty states to distinguish —
> `Optional.empty()` and `Optional.of(List.of())` — with no semantic
> difference between them, and it blocks the for-each loop that an empty list
> supports for free.

```java
// bad — two representations of "nothing", and no direct iteration
public Optional<List<Order>> ordersFor(CustomerId id) {
  List<Order> found = repository.findByCustomer(id);
  return found.isEmpty() ? Optional.empty() : Optional.of(found);
}

// good
public List<Order> ordersFor(CustomerId id) {
  return repository.findByCustomer(id); // empty list when there are none
}
```

## 19.8 Never call `get()` or `orElseThrow()` on an `Optional` you have not proven is present.

> Why? `Optional.get()` throws `NoSuchElementException` on an empty optional,
> so an unguarded `get()` is a `NullPointerException` with extra steps — it
> reintroduces exactly the failure mode `Optional` was introduced to remove.
> Error Prone catches the provable cases: "This Optional has been confirmed to
> be empty at this point, so the call to `get()` or `orElseThrow()` will always
> throw." **Violation — enforced by Error Prone `OptionalNotPresent`.** The
> unprovable cases are worse, because they only fail on data you did not test
> with.

```java
// bad — throws NoSuchElementException whenever the user is unknown
User user = findByEmail(email).get();

// bad — the provable case: the branch is reached only when the optional is
// empty, so this always throws
Optional<User> maybeUser = findByEmail(email);
if (maybeUser.isEmpty()) {
  return maybeUser.get();
}

// bad — the check and the unwrap can drift apart during a refactor
Optional<User> found = findByEmail(email);
if (found.isPresent()) {
  render(found.get());
}

// good — the unwrap is impossible to separate from the check
findByEmail(email).ifPresent(this::render);
```

## 19.9 Prefer the combinators — `map`, `filter`, `flatMap`, `or`, `ifPresent`, `ifPresentOrElse`, `orElse`, `orElseGet`, `orElseThrow` — to `isPresent()` plus `get()`.

> Why? Effective Java, Item 55 lists these as the reason the type is worth
> having: they let a chain of optional-producing steps compose without the
> pyramid of `isPresent()` checks that a nullable chain requires. Error Prone
> also flags the mechanical version of this mistake — calling `get()` on an
> optional inside a lambda whose parameter is already the unwrapped value:
> "This code can be simplified by directly using the lambda parameters instead
> of calling `get..()` on optional." **Violation — enforced by Error Prone
> `UnnecessaryOptionalGet`.**

```java
// bad — three checks and three unwraps for one value
Optional<User> user = findByEmail(email);
String city;
if (user.isPresent()) {
  Optional<Address> address = user.get().address();
  if (address.isPresent()) {
    city = address.get().city();
  } else {
    city = "unknown";
  }
} else {
  city = "unknown";
}

// good
String city =
    findByEmail(email).flatMap(User::address).map(Address::city).orElse("unknown");
```

## 19.10 Use `flatMap` when the mapper itself returns an `Optional`; `map` here produces a nested optional.

> Why? `map` has signature `<U> Optional<U> map(Function<? super T, ? extends U>
> mapper)`, so mapping with an `Optional`-returning function yields
> `Optional<Optional<U>>` — a type that compiles, reads plausibly, and is
> almost never what was meant. Error Prone says exactly this: "Mapping to
> another Optional will yield a nested Optional. Did you mean flatMap?"
> **Violation — enforced by Error Prone `OptionalMapToOptional`.**

```java
// bad — Optional<Optional<Address>>; the outer one is never empty
Optional<Optional<Address>> address = findByEmail(email).map(User::address);

// good
Optional<Address> address = findByEmail(email).flatMap(User::address);
```

## 19.11 Use `orElseGet` when the fallback is expensive; `orElse` evaluates its argument unconditionally.

> Why? `orElse(T other)` takes a *value*, so the expression that produces it
> runs whether or not the optional is present — a database call, an object
> allocation, or a side effect fires on every invocation, including the ones
> that never use the result. `orElseGet(Supplier<? extends T> supplier)` takes a
> supplier and invokes it only on the empty path. Use `orElse` for constants
> and cheap literals; use `orElseGet` for anything that does work.

```java
// bad — createGuest() runs on every call, even when a user was found
User user = findByEmail(email).orElse(createGuest());

// bad — worse: the fallback has a side effect that fires unconditionally
Config config = cached().orElse(loadAndCache());

// good — the supplier runs only when the optional is empty
User user = findByEmail(email).orElseGet(this::createGuest);

// good — orElse is right for a constant
String display = nickname().orElse("anonymous");
```

## 19.12 Use `orElseThrow()` rather than `get()` when the empty case really is a programming error.

> Why? The two do the same thing — `orElseThrow()` (Java 10+) is documented as
> the preferred spelling precisely because `get()` reads like a safe accessor
> and is therefore easy to write without thinking. `orElseThrow()` names the
> consequence at the call site, and the one-argument
> `orElseThrow(Supplier<? extends X>)` overload lets you raise a domain
> exception the caller can actually act on
> ([Chapter 24](24-exceptions.md)).

```java
// bad — reads like a getter, throws like an assertion
Tenant tenant = tenantFor(request).get();

// good — the throw is visible
Tenant tenant = tenantFor(request).orElseThrow();

// better — a domain exception with a message the operator can use
Tenant tenant =
    tenantFor(request)
        .orElseThrow(() -> new UnknownTenantException(request.tenantHeader()));
```

## 19.13 Use `filter` to narrow an `Optional` rather than unwrapping to test a condition.

> Why? `filter(Predicate<? super T>)` returns the optional unchanged when the
> predicate holds and an empty optional when it does not, so a validity check
> stays inside the chain and the empty case stays a single code path.
> Unwrapping to test forces the fallback to be written twice — once for
> "absent" and once for "present but invalid".

```java
// bad — the "unknown" default is duplicated across two branches
Optional<User> found = findByEmail(email);
String label = found.isPresent() && found.get().isActive() ? found.get().name() : "unknown";

// good
String label =
    findByEmail(email).filter(User::isActive).map(User::name).orElse("unknown");
```

## 19.14 Use `or` to fall back to another `Optional` without unwrapping.

> Why? `or(Supplier<? extends Optional<? extends T>> supplier)` (Java 9+)
> chains alternative sources — cache, then primary, then default — while
> staying in `Optional` the whole way, and it is lazy, so the later lookups
> only run when the earlier ones came back empty. The `isPresent() ? … : …`
> version evaluates both sides and inverts the reading order.

```java
// bad — both lookups run, and the ternary reads backwards
Optional<Config> cached = cache.lookup(key);
Optional<Config> config = cached.isPresent() ? cached : registry.lookup(key);

// good — lazy, ordered, and still an Optional
Optional<Config> config = cache.lookup(key).or(() -> registry.lookup(key));
```

## 19.15 Use `Optional.stream()` to flatten a stream of optionals.

> Why? `Optional.stream()` (Java 9+) returns a `Stream<T>` of zero or one
> element, so `flatMap(Optional::stream)` drops the empties and unwraps the
> rest in one operation. The `filter(Optional::isPresent).map(Optional::get)`
> idiom it replaces is the `isPresent()`-plus-`get()` anti-pattern of 19.8
> spread across two pipeline stages, where a refactor can separate them.

```java
// bad — a get() that is only safe because of the previous stage
List<User> users =
    ids.stream()
        .map(this::findById)
        .filter(Optional::isPresent)
        .map(Optional::get)
        .toList();

// good
List<User> users = ids.stream().map(this::findById).flatMap(Optional::stream).toList();
```

## 19.16 Use `OptionalInt`, `OptionalLong`, and `OptionalDouble` for primitives — never `Optional<Integer>`.

> Why? Effective Java, Item 55: "you should never return an optional of a boxed
> primitive type," because such a value is "doubly expensive" — one allocation
> for the box and another for the `Optional`. The JDK ships the three
> primitive specializations for exactly this. Note their deliberate
> limitation: per the
> [`OptionalInt`
> API](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/OptionalInt.html),
> they offer `getAsInt`, `isPresent`, `isEmpty`, `ifPresent`,
> `ifPresentOrElse`, `stream`, `orElse`, `orElseGet`, and `orElseThrow` — and
> no `map`, `filter`, `flatMap`, or `or`. If you need to chain
> transformations, `stream()` back into an `IntStream`, or accept that the
> boxed form is the right trade-off for this particular call site and say so
> in a comment.

```java
// bad — two allocations per present value: one box, one Optional
public Optional<Integer> parsePort(String raw) {
  try {
    return Optional.of(Integer.valueOf(raw));
  } catch (NumberFormatException e) {
    return Optional.empty();
  }
}

// good
public OptionalInt parsePort(String raw) {
  try {
    return OptionalInt.of(Integer.parseInt(raw));
  } catch (NumberFormatException e) {
    return OptionalInt.empty();
  }
}

int port = parsePort(raw).orElse(DEFAULT_PORT);
```

## 19.17 Never compare `Optional` values with `==`, and never `equals` an `Optional` against its contents.

> Why? `Optional` is documented as a
> [value-based](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/doc-files/ValueBased.html)
> class, and that specification is explicit: "When two instances of a
> value-based class are equal (according to `equals`), a program should not
> attempt to distinguish between their identities, whether directly via
> reference equality or indirectly via an appeal to synchronization, identity
> hashing, serialization, or any other identity-sensitive mechanism." So `==`
> between two optionals holding equal values may be `true` or `false`
> depending on the JVM's caching
> decisions. Error Prone flags it as "comparison using reference equality
> instead of value equality." **Violation — enforced by Error Prone
> `OptionalEquality`.** The mirror-image mistake — `optional.equals(value)` —
> silently returns `false` forever, because an `Optional` is never equal to
> the thing inside it.

```java
// bad — reference comparison on a value-based class
if (findByEmail(a) == findByEmail(b)) { ... }

// bad — always false; an Optional<String> never equals a String
if (nickname().equals("root")) { ... }

// good
if (findByEmail(a).equals(findByEmail(b))) { ... }
if (nickname().filter("root"::equals).isPresent()) { ... }
```

## 19.18 Do not call `isPresent`, `orElse`, `ifPresent`, or `or` on an `Optional.of(...)` you just created.

> Why? `Optional.of` throws `NullPointerException` on a null argument and
> otherwise returns a guaranteed-present optional, so every emptiness-handling
> method applied to it is dead code — and its presence usually means the
> author meant `ofNullable`. Error Prone: "`Optional.of()` always returns a
> non-empty optional. Using `ifPresent`/`isPresent`/`orElse`/`orElseGet`/
> `orElseThrow`/`or`/`orNull` method on it is unnecessary and most probably a
> bug." **Violation — enforced by Error Prone `OptionalOfRedundantMethod`.**

```java
// bad — the fallback is unreachable; the author meant ofNullable
String name = Optional.of(user.displayName()).orElse("anonymous");

// good — when the value may be null
String name = Optional.ofNullable(user.displayName()).orElse("anonymous");

// good — when it genuinely cannot be null, drop the Optional entirely
String name = user.displayName();
```

## 19.19 Use `ifPresent`, not `map`, when the result is discarded.

> Why? `map` exists to transform a value into another value; using it for its
> side effect leaves an `Optional` of whatever the action happened to return —
> `Optional<Boolean>` below — that nobody reads, and misleads the next reader
> into looking for where the mapped value goes. Error
> Prone: "`Optional.ifPresent` is preferred over `Optional.map` when the
> return value is unused." **Violation — enforced by Error Prone
> `OptionalMapUnusedValue`.**

```java
// bad — the mapped Optional<Boolean> is thrown away
findByEmail(email).map(user -> queue.add(user));

// good
findByEmail(email).ifPresent(queue::add);
```

## 19.20 Use `ifPresentOrElse` when both branches have work to do.

> Why? `ifPresentOrElse(Consumer<? super T> action, Runnable emptyAction)`
> (Java 9+) expresses a two-branch effect in one statement, so the optional is
> inspected exactly once and neither branch can be added later without
> touching the other. The `isPresent()`/`else` version reopens the unwrap
> hazard of 19.8 for the sake of an `else`.

```java
// bad
Optional<User> found = findByEmail(email);
if (found.isPresent()) {
  audit.record(found.get());
} else {
  metrics.increment("lookup.miss");
}

// good
findByEmail(email)
    .ifPresentOrElse(audit::record, () -> metrics.increment("lookup.miss"));
```

## 19.21 Do not reach for `Optional` where a plain value, a null check, or an exception is the honest answer.

> Why? Effective Java, Item 55 warns that "optionals are similar in spirit to
> checked exceptions… in that they force the user of an API to confront the
> fact that there may be no value returned," and that this is a cost as well
> as a benefit: `Optional` is an allocation, an extra indirection, and an
> extra concept in every signature it touches. Wrapping a value you already
> hold, or a private helper's return that the single caller immediately
> unwraps, pays the cost and buys nothing. In performance-critical internal
> code, Item 55 explicitly allows returning `null` or throwing instead —
> provided the contract is documented.

```java
// bad — allocated and immediately discarded
Optional.ofNullable(request.header("X-Trace-Id")).ifPresent(span::setTraceId);
String id = Optional.of(user.id()).get();

// bad — a private helper whose only caller unwraps it on the next line
private Optional<Node> parent(Node node) {
  return Optional.ofNullable(node.parent());
}

// good
String traceId = request.header("X-Trace-Id");
if (traceId != null) {
  span.setTraceId(traceId);
}
String id = user.id();
```

## 19.22 Document what an empty `Optional` means.

> Why? A signature returning `Optional<Rate>` tells the caller a value may be
> absent but not *why* — no such currency pair, a rate that has expired, or a
> feed that is temporarily down are three very different situations that call
> for three different responses. Google Java Style
> [§7.1.3](https://google.github.io/styleguide/javaguide.html#s7.1.3-javadoc-block-tags)
> requires that `@return` "never appear with an empty description," and the
> empty case is the part of the description that actually needs writing. When
> the caller must distinguish several kinds of absence, `Optional` is the
> wrong type — use a sealed result type
> ([Chapter 13](13-sealed-types.md)) instead.

```java
// bad — the reader has to guess what empty means
/**
 * Returns the rate.
 *
 * @return the rate
 */
Optional<Rate> rateFor(CurrencyPair pair);

// good
/**
 * Returns the most recently published rate for {@code pair}.
 *
 * @param pair the currency pair to look up
 * @return the current rate, or empty if no rate has been published for this
 *     pair within the freshness window
 */
Optional<Rate> rateFor(CurrencyPair pair);
```
