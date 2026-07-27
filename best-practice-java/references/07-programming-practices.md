<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 7. Programming Practices

Google Java Style [§6 Programming
Practices](https://google.github.io/styleguide/javaguide.html#s6-programming-practices)
is four short subsections — [§6.1
`@Override`](https://google.github.io/styleguide/javaguide.html#s6.1-override-annotation),
[§6.2 Caught
exceptions](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions),
[§6.3 Static
members](https://google.github.io/styleguide/javaguide.html#s6.3-static-members),
and [§6.4
Finalizers](https://google.github.io/styleguide/javaguide.html#s6.4-finalizers)
— and every one of them is a rule about a mistake the compiler will happily
let you make. This chapter covers all four in full and then extends outward
to the adjacent everyday practices that share the same character: legal Java
that silently does the wrong thing.

Several neighbours own their own chapters and are only cross-referenced
here. Exception *design* — checked versus unchecked, what to throw across an
API boundary, how to chain causes — is [Chapter 24](24-exceptions.md); this
chapter only covers what §6.2 covers, which is what you may do with an
exception once you have caught it. `AutoCloseable` and resource lifecycle
are [Chapter 9](09-object-lifecycle-and-resources.md). The `equals`/`hashCode`
contract is [Chapter 10](10-equals-hashcode-tostring.md). Numeric precision
is [Chapter 29](29-numeric-types-and-literals.md). `switch` form and
exhaustiveness are [Chapter 23](23-control-structures-and-switch.md).

**Tool alignment:** most of this chapter is mechanically checkable. Error
Prone's `MissingOverride`, `ReferenceEquality`, `ArrayEquals`,
`ArrayHashCode`, `ArrayToString`, `ArrayAsKeyOfSetOrMap`, `Finally`, and
`BigDecimalLiteralDouble` cover the semantic traps; Checkstyle's
`EmptyCatchBlock`, `IllegalCatch`, `NoFinalizer`, `StringLiteralEquality`,
and `EqualsAvoidNull` cover the structural ones.

## 7.1 Annotate a method with `@Override` whenever it is legal to do so.

> Why? [§6.1](https://google.github.io/styleguide/javaguide.html#s6.1-override-annotation)
> requires that "a method is marked with the `@Override` annotation whenever
> it is legal." Without it, a rename or signature change in the supertype
> turns your override into a brand-new, never-called method, and the code
> still compiles. `@Override` converts that silent behavioral regression
> into a compile error.
> **Violation — enforced by `errorprone/MissingOverride`.**

```java
// bad — the supertype method is `post`; this typo compiles and is never called
final class CachingLedger extends AbstractLedger {
  public void postEntry(Entry entry) {
    cache.put(entry.id(), entry);
    super.post(entry);
  }
}

// good — the compiler rejects the typo immediately
final class CachingLedger extends AbstractLedger {
  @Override
  public void post(Entry entry) {
    cache.put(entry.id(), entry);
    super.post(entry);
  }
}
```

## 7.2 Annotate interface implementations with `@Override` too.

> Why? [§6.1](https://google.github.io/styleguide/javaguide.html#s6.1-override-annotation)
> spells out that this includes "a class method implementing an interface
> method." Interface implementations are where the annotation matters
> *most*: a class that fails to implement an abstract method fails to
> compile, but a class implementing a `default` method with a slightly
> wrong signature compiles fine and silently inherits the default forever.
> **Violation — enforced by `errorprone/MissingOverride`.**

```java
// bad — the interface declares `onSettled(Payment)`; this overload is dead code
final class AuditListener implements PaymentListener {
  public void onSettled(Payment payment, Instant at) {
    auditLog.record(payment.id(), at);
  }
}

// good
final class AuditListener implements PaymentListener {
  @Override
  public void onSettled(Payment payment) {
    auditLog.record(payment.id(), clock.instant());
  }
}
```

## 7.3 Omit `@Override` only when the parent method is `@Deprecated`.

> Why? [§6.1](https://google.github.io/styleguide/javaguide.html#s6.1-override-annotation)
> grants exactly one exception: "`@Override` may be omitted when the parent
> method is `@Deprecated`." Applying `@Override` there forces the
> deprecation warning into your subclass even though you have no choice
> about implementing it, so the exception exists to keep a build
> warning-clean without a blanket `@SuppressWarnings`. Note that this is a
> permission, not a requirement — keeping the annotation is fine if the
> deprecation warning is already suppressed for other reasons.

```java
// bad — @Override omitted on a live method, and applied to a deprecated one
// where it drags a deprecation warning into this class
final class ReportingLedger extends AbstractLedger {
  public void post(Entry entry) {
    metrics.increment("ledger.post");
    super.post(entry);
  }

  @Override
  public void postLegacy(Entry entry) {
    metrics.increment("ledger.post.legacy");
    super.postLegacy(entry);
  }
}

// good — annotate the live override; omit it on the @Deprecated parent method
final class ReportingLedger extends AbstractLedger {
  @Override
  public void post(Entry entry) {
    metrics.increment("ledger.post");
    super.post(entry);
  }

  public void postLegacy(Entry entry) {
    metrics.increment("ledger.post.legacy");
    super.postLegacy(entry);
  }
}
```

## 7.4 Never respond to a caught exception by doing nothing, unless a comment explains why that is correct.

> Why? [§6.2](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions)
> is blunt: "It is very rarely correct to do nothing in response to a
> caught exception," and where no action is taken "the reason this is
> justified is explained in a comment." An empty catch block is
> indistinguishable from an unfinished one; the comment is the only thing
> that tells a future reader whether the silence was a decision or an
> oversight.
> **Violation — enforced by `checkstyle/EmptyCatchBlock`, which accepts an
> empty catch containing any comment (`commentFormat` defaults to `.*`).**

```java
// bad — was this deliberate, or did someone stub it out and forget?
try {
  int i = Integer.parseInt(response);
  return handleNumericResponse(i);
} catch (NumberFormatException e) {
}
return handleTextResponse(response);

// good — the comment carries the justification
try {
  int i = Integer.parseInt(response);
  return handleNumericResponse(i);
} catch (NumberFormatException ok) {
  // it's not numeric; that's fine, just continue
}
return handleTextResponse(response);
```

## 7.5 In a test, name a deliberately ignored exception `expected`.

> Why? An empty catch in a test still has to say why it is empty, and in a
> test the variable name can carry that on its own: `expected` states that
> the throw *is* the assertion. This is a Checkstyle convention rather than
> a Google one — the current [§6.2](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions)
> makes no test-specific exception, and its example uses the unnamed
> variable `catch (NumberFormatException _)`, which is only a preview
> feature on Java 21. In new code prefer JUnit 5's
> `org.junit.jupiter.api.Assertions.assertThrows`, which states the intent
> in the assertion itself and additionally fails when *no* exception is
> thrown. See [Chapter 31](31-testing.md). **Suggestion** — rule 7.4's
> `checkstyle/EmptyCatchBlock` already rejects the bare empty catch;
> naming it `expected` only suppresses that check once
> `exceptionVariableName` is configured to `^expected` (its default, `^$`,
> matches no identifier).

```java
// bad — an empty catch in a test with an uninformative variable name
@Test
void popOnEmptyStackThrows() {
  try {
    emptyStack.pop();
    fail();
  } catch (NoSuchElementException e) {
  }
}

// good — the assertion states the expectation and fails if nothing throws
@Test
void popOnEmptyStackThrows() {
  assertThrows(NoSuchElementException.class, emptyStack::pop);
}
```

## 7.6 Log an exception or rethrow it — never both, and never neither.

> Why? Logging and rethrowing produces the same failure twice in the log,
> once with a partial stack and once with the full one, which makes an
> incident timeline unreadable and doubles the alert volume. Doing neither
> deletes the failure entirely. [§6.2](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions)
> lists the legitimate responses — log it, or rethrow it (possibly wrapped
> as an `AssertionError`) — and the choice belongs to whichever frame can
> actually decide what to do. See [Chapter 24](24-exceptions.md) and
> [Chapter 30](30-logging.md).

```java
// bad — the same failure lands in the log twice, from two different frames
try {
  return gateway.authorize(card, amount);
} catch (GatewayException e) {
  log.error("authorization failed", e);
  throw new PaymentException("authorization failed", e);
}

// good — add context, rethrow, and let the boundary that handles it log once
try {
  return gateway.authorize(card, amount);
} catch (GatewayException e) {
  throw new PaymentException("authorize card=" + card.maskedNumber(), e);
}
```

## 7.7 Never catch `Exception`, `Throwable`, `Error`, or `RuntimeException` to make a compiler complaint go away.

> Why? A broad catch swallows everything the block can raise, including the
> `NullPointerException` from your own bug and, for `Throwable`, the
> `OutOfMemoryError` that means the process should be dying. It converts a
> loud, diagnosable failure into a quiet wrong answer. Catch the specific
> types you can actually handle; Java 7 multi-catch makes listing several
> cheap.
> **Violation — enforced by `checkstyle/IllegalCatch`.**

```java
// bad — an NPE in mapRow() is now indistinguishable from a real parse failure
try {
  return mapRow(resultSet);
} catch (Exception e) {
  return Row.EMPTY;
}

// good
try {
  return mapRow(resultSet);
} catch (SQLException | DateTimeParseException e) {
  log.warn("unmappable row, skipping", e);
  return Row.EMPTY;
}
```

## 7.8 Never `return` or `throw` from a `finally` block.

> Why? A `finally` block that completes abruptly discards whatever the
> `try` or `catch` block was returning or throwing — including the original
> exception, which vanishes with no trace anywhere. The method then returns
> a plausible-looking value for an operation that actually failed. `javac`
> emits a `finally block does not complete normally` lint warning for this,
> and it is one worth promoting to an error.
> **Violation — enforced by `errorprone/Finally`.**

```java
// bad — an IOException from Files.lines is swallowed and -1 is returned
int lineCount(Path path) throws IOException {
  try (var lines = Files.lines(path)) {
    return (int) lines.count();
  } finally {
    return -1;
  }
}

// good — try-with-resources already guarantees the close
int lineCount(Path path) throws IOException {
  try (var lines = Files.lines(path)) {
    return (int) lines.count();
  }
}
```

## 7.9 Qualify a static member with its class name, never with an instance reference.

> Why? [§6.3](https://google.github.io/styleguide/javaguide.html#s6.3-static-members)
> requires that "when a reference to a static class member must be
> qualified, it is qualified with that class's name, not with a reference
> or expression of that class's type." Calling a static through an instance
> makes it read like polymorphic dispatch, which it is not — static methods
> are bound at compile time by the *declared* type, so the call ignores the
> runtime type entirely.

```java
// bad — reads like an instance method; `parseInt` has nothing to do with holder
Integer holder = Integer.valueOf(0);
int parsed = holder.parseInt(raw);

// good
int parsed = Integer.parseInt(raw);
```

## 7.10 Never reach a static member through an expression that does work.

> Why? [§6.3](https://google.github.io/styleguide/javaguide.html#s6.3-static-members)
> covers "a reference *or expression* of that class's type," and the
> expression case is the dangerous one: Java evaluates the receiver
> expression in full and then throws the result away, because the call
> binds statically. A side-effecting receiver therefore runs for no reason
> — checking out a pooled connection, opening a socket, incrementing a
> counter — and nothing in the source hints that it happened.

```java
// bad — a connection is checked out of the pool and immediately discarded
int timeout = pool.nextConnection().getDefaultTimeout();

// good — no connection is touched; the static is read directly
int timeout = Connection.getDefaultTimeout();
```

## 7.11 Never override `Object.finalize`.

> Why? [§6.4](https://google.github.io/styleguide/javaguide.html#s6.4-finalizers)
> is two sentences: "Do not override `Object.finalize`. Finalization
> support is scheduled for removal." The JDK 21 API docs
> mark the method `@Deprecated(since="9", forRemoval=true)` and state that
> "finalization is deprecated and subject to removal in a future release.
> The use of finalization can lead to problems with security, performance,
> and reliability." Beyond that, a finalizer runs at an unspecified time on
> an unspecified thread, may never run at all, and an exception thrown from
> one is silently discarded — leaving the object half-cleaned with no
> record.
> **Violation — enforced by `checkstyle/NoFinalizer`.** (Do not reach for
> `checkstyle/SuperFinalize` here: it checks that an overriding
> `finalize()` calls `super.finalize()`, which presumes the finalizer you
> should not have written.)

```java
// bad — may never run; may run after the process has already leaked the handle
final class NativeBuffer {
  private long handle;

  @Override
  protected void finalize() throws Throwable {
    try {
      free(handle);
    } finally {
      super.finalize();
    }
  }
}

// good — deterministic release at a point the caller controls
final class NativeBuffer implements AutoCloseable {
  private long handle;

  @Override
  public void close() {
    if (handle != 0L) {
      free(handle);
      handle = 0L;
    }
  }
}
```

## 7.12 Release resources with try-with-resources; treat `Cleaner` as a last-ditch net, not a strategy.

> Why? The `Object.finalize` API note in JDK 21 gives exactly two
> replacements: "add a `close` method... and implement `AutoCloseable` to
> enable use of the try-with-resources statement," or use
> `java.lang.ref.Cleaner`. Only the first is deterministic. `Cleaner` is
> still tied to garbage collection — its own javadoc says "the behavior of
> cleaners during `System.exit` is implementation specific. No guarantees
> are made relating to whether cleaning actions are invoked or not," and
> that "the cleaning action must not refer to the object being registered.
> If so, the object will not become phantom reachable and the cleaning
> action will not be invoked automatically." The javadoc adds that an
> "inner" class, anonymous or not, "must not be used because it implicitly
> contains a reference to the outer instance." That trap is why most
> `Cleaner` uses are wrong. Reach for it
> only to catch a caller who forgot to `close`, never as the primary path.
> See [Chapter 9](09-object-lifecycle-and-resources.md).

```java
// bad — the lambda captures `this`, so the buffer is never phantom-reachable
final class NativeBuffer implements AutoCloseable {
  private static final Cleaner CLEANER = Cleaner.create();
  private long handle;

  NativeBuffer(long handle) {
    this.handle = handle;
    CLEANER.register(this, () -> free(this.handle));
  }

  @Override
  public void close() {
    free(handle);
  }
}

// good — the cleaning state is a static nested class that captures nothing
final class NativeBuffer implements AutoCloseable {
  private static final Cleaner CLEANER = Cleaner.create();

  private final Cleaner.Cleanable cleanable;

  NativeBuffer(long handle) {
    this.cleanable = CLEANER.register(this, new Release(handle));
  }

  @Override
  public void close() {
    cleanable.clean();
  }

  private record Release(long handle) implements Runnable {
    @Override
    public void run() {
      free(handle);
    }
  }
}
```

## 7.13 Iterate with the enhanced `for` loop unless you need the index itself.

> Why? Effective Java, 3rd ed., Item 58 ("Prefer for-each loops to
> traditional for loops") points out that the index and iterator variables
> in a traditional loop are "just clutter" and, in nested loops, an
> outright bug source — the classic failure is calling `outer.next()` in
> the inner loop and exhausting the outer iterator. The enhanced form
> removes the variable that can be wrong. Keep the indexed form only when
> the index is part of the logic, or when you must remove elements during
> traversal (which needs an explicit `Iterator`).

```java
// bad — the index exists only to reach the element
for (int i = 0; i < payments.size(); i++) {
  ledger.post(payments.get(i));
}

// good
for (Payment payment : payments) {
  ledger.post(payment);
}

// good — the index is genuinely part of the logic, so keep it
for (int i = 0; i < columns.size(); i++) {
  statement.setObject(i + 1, columns.get(i));
}
```

## 7.14 Compare with `==` only for enums, `null`, and deliberate identity checks.

> Why? `==` on references asks "same object," which is almost never the
> question. It is famously wrong for `String` (two equal strings from
> different sources are different objects) and quietly wrong for boxed
> numerics outside the `Integer` cache range of −128..127. Enums are the
> clean exception: the language guarantees one instance per constant, so
> `==` is both correct and null-safe there.
> **Violation — enforced by `errorprone/ReferenceEquality` and
> `checkstyle/StringLiteralEquality`.**

```java
// bad — true only when the JVM happens to have interned both operands
if (currencyCode == "USD") {
  applyDomesticFee();
}

// bad — both operands are boxed, so this is false for any count above 127
// (the JLS only guarantees the cache for -128..127; a larger cache makes
// the bug intermittent rather than absent)
Integer count = repository.count();
Integer expected = snapshot.count();
if (count == expected) {
  return;
}

// good
if ("USD".equals(currencyCode)) {
  applyDomesticFee();
}

// good — compare primitives, or use Objects.equals if either may be null
int count = repository.count();
int expected = snapshot.count();
if (count == expected) {
  return;
}

// good — enums have exactly one instance per constant
if (status == Status.SETTLED) {
  return;
}
```

## 7.15 Call `equals` on the operand that cannot be null.

> Why? `maybeNull.equals(CONSTANT)` throws `NullPointerException` for the
> one input you most need to handle; `CONSTANT.equals(maybeNull)` returns
> `false` and moves on. When neither side is known non-null,
> `java.util.Objects.equals(a, b)` handles both nulls and is the honest
> way to say "either may be absent."
> **Violation for the literal case — enforced by
> `checkstyle/EqualsAvoidNull`, which "checks that any combination of
> String literals is on the left side of an `equals()` comparison."** When
> neither operand is a literal no check can tell which one may be null, so
> that half is a **Suggestion**.

```java
// bad — NPE whenever currencyCode is absent
if (currencyCode.equals("USD")) {
  applyDomesticFee();
}

// good — the literal is the receiver
if ("USD".equals(currencyCode)) {
  applyDomesticFee();
}

// good — neither operand is known non-null
if (Objects.equals(previous.reference(), current.reference())) {
  return;
}
```

## 7.16 Never call `toString`, `equals`, or `hashCode` on an array.

> Why? Arrays inherit all three from `Object` and override none of them.
> `toString` yields `[Ljava.lang.String;@1b6d3586`, `equals` is reference
> identity, and `hashCode` is the identity hash — so a log line shows
> nothing, a comparison of two equal arrays is `false`, and a hash lookup
> always misses. `java.util.Arrays` provides the content-based versions,
> with `deepToString` / `deepEquals` / `deepHashCode` for nested arrays.
> **Violation — enforced by `errorprone/ArrayToString`,
> `errorprone/ArrayEquals`, and `errorprone/ArrayHashCode`.**

```java
// bad — logs an identity hash, compares identity, hashes identity
String[] expected = {"USD", "EUR"};
String[] actual = loadCurrencies();
log.info("currencies={}", actual);
if (expected.equals(actual)) {
  return actual.hashCode();
}

// good
String[] expected = {"USD", "EUR"};
String[] actual = loadCurrencies();
log.info("currencies={}", Arrays.toString(actual));
if (Arrays.equals(expected, actual)) {
  return Arrays.hashCode(actual);
}
```

## 7.17 Never use an array as a `Set` element or a `Map` key.

> Why? This is 7.16's consequence at the collection level: because arrays
> use identity `equals`/`hashCode`, every `get` with a freshly built key
> misses and every `add` of an equal-content array creates a duplicate
> entry. The collection appears to work in a unit test that reuses the same
> array reference and fails in production. Convert to a `List`, a `String`,
> or a record with a proper contract.
> **Violation — enforced by `errorprone/ArrayAsKeyOfSetOrMap`.**

```java
// bad — the lookup misses even though the bytes are identical
Map<byte[], Session> sessions = new HashMap<>();
sessions.put(token, session);
Session found = sessions.get(token.clone());

// good — a value-typed key with a real equals/hashCode contract
Map<String, Session> sessions = new HashMap<>();
sessions.put(HexFormat.of().formatHex(token), session);
Session found = sessions.get(HexFormat.of().formatHex(token.clone()));
```

## 7.18 Never use `float` or `double` where exact values matter.

> Why? Effective Java, 3rd ed., Item 60 ("Avoid `float` and `double` if
> exact answers are required") shows the canonical failure: `1.03 - 0.42`
> prints `0.6100000000000001`, because binary floating point cannot
> represent most decimal fractions. Money, tax, and any value a human will
> reconcile need `BigDecimal` — constructed from a `String`, never from a
> `double`, since `new BigDecimal(0.1)` faithfully preserves the binary
> error. See [Chapter 29](29-numeric-types-and-literals.md).
> **Violation for `new BigDecimal(double)` — enforced by
> `errorprone/BigDecimalLiteralDouble` ("new BigDecimal(double) loses
> precision in this case").** Choosing `double` for a value that must be
> exact is a **Suggestion**; no check can tell which of your `double`s
> represents money.

```java
// bad — prints 0.6100000000000001, and the BigDecimal fix reintroduces it
double change = 1.03 - 0.42;
BigDecimal price = new BigDecimal(1.03);

// good — decimal arithmetic all the way down
BigDecimal change = new BigDecimal("1.03").subtract(new BigDecimal("0.42"));
BigDecimal price = new BigDecimal("1.03");
```

## 7.19 Make value types immutable by default.

> Why? Effective Java, 3rd ed., Item 17 ("Minimize mutability") lists what
> immutability buys: an immutable object is thread-safe with no
> synchronization, can be shared and cached freely, and is safe to use as a
> map key because its hash can never change underneath the map. In Java 21
> a `record` gives you the whole package — final components, a generated
> value-based `equals`/`hashCode`, and a compact constructor for
> validation. See [Chapter 12](12-records.md).

```java
// bad — any holder can mutate the amount under every other holder
final class Money {
  private BigDecimal amount;
  private Currency currency;

  void setAmount(BigDecimal amount) {
    this.amount = amount;
  }
}

// good
record Money(BigDecimal amount, Currency currency) {
  Money {
    Objects.requireNonNull(amount, "amount");
    Objects.requireNonNull(currency, "currency");
  }

  Money plus(Money other) {
    if (!currency.equals(other.currency)) {
      throw new IllegalArgumentException("currency mismatch: " + currency);
    }
    return new Money(amount.add(other.amount), currency);
  }
}
```

## 7.20 Copy mutable input on the way in and mutable state on the way out.

> Why? Effective Java, 3rd ed., Item 50 ("Make defensive copies when
> needed") covers both directions, and both matter: storing a caller's
> `List` directly lets them mutate your state after construction, and
> returning your internal `List` lets them mutate it at any time
> afterwards. `List.copyOf`, `Set.copyOf`, and `Map.copyOf` (Java 10+)
> return genuinely unmodifiable snapshots and are the one-line answer to
> both.

```java
// bad — the caller keeps a live handle on the router's routing table
final class Router {
  private final List<Route> routes;

  Router(List<Route> routes) {
    this.routes = routes;
  }

  List<Route> routes() {
    return routes;
  }
}

// good — copied on the way in; the copy is already unmodifiable on the way out
final class Router {
  private final List<Route> routes;

  Router(List<Route> routes) {
    this.routes = List.copyOf(routes);
  }

  List<Route> routes() {
    return routes;
  }
}
```

## 7.21 Put no side effects in an `assert`.

> Why? Assertions are disabled unless the JVM is started with `-ea`, and
> they are disabled in essentially every production deployment. Anything
> the assert expression *does* — draining a queue, advancing an iterator,
> incrementing a counter — therefore happens in your tests and not in
> production, which is the worst possible place for a behavioral
> difference. Perform the action on its own line and assert on the result.

```java
// bad — with assertions off (the default) the queue is never drained
assert queue.poll() != null;

// good — the poll always happens; only the check is conditional
Message message = queue.poll();
assert message != null : "queue drained by another thread";
```

## 7.22 Never validate a public method's arguments with `assert`.

> Why? Effective Java, 3rd ed., Item 49 ("Check parameters for validity")
> draws the line: assertions express beliefs about *internal* invariants
> that must hold no matter what a caller does, so they are appropriate for
> private and package-private helpers. A public method's parameters come
> from outside your control, so the check must be unconditional.
> `java.util.Objects.requireNonNull` and an explicit
> `IllegalArgumentException` fail fast in every deployment, with a message
> that names the offending parameter.

```java
// bad — assertions are off in production, so null sails straight through
public void register(Listener listener, int priority) {
  assert listener != null;
  assert priority >= 0;
  listeners.add(listener);
}

// good
public void register(Listener listener, int priority) {
  Objects.requireNonNull(listener, "listener");
  if (priority < 0) {
    throw new IllegalArgumentException("priority must be non-negative, got " + priority);
  }
  listeners.add(listener);
}
```
