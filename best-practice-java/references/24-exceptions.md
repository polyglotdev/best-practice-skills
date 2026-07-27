<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 24. Exceptions

Java's exception mechanism is two designs wearing one syntax. Unchecked
exceptions are a crash report: they say a programmer made a mistake and the
only reasonable response is to fail loudly. Checked exceptions are an API
contract: they say a caller can plausibly do something about this and the
compiler will make sure they consider it. Most exception-handling defects
come from confusing the two — declaring a crash report as a contract, or
catching a contract and pretending it was a crash report.

This chapter is built almost entirely on Effective Java, 3rd ed.,
Chapter 10 (Items 69-77). Google's Java Style Guide contributes exactly one
normative rule to the topic:
[§6.2 Caught exceptions: not ignored](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions),
which states that "it is very rarely correct to do nothing in response to a
caught exception," and that when no action is taken, "the reason this is
justified is explained in a comment." Javadoc's `@throws` ordering and
non-emptiness obligations come from
[§7.1.3](https://google.github.io/styleguide/javaguide.html#s7.1.3-javadoc-block-tags).

Three neighbouring topics live elsewhere. Why control flow must not run
through exceptions in the first place is stated in
[Chapter 23, §23.19](23-control-structures-and-switch.md). The mechanics of
`try`-with-resources and `AutoCloseable` design belong to
[Chapter 9](09-object-lifecycle-and-resources.md); §24.18 here covers only
what that construct means for *exceptions*. And the logging rules that
§24.17 leans on are in [Chapter 30](30-logging.md).

**Tool alignment:** Checkstyle's `IllegalCatch`, `IllegalThrows`,
`EmptyCatchBlock`, and `JavadocMethod` (with `validateThrows` enabled), plus
Error Prone's `EmptyCatch`, `CatchAndPrintStackTrace`, `Finally`,
`ThrowSpecificExceptions`, `InterruptedExceptionSwallowed`, and
`AssertionFailureIgnored`, cover a large
share of this chapter mechanically. Design rules no tool can judge —
"is this exception at the right abstraction level?" — are labeled
**Suggestion**.

## 24.1 Use exceptions only for exceptional conditions.

> Why? Effective Java, 3rd ed., Item 69 ("Use exceptions only for
> exceptional conditions") gives three reasons an exception-driven loop is
> worse than the obvious one: it is slower, because placing code inside a
> `try` block inhibits JVM optimisations that a plain bounds check enables;
> it obscures intent; and — the reason that actually bites — the `catch`
> silently absorbs the *same* exception thrown from anywhere inside the
> loop body, turning an unrelated bug into a normal-looking termination.
> **Suggestion.**

```java
// bad — the loop ends by throwing, and any AIOOBE raised inside
// process() is indistinguishable from the intended terminator
try {
  int i = 0;
  while (true) {
    process(items[i++]);
  }
} catch (ArrayIndexOutOfBoundsException e) {
  // reached the end
}

// good
for (Item item : items) {
  process(item);
}
```

## 24.2 Give a state-dependent method a state-testing method or a distinguished return value, so callers never need a `try` block for the normal case.

> Why? Effective Java, 3rd ed., Item 69 spells out the API-design
> consequence of §24.1: "a well-designed API must not force its clients to
> use exceptions for ordinary control flow." `Iterator` models the
> state-testing form (`hasNext` guards `next`); `Optional` and `null` model
> the distinguished-return form. Prefer the distinguished return when the
> object can be mutated concurrently or when the test would duplicate the
> work the action does, since a separate test-then-act pair is racy and
> potentially twice as expensive — an `Optional<Token> poll()` is the right
> shape there. **Suggestion.**

```java
// bad — the only way to ask "is there one?" is to try and fail
public final class TokenQueue {
  public Token next() {
    if (tokens.isEmpty()) {
      throw new NoSuchElementException("queue exhausted");
    }
    return tokens.removeFirst();
  }
}

// caller is forced into exception-driven control flow
try {
  while (true) {
    consume(queue.next());
  }
} catch (NoSuchElementException e) {
  // done
}

// good — a state-testing method makes the normal case ordinary code
public final class TokenQueue {
  public boolean hasNext() {
    return !tokens.isEmpty();
  }

  public Token next() {
    if (tokens.isEmpty()) {
      throw new NoSuchElementException("queue exhausted");
    }
    return tokens.removeFirst();
  }
}

while (queue.hasNext()) {
  consume(queue.next());
}
```

## 24.3 Use checked exceptions for conditions the caller can plausibly recover from, and unchecked exceptions for programming errors.

> Why? Effective Java, 3rd ed., Item 70 ("Use checked exceptions for
> recoverable conditions and runtime exceptions for programming errors")
> makes this the primary axis of exception design: a checked exception
> "forces the caller to handle the exception in a catch clause or to
> propagate it outward," which is only appropriate when there is something
> useful to do. A programming error — a bad argument, a violated invariant
> — has no recovery, so a checked exception there just spreads noise
> through every frame up the stack. **Suggestion.**

```java
// bad — a bug in the caller, declared as a contract the caller must handle
public void setRate(BigDecimal rate) throws InvalidRateException {
  if (rate.signum() < 0) {
    throw new InvalidRateException(rate);
  }
  this.rate = rate;
}

// good — programming error is unchecked; a genuinely recoverable
// condition stays checked
public void setRate(BigDecimal rate) {
  if (rate.signum() < 0) {
    throw new IllegalArgumentException("rate must be non-negative, was " + rate);
  }
  this.rate = rate;
}

public Account withdraw(Money amount) throws InsufficientFundsException {
  if (balance.compareTo(amount) < 0) {
    throw new InsufficientFundsException(id, balance, amount);
  }
  return debited(amount);
}
```

## 24.4 Don't add a checked exception when a state-testing method or an `Optional` return would serve.

> Why? Effective Java, 3rd ed., Item 71 ("Avoid unnecessary use of checked
> exceptions") observes that a single checked exception is often the worst
> case of all: it forces every caller into a `try` block that cannot be
> chained or streamed, for one outcome. The item's own remedy is to "turn a
> checked exception into an unchecked exception by breaking the method into
> two" — a state-testing method plus an action — or to return `Optional`.
> See [Chapter 19](19-optional.md) for when `Optional` is the right return
> type. **Suggestion.**

```java
// bad — one checked exception makes the method unusable in a stream
public Config load(Path path) throws MissingConfigException {
  if (!Files.exists(path)) {
    throw new MissingConfigException(path);
  }
  return parse(path);
}

// good — absence is a value, so callers compose instead of catching
public Optional<Config> load(Path path) {
  return Files.exists(path) ? Optional.of(parse(path)) : Optional.empty();
}
```

## 24.5 Reach for a standard exception before writing your own.

> Why? Effective Java, 3rd ed., Item 72 ("Favor the use of standard
> exceptions") lists the payoff: your API is easier to learn because it
> matches conventions programmers already know, it is easier to read
> because it has fewer unfamiliar types, and fewer exception classes means
> a smaller footprint and less class-loading time. The six below cover the
> overwhelming majority of real cases. **Suggestion.**

| Exception | Use when |
|---|---|
| `IllegalArgumentException` | A parameter value is inappropriate. |
| `IllegalStateException` | The receiver's state makes the call invalid. |
| `NullPointerException` | A parameter is `null` where `null` is prohibited. |
| `IndexOutOfBoundsException` | An index parameter is out of range. |
| `UnsupportedOperationException` | The receiver does not support this operation. |
| `ConcurrentModificationException` | Concurrent modification was detected. |

```java
// bad — three bespoke classes that say nothing the standard ones don't
public void connect(String host, int port) {
  if (host == null) {
    throw new NullHostException();
  }
  if (port < 0 || port > 65535) {
    throw new BadPortException(port);
  }
  if (closed) {
    throw new ClosedClientException();
  }
}

// good
public void connect(String host, int port) {
  Objects.requireNonNull(host, "host");
  if (port < 0 || port > 65535) {
    throw new IllegalArgumentException("port out of range: " + port);
  }
  if (closed) {
    throw new IllegalStateException("client is closed");
  }
}
```

## 24.6 Distinguish `IllegalArgumentException` from `IllegalStateException` by asking whether the call would have succeeded with different arguments.

> Why? Effective Java, 3rd ed., Item 72 gives exactly this tie-breaker: "if
> no argument values would have worked, throw `IllegalStateException`;
> otherwise throw `IllegalArgumentException`." Getting it backwards sends a
> debugging reader to inspect the wrong thing — the call site's arguments
> instead of the object's lifecycle, or vice versa. **Suggestion.**

```java
// bad — the argument is fine; the object is in the wrong state
public void send(Message message) {
  if (!connected) {
    throw new IllegalArgumentException("cannot send: not connected");
  }
  transport.write(message);
}

// good
public void send(Message message) {
  if (!connected) {
    throw new IllegalStateException("cannot send before connect()");
  }
  if (message.body().length() > maxBodyBytes) {
    throw new IllegalArgumentException(
        "body exceeds " + maxBodyBytes + " bytes: " + message.body().length());
  }
  transport.write(message);
}
```

## 24.7 Throw `UnsupportedOperationException` from an unimplemented operation — never return silently.

> Why? A no-op implementation of a mutator is a lie the caller cannot
> detect: it reports success, the data does not change, and the failure
> surfaces somewhere else entirely. `UnsupportedOperationException` is the
> designated signal, and it is what the JDK's own immutable collections
> throw. **Suggestion.**

```java
// bad — the caller believes the write landed
@Override
public void put(String key, String value) {
  // read-only view; nothing to do
}

// good
@Override
public void put(String key, String value) {
  throw new UnsupportedOperationException("read-only view of " + name);
}
```

## 24.8 Write a custom exception only when callers need to distinguish it programmatically or need data from the failure.

> Why? A custom class earns its keep when a `catch` clause will name it
> specifically, or when it carries fields the handler acts on — an account
> id, a retry-after duration, a validation-failure list. If every handler
> would only read `getMessage()`, the class adds a type to learn and buys
> nothing over `IllegalStateException` with a good message (§24.12).
> **Suggestion.**

```java
// bad — a distinct type whose only content is the message
public final class OrderProcessingException extends RuntimeException {
  public OrderProcessingException(String message) {
    super(message);
  }
}

// good — the type exists because handlers act on its data
public final class RateLimitedException extends RuntimeException {
  private final Duration retryAfter;

  public RateLimitedException(String endpoint, Duration retryAfter) {
    super("rate limited on " + endpoint + ", retry after " + retryAfter);
    this.retryAfter = Objects.requireNonNull(retryAfter, "retryAfter");
  }

  public Duration retryAfter() {
    return retryAfter;
  }
}
```

## 24.9 Throw exceptions appropriate to the abstraction, translating lower-level ones at the boundary.

> Why? Effective Java, 3rd ed., Item 73 ("Throw exceptions appropriate to
> the abstraction") warns that letting an implementation's exception escape
> "pollutes the API of the higher layer with implementation details" and
> can break the API in a later release when the implementation changes. A
> repository that throws `SQLException` has published its storage engine as
> part of its contract; swapping to a document store becomes a breaking
> change for every caller. **Suggestion.**

```java
// bad — the persistence technology leaks into the domain API
public interface CustomerRepository {
  Customer byId(CustomerId id) throws SQLException;
}

// good — the boundary translates; the storage engine stays private
public interface CustomerRepository {
  Customer byId(CustomerId id) throws CustomerLookupException;
}

@Override
public Customer byId(CustomerId id) throws CustomerLookupException {
  try {
    return jdbc.queryForObject(SELECT_BY_ID, MAPPER, id.value());
  } catch (SQLException e) {
    throw new CustomerLookupException("lookup failed for customer " + id, e);
  }
}
```

## 24.10 Always chain the cause when you translate.

> Why? Effective Java, 3rd ed., Item 73 presents exception chaining as the
> mandatory companion to translation: the cause "is eventually passed to a
> superclass constructor such as `Throwable(Throwable)`," and it "allows
> access to the cause programmatically (using `getCause`) and integrates
> the cause's stack trace into that of the higher-level exception." Drop
> the cause and you delete the only frames that identify where the failure
> actually happened — the stack trace now starts at your translation site.
> **Suggestion.**

```java
// bad — the original stack trace is gone; the message is all that survives
try {
  return parse(Files.readString(path));
} catch (IOException e) {
  throw new ConfigLoadException("could not read " + path + ": " + e.getMessage());
}

// good — cause preserved, stack traces concatenated in the log
try {
  return parse(Files.readString(path));
} catch (IOException e) {
  throw new ConfigLoadException("could not read " + path, e);
}
```

## 24.11 Document every exception a method can throw, with `@throws`.

> Why? Effective Java, 3rd ed., Item 74 ("Document all exceptions thrown by
> each method") requires documenting checked *and* unchecked exceptions,
> because an unchecked exception's `@throws` tag is how a caller learns the
> method's preconditions. Google Java Style
> [§7.1.3](https://google.github.io/styleguide/javaguide.html#s7.1.3-javadoc-block-tags)
> fixes the order — "`@param`, `@return`, `@throws`, `@deprecated`" — and
> requires that "these four types never appear with an empty description."
> Item 74 also warns never to declare `throws Exception` on a method that
> can fail in several distinct ways: it erases exactly the information the
> caller needs. **Violation — enforced by `checkstyle/JavadocMethod` with
> `validateThrows` enabled** (it defaults to `false`, so turn it on).
> `checkstyle/IllegalThrows` covers the related declaration case, but note
> its defaults are `Error`, `RuntimeException`, and `Throwable` only — add
> `Exception` to `illegalClassNames` if you want `throws Exception` flagged
> too.

```java
// bad — one opaque declaration, no @throws, callers learn nothing
/** Transfers funds. */
public Receipt transfer(AccountId from, AccountId to, Money amount)
    throws Exception {
  // ...
}

// good — every failure named, with a description of when it happens
/**
 * Moves {@code amount} from one account to another.
 *
 * @param from the debited account, must be open
 * @param to the credited account, must be open
 * @param amount the amount to move, must be positive
 * @return a receipt for the completed transfer
 * @throws IllegalArgumentException if {@code amount} is not positive
 * @throws AccountClosedException if either account is closed
 * @throws InsufficientFundsException if {@code from} cannot cover the amount
 */
public Receipt transfer(AccountId from, AccountId to, Money amount)
    throws AccountClosedException, InsufficientFundsException {
  // ...
}
```

## 24.12 Put the values that caused the failure in the detail message — and nothing sensitive.

> Why? Effective Java, 3rd ed., Item 75 ("Include failure-capture
> information in detail messages") states that "to capture a failure, the
> detail message of an exception should contain the values of all
> parameters and fields that contributed to the exception," because the
> stack trace is often the only artifact an engineer has. The same item is
> equally clear on the limit: do not include passwords, encryption keys,
> and the like, since stack traces are widely visible in logs, bug
> trackers, and support tickets. **Suggestion.**

```java
// bad — nothing actionable, and the token is now in every log aggregator
throw new IllegalArgumentException("bad request");
throw new AuthException("invalid token: " + bearerToken);

// good — the failing values, none of them secret
throw new IndexOutOfBoundsException(
    "index " + index + " out of bounds for length " + length);
throw new AuthException("invalid token for subject " + subjectId + ", kid=" + keyId);
```

## 24.13 Treat the detail message as documentation for humans, never as a parseable API.

> Why? Effective Java, 3rd ed., Item 75 draws the line explicitly: detail
> messages should not be confused with user-level error messages, which
> must be intelligible to end users; and a caller that wants a value from a
> failure should get an accessor, not a string to parse. Parsing
> `getMessage()` breaks the first time anyone rewords the message — which
> nobody will treat as a breaking change, because it isn't one. **Suggestion.**

```java
// bad — a regex against a message nobody promised to keep stable
try {
  return client.send(request);
} catch (RateLimitedException e) {
  Matcher matcher = Pattern.compile("retry after (\\d+)s").matcher(e.getMessage());
  long seconds = matcher.find() ? Long.parseLong(matcher.group(1)) : 60L;
  return scheduler.retryIn(Duration.ofSeconds(seconds));
}

// good — the exception exposes the datum as a field (see §24.8)
try {
  return client.send(request);
} catch (RateLimitedException e) {
  return scheduler.retryIn(e.retryAfter());
}
```

## 24.14 Strive for failure atomicity: validate before mutating, so a failed call leaves the object as it was.

> Why? Effective Java, 3rd ed., Item 76 ("Strive for failure atomicity")
> states that "a failed method invocation should leave the object in the
> state that it was in prior to the invocation," and that the simplest way
> to achieve it is to "check parameters for validity before performing the
> operation." Without it, a caught-and-recovered exception leaves a
> half-mutated object whose next use fails somewhere unrelated — the
> hardest class of bug to trace back. **Suggestion.**

```java
// bad — the size counter is already decremented when the throw happens
public E pop() {
  size--;
  E result = elements[size];
  elements[size] = null;
  return result;  // throws ArrayIndexOutOfBoundsException when empty,
                  // and size is now negative
}

// good — validate first; the object is untouched on the failure path
public E pop() {
  if (size == 0) {
    throw new IllegalStateException("stack is empty");
  }
  E result = elements[--size];
  elements[size] = null;
  return result;
}
```

## 24.15 Never ignore an exception; an empty `catch` needs a comment and a deliberately named variable.

> Why? Effective Java, 3rd ed., Item 77 ("Don't ignore exceptions") calls
> an empty `catch` block a defeat of "the purpose of exceptions, which is
> to force you to handle exceptional conditions." Google Java Style
> [§6.2](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions)
> says the same and adds the escape hatch: "When it truly is appropriate to
> take no action whatsoever in a catch block, the reason this is justified
> is explained in a comment." The `expected` / `ignored` naming convention
> makes the intent visible at the `catch` itself, not three lines down.
> `checkstyle/EmptyCatchBlock` suppresses on either signal, but only the
> comment works out of the box: `commentFormat` defaults to `.*`, while
> `exceptionVariableName` defaults to `^$`, which matches nothing — set it
> to `^(ignored|expected)$` if you want the naming convention to count.
> **Violation — enforced by `checkstyle/EmptyCatchBlock` and Error Prone
> `EmptyCatch`.**

```java
// bad — a real failure disappears without trace
try {
  return Integer.parseInt(raw);
} catch (NumberFormatException e) {
}

// good — either handle it...
try {
  return Integer.parseInt(raw);
} catch (NumberFormatException e) {
  log.warn("unparseable count '{}', defaulting to 0", raw);
  return 0;
}

// ...or justify ignoring it, and name the variable to say so
try {
  Files.deleteIfExists(lockFile);
} catch (IOException ignored) {
  // Best-effort cleanup on shutdown; the lock file is stale either way
  // and the next start reclaims it.
}
```

## 24.16 Never catch `Throwable`, `Error`, or bare `Exception`, and never declare a method as throwing them.

> Why? Checkstyle's own rationale is the clearest statement of the problem:
> "catching `java.lang.Exception`, `java.lang.Error` or
> `java.lang.RuntimeException` is almost never acceptable... this
> unfortunately leads to code that inadvertently catches
> `NullPointerException`, `OutOfMemoryError`, etc." An `OutOfMemoryError`
> or `StackOverflowError` caught by application code turns an unrecoverable
> JVM condition into a corrupted retry loop. On the throwing side, Error
> Prone's `ThrowSpecificExceptions` notes that "base exception classes
> offer no information on the nature of the failure" and force callers to
> "catch unrelated exceptions as well." **Violation — enforced by
> `checkstyle/IllegalCatch` (defaults: `Error`, `Exception`,
> `RuntimeException`, `Throwable`), `checkstyle/IllegalThrows`, and Error
> Prone `ThrowSpecificExceptions`.**

```java
// bad — swallows OutOfMemoryError and every unrelated runtime bug
try {
  return handler.handle(request);
} catch (Throwable t) {
  log.error("request failed", t);
  return Response.serverError();
}

// good — name the failures you can actually handle
try {
  return handler.handle(request);
} catch (IOException | TimeoutException e) {
  log.error("request to {} failed", request.uri(), e);
  return Response.serverError();
}
```

## 24.17 Handle an exception once: log it or rethrow it, never both.

> Why? Logging and rethrowing produces two entries for one failure, at two
> stack depths, with no marker tying them together — which triples the
> volume of an incident's logs while halving their usefulness. The frame
> that *handles* a failure logs it; every frame below only enriches and
> propagates. Error Prone's `CatchAndPrintStackTrace` catches the
> degenerate version of this, where `printStackTrace()` substitutes for
> both handling and logging. See [Chapter 30](30-logging.md) for the
> logging side. **Violation — enforced by Error Prone
> `CatchAndPrintStackTrace` for the `printStackTrace` form.**

```java
// bad — two entries and one exception for a single failure
try {
  return jdbc.queryForObject(SELECT_BY_ID, MAPPER, id.value());
} catch (SQLException e) {
  log.error("query failed", e);
  throw new RepositoryException("query failed", e);
}

// bad — printStackTrace neither handles nor logs properly
try {
  return jdbc.queryForObject(SELECT_BY_ID, MAPPER, id.value());
} catch (SQLException e) {
  e.printStackTrace();
  return null;
}

// good — enrich and propagate; the handler at the top logs once
try {
  return jdbc.queryForObject(SELECT_BY_ID, MAPPER, id.value());
} catch (SQLException e) {
  throw new RepositoryException("lookup failed for customer " + id, e);
}
```

## 24.18 Use `try`-with-resources, and let it record cleanup failures as suppressed exceptions.

> Why? Effective Java, 3rd ed., Item 9 ("Prefer try-with-resources to
> try-finally") shows the failure mode of the manual form: when the body
> and the `close()` both throw, the `finally` block's exception replaces
> the body's, so "the stack trace contains no record of the first
> exception," which is the one that explains the failure.
> `try`-with-resources inverts this — the JDK documents that "the exception
> originating from the try block is propagated and the exception from the
> finally block is added to the list of exceptions suppressed by the
> exception from the try block," retrievable via
> `Throwable.getSuppressed()`. See
> [Chapter 9](09-object-lifecycle-and-resources.md) for resource design.
> **Suggestion.**

```java
// bad — a failing close() erases the real exception from the body
Session session = pool.acquire();
try {
  return session.query(sql);
} finally {
  session.close();
}

// good — the body's exception wins; the close failure rides along
// as a suppressed exception reachable via Throwable.getSuppressed()
try (Session session = pool.acquire()) {
  return session.query(sql);
}
```

## 24.19 Never `return` or `throw` from a `finally` block.

> Why? Error Prone's `Finally` check states the consequence precisely:
> "terminating a finally block abruptly preempts the outcome of the try and
> catch blocks, and will cause the result of any previously executed return
> or throw statements to be ignored." A `return` in `finally` silently
> discards an in-flight exception — the method reports success while the
> real failure vanishes with no trace anywhere. **Violation — enforced by
> Error Prone `Finally`.**

```java
// bad — an exception from parse() is discarded and -1 is returned
try {
  return parse(raw);
} finally {
  if (shouldFallBack) {
    return -1;
  }
}

// good — the fallback is a catch, so the failure is visible and chosen
try {
  return parse(raw);
} catch (ParseException e) {
  log.debug("unparseable input, using fallback", e);
  return -1;
}
```

## 24.20 Don't let a checked exception meet a lambda — translate it at the throw site or keep the loop.

> Why? None of the standard functional interfaces (`Function`, `Supplier`,
> `Consumer`, `Predicate`) declare checked exceptions, so a checked
> exception inside a stream pipeline cannot compile — which pushes people
> into a `catch`-and-wrap block *inside* the lambda that is invisible from
> the pipeline. If a step can genuinely fail in a way the caller must
> handle, an ordinary `for` loop keeps the exception on the method
> signature where it belongs. See [Chapter 18](18-streams.md) for stream
> design. **Suggestion.**

```java
// bad — the wrapping is buried in the lambda and the pipeline's
// signature claims it cannot fail
List<Config> configs =
    paths.stream()
        .map(
            path -> {
              try {
                return parse(Files.readString(path));
              } catch (IOException e) {
                throw new UncheckedIOException(e);
              }
            })
        .toList();

// good — the loop keeps IOException on the method signature
List<Config> load(List<Path> paths) throws IOException {
  List<Config> configs = new ArrayList<>(paths.size());
  for (Path path : paths) {
    configs.add(parse(Files.readString(path)));
  }
  return List.copyOf(configs);
}
```

## 24.21 When you catch `InterruptedException` without rethrowing it, restore the interrupt status.

> Why? Catching `InterruptedException` clears the thread's interrupt flag.
> If you neither rethrow nor call `Thread.currentThread().interrupt()`, the
> cancellation request is destroyed: code higher up the stack that polls
> `Thread.interrupted()` — every well-behaved executor and every blocking
> library call — will never learn that shutdown was requested, and the task
> runs to completion after the pool was asked to stop. **Violation —
> enforced by Error Prone `InterruptedExceptionSwallowed`.**

```java
// bad — the cancellation request is silently destroyed
try {
  queue.take();
} catch (InterruptedException e) {
  log.warn("interrupted while polling");
}

// good — restore the flag so callers can still observe the interrupt
try {
  queue.take();
} catch (InterruptedException e) {
  Thread.currentThread().interrupt();
  log.warn("interrupted while polling, aborting", e);
  return;
}

// also good — declare it and let the caller decide
void drain() throws InterruptedException {
  queue.take();
}
```

## 24.22 Never catch an exception thrown by an assertion or a test failure to keep a loop going.

> Why? A `catch` inside a test's retry or iteration loop swallows
> `AssertionError`, so a failing assertion is reported as a pass. Error
> Prone's `AssertionFailureIgnored` exists specifically because this
> pattern is common and its effect — a permanently green test that verifies
> nothing — is invisible in CI output. See
> [Chapter 31](31-testing.md) for the testing rules this supports.
> **Violation — enforced by Error Prone `AssertionFailureIgnored`.**

```java
// bad — every assertion failure is swallowed; the test can never fail
for (Case testCase : cases) {
  try {
    assertThat(transform(testCase.input())).isEqualTo(testCase.expected());
  } catch (Throwable t) {
    failures.add(t.getMessage());
  }
}

// good — a soft assertion collects failures and still fails the test
SoftAssertions softly = new SoftAssertions();
for (Case testCase : cases) {
  softly.assertThat(transform(testCase.input())).isEqualTo(testCase.expected());
}
softly.assertAll();
```
