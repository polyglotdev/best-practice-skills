<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 9. Object Lifecycle & Resources

Java gives you automatic memory management and nothing else. File descriptors,
sockets, database connections, native memory, thread pools, and `ThreadLocal`
entries are all released by *your* code, on a schedule *you* choose, or they are
not released at all. This chapter is about that half of the lifecycle: acquiring
a resource, guaranteeing its release, implementing `AutoCloseable` so that
guarantee actually holds, and recognising the specific shapes of leak that
garbage collection cannot save you from.

The rules draw on **Effective Java, 3rd Edition, Items 7–9** (eliminate obsolete
object references; avoid finalizers and cleaners; prefer `try`-with-resources to
`try`-`finally`), the JDK 21 API contracts for
[`AutoCloseable`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/AutoCloseable.html),
[`Closeable`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/Closeable.html),
and [`Cleaner`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/ref/Cleaner.html),
and [Google Java Style §6.4](https://google.github.io/styleguide/javaguide.html#s6.4-finalizers)
on finalizers.

Two things are deliberately deferred. **Constructing** the object in the first
place — factories, builders, validation, defensive copying — is
[Chapter 8](08-object-creation.md), and §8.16 states the finalizer prohibition
this chapter elaborates. **Exception design** — what to throw, when to wrap,
and the rule against swallowing — is [Chapter 24](24-exceptions.md); this
chapter covers only the exception mechanics that are specific to `close`.
Virtual-thread-aware executor lifecycles are in
[Chapter 27](27-virtual-threads.md).

**Tool alignment:** Error Prone's `Finalize`, `EmptyCatch`,
`MustBeClosedChecker`, `ThreadLocalUsage`, and `Finally` fire at compile time;
Checkstyle's `NoFinalizer`, `EmptyCatchBlock`, `IllegalCatch`, and
`UnnecessarySemicolonInTryWithResources` fire in the same build. Rules a named
check actually enforces are marked **Violation**; the rest are **Suggestion**,
even where a related check covers an adjacent symptom.

## 9.1 Use `try`-with-resources, never `try`-`finally`, to close a resource.

> Why? Effective Java, 3rd ed., Item 9: "Prefer try-with-resources to
> try-finally." The `finally` form is not merely verbose — it is wrong in a way
> that is easy to miss. If the body throws and `close()` also throws, the
> exception from `close()` replaces the one from the body, and the *actual*
> failure disappears from the stack trace entirely. `try`-with-resources inverts
> this: the body's exception propagates and the `close()` exception is attached
> as suppressed. **Suggestion.**

```java
// bad — a failure in close() erases the real failure from read()
static String firstLineOf(Path path) throws IOException {
  BufferedReader reader = Files.newBufferedReader(path);
  try {
    return reader.readLine();
  } finally {
    reader.close();
  }
}

// good — read()'s exception wins; close()'s is suppressed, not lost
static String firstLineOf(Path path) throws IOException {
  try (BufferedReader reader = Files.newBufferedReader(path)) {
    return reader.readLine();
  }
}
```

## 9.2 Declare multiple resources in a single `try`-with-resources header rather than nesting `try` blocks.

> Why? The resource list closes in reverse declaration order, which is exactly
> the ordering nested `try` blocks give you, without the indentation or the risk
> of an outer resource being acquired and then abandoned when the inner
> acquisition throws. Note that the JLS *permits* a trailing semicolon after the
> last resource — `ResourceSpecification` is `( {Resource} {Semicolon} )`, so
> `try (a; b;)` compiles — but it carries no meaning and Checkstyle flags it.
> **Suggestion** for the rule itself; a stray trailing semicolon is a
> **Violation — enforced by
> `checkstyle/UnnecessarySemicolonInTryWithResources`.**

```java
// bad — three levels of nesting for what is one operation
static void copy(Path src, Path dst) throws IOException {
  try (InputStream in = Files.newInputStream(src)) {
    try (OutputStream out = Files.newOutputStream(dst)) {
      in.transferTo(out);
    }
  }
}

// good — one header; `out` closes first, then `in`
static void copy(Path src, Path dst) throws IOException {
  try (InputStream in = Files.newInputStream(src);
      OutputStream out = Files.newOutputStream(dst)) {
    in.transferTo(out);
  }
}
```

## 9.3 When you catch an exception from a `try`-with-resources block, read `getSuppressed()` before deciding the cause.

> Why? The suppressed-exception mechanism only helps if something looks at it.
> `Throwable.getSuppressed()` returns the array of exceptions thrown by `close()`
> while the primary exception was propagating; if your logging or diagnostics
> path prints only `getMessage()`, those are invisible. Logging the throwable
> itself (SLF4J's trailing-throwable form, see [Chapter 30](30-logging.md)) prints
> the suppressed chain automatically. **Suggestion.**

```java
// bad — the message alone hides both the cause chain and the suppressed close failure
try (Connection connection = dataSource.getConnection()) {
  return query(connection);
} catch (SQLException e) {
  log.error("query failed: " + e.getMessage());
  throw new DataAccessException("query failed", e);
}

// good — surface each suppressed close failure, and pass the throwable itself
// so the logger prints the cause chain
try (Connection connection = dataSource.getConnection()) {
  return query(connection);
} catch (SQLException e) {
  for (Throwable suppressed : e.getSuppressed()) {
    log.warn("suppressed while closing connection", suppressed);
  }
  throw new DataAccessException("query failed", e);
}
```

## 9.4 Use the effectively-final resource form when the resource already exists; do not re-declare it.

> Why? Since Java 9, `try`-with-resources accepts an existing final or
> effectively final variable. Re-declaring it as `try (Foo ignored = foo)`
> introduces a second name for the same object, which readers must check for
> aliasing, and which some static analysis reads as an unused variable.
> **Suggestion.**

```java
// bad — a pointless alias whose only purpose is to satisfy the old syntax
void process(Session session) {
  try (Session ignored = session) {
    session.run();
  }
}

// good — Java 9+ accepts the effectively final variable directly
void process(Session session) {
  try (session) {
    session.run();
  }
}
```

## 9.5 Implement `AutoCloseable` for a general resource; implement `Closeable` only when `close()` throws `IOException` and is genuinely idempotent.

> Why? The two interfaces make different promises. The JDK 21 `AutoCloseable`
> docs state that its `close` "is *not* required to be idempotent … unlike
> `Closeable.close` which is required to have no effect if called more than
> once", and `Closeable` narrows the throws clause to `IOException`. Declaring
> `Closeable` on a type whose `close` is not idempotent, or whose failure mode is
> not an I/O failure, breaks a contract callers are entitled to rely on — and
> `Closeable` extends `AutoCloseable`, so you gain nothing by picking the wrong
> one. **Suggestion.**

```java
// bad — Closeable promises idempotency this class does not provide, and the
// failure mode is not an I/O failure at all
public final class LeaseHandle implements Closeable {
  @Override
  public void close() throws IOException {
    coordinator.release(leaseId); // second call throws IllegalStateException
  }
}

// good — AutoCloseable with a domain-appropriate, narrowed throws clause
public final class LeaseHandle implements AutoCloseable {
  @Override
  public void close() throws LeaseException {
    coordinator.release(leaseId);
  }
}
```

## 9.6 Narrow `close()`'s `throws` clause to the most specific type possible, and to nothing at all when closing cannot fail.

> Why? The JDK 21 `AutoCloseable` docs are explicit: "implementers are *strongly*
> encouraged to declare concrete implementations of the `close` method to throw
> more specific exceptions, or to throw no exception at all if the close
> operation cannot fail." Inheriting `throws Exception` forces every
> `try`-with-resources user of your type to catch or declare `Exception`, which
> in turn swallows every unrelated checked exception in the block. That is a
> whole-codebase cost imposed by one lazy signature.
> **Suggestion** — nothing flags an over-broad `throws` clause at its
> declaration; `checkstyle/IllegalCatch` only catches the downstream symptom, a
> `catch (Exception e)` at the call site.

```java
// bad — every caller is now forced into `catch (Exception e)`
public final class MetricsScope implements AutoCloseable {
  @Override
  public void close() throws Exception {
    reporter.flush();
  }
}

// good — close cannot fail, so it declares nothing
public final class MetricsScope implements AutoCloseable {
  @Override
  public void close() {
    reporter.flush();
  }
}
```

## 9.7 Make `close()` idempotent.

> Why? A resource can be closed by `try`-with-resources, by an explicit call in
> a shutdown hook, and by a wrapper that owns it — and you cannot always prove
> only one of those runs. The JDK 21 `AutoCloseable` docs "strongly encourage"
> idempotency for exactly this reason. A `close()` that throws or double-releases
> on the second call turns a benign redundancy into a crash, often on the error
> path where you can least afford it. **Suggestion.**

```java
// bad — the second close double-releases the native handle
public final class NativeBuffer implements AutoCloseable {
  private long address;

  @Override
  public void close() {
    free(address);
  }
}

// good — guarded, so any number of calls is safe
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

## 9.8 Never let `close()` throw `InterruptedException`.

> Why? The JDK 21 `AutoCloseable` docs single this out: "Implementers of this
> interface are also strongly advised to not have the `close` method throw
> `InterruptedException`. This exception interacts with a thread's interrupted
> status, and runtime misbehavior is likely to occur if an `InterruptedException`
> is suppressed." A suppressed `InterruptedException` means the interrupt was
> consumed and the flag was cleared, and nothing in the calling code will ever
> learn the thread was asked to stop. Restore the interrupt status inside `close`
> instead. **Suggestion.**

```java
// bad — if the body also threw, this InterruptedException is suppressed and the
// interrupt is silently lost
public final class Pipeline implements AutoCloseable {
  @Override
  public void close() throws InterruptedException {
    worker.join();
  }
}

// good — handle the interrupt inside close and re-assert the flag
public final class Pipeline implements AutoCloseable {
  @Override
  public void close() {
    try {
      worker.join();
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
    }
  }
}
```

## 9.9 Close only the resources you opened; never close one the caller handed you.

> Why? Ownership is the single most common source of "stream closed" bugs.
> Wrapping a caller's `InputStream` in your own decorator and putting the
> decorator in a `try`-with-resources closes the caller's stream too, because
> decorator `close()` cascades. The caller then hits `IOException: Stream closed`
> in code that looks completely unrelated. If you did not open it, you do not
> close it — and if you *do* take ownership, say so in the Javadoc.
> **Suggestion.**

```java
// bad — closing the reader cascades into the caller's InputStream
public List<Record> parse(InputStream in) throws IOException {
  try (BufferedReader reader = new BufferedReader(new InputStreamReader(in, UTF_8))) {
    return reader.lines().map(Record::parse).toList();
  }
}

// good — the caller keeps ownership of `in`; we own nothing that needs closing
public List<Record> parse(InputStream in) throws IOException {
  BufferedReader reader = new BufferedReader(new InputStreamReader(in, UTF_8));
  return reader.lines().map(Record::parse).toList();
}

// good — we open it, so we close it, and the signature says we own the Path
public List<Record> parse(Path path) throws IOException {
  try (BufferedReader reader = Files.newBufferedReader(path, UTF_8)) {
    return reader.lines().map(Record::parse).toList();
  }
}
```

## 9.10 Document ownership transfer in Javadoc whenever a method takes or returns a resource.

> Why? Ownership is not expressible in the type system, so it has to be
> expressible in prose. A method that returns an `AutoCloseable` is handing the
> caller a release obligation; a method that accepts one may or may not be taking
> that obligation on. Without a sentence saying which, every caller guesses, and
> half of them guess wrong. Google Java Style
> [§7.3](https://google.github.io/styleguide/javaguide.html#s7.3-javadoc-where-required)
> already requires Javadoc on every public class and every public or protected
> member of one — this is what belongs in it. **Suggestion.**

```java
// bad — does the caller close this? does openSession close it on failure?
public Session openSession(Connection connection) { ... }

// good
/**
 * Opens a session over {@code connection}.
 *
 * <p>The returned session takes ownership of {@code connection} and closes it
 * when the session is closed; callers must not close {@code connection}
 * themselves.
 *
 * @param connection an open connection, ownership of which transfers to the result
 * @return a new session that the caller is responsible for closing
 */
public Session openSession(Connection connection) { ... }
```

## 9.11 Close every stream that is backed by an I/O resource.

> Why? Most `Stream` pipelines need no closing, but `Files.lines`,
> `Files.list`, `Files.walk`, and `Files.find` return streams that hold an open
> file handle or directory handle. Their Javadoc says so, and their handles leak
> until GC if the stream is not closed. `Stream` extends `AutoCloseable` (via
> `BaseStream`) precisely so these can go in a `try`-with-resources header.
> **Suggestion** — the JDK does not annotate `Files.walk` and friends, so no
> check fires on the example below. If you write your own resource-returning
> factory, annotating it `@MustBeClosed` *does* make an unclosed call a
> **Violation — enforced by `error-prone/MustBeClosedChecker`**, which reports
> that the method "returns a resource which must be managed carefully".

```java
// bad — the directory handle stays open until the next GC, if ever
long javaFileCount(Path root) throws IOException {
  return Files.walk(root).filter(p -> p.toString().endsWith(".java")).count();
}

// good
long javaFileCount(Path root) throws IOException {
  try (Stream<Path> paths = Files.walk(root)) {
    return paths.filter(p -> p.toString().endsWith(".java")).count();
  }
}
```

## 9.12 Put an `ExecutorService` in a `try`-with-resources block when its lifetime is scoped to a method.

> Why? `ExecutorService` has extended `AutoCloseable` since Java 19, and its
> `close()` "initiates an orderly shutdown … and waits until all tasks have
> completed execution and the executor has terminated." An executor that is never
> shut down keeps its non-daemon platform threads alive, which keeps the JVM
> alive — a classic "my CLI hangs after printing the answer" bug. This is
> especially natural with `Executors.newVirtualThreadPerTaskExecutor()`; see
> [Chapter 27](27-virtual-threads.md). **Suggestion.**

```java
// bad — the pool's threads keep the JVM from exiting
List<Report> runAll(List<Query> queries) throws Exception {
  ExecutorService executor = Executors.newFixedThreadPool(8);
  List<Future<Report>> futures = executor.invokeAll(queries.stream().map(Query::asTask).toList());
  return collect(futures);
}

// good — close() shuts down and waits for termination
List<Report> runAll(List<Query> queries) throws Exception {
  try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<Report>> futures =
        executor.invokeAll(queries.stream().map(Query::asTask).toList());
    return collect(futures);
  }
}
```

## 9.13 Null out obsolete references in any class that manages its own storage.

> Why? Effective Java, 3rd ed., Item 7: "Eliminate obsolete object references."
> The canonical case is a stack backed by an array — after `pop()` decrements the
> size, `elements[size]` still points at the popped object, so the GC cannot
> reclaim it, nor anything it transitively references. Bloch's rule is narrow on
> purpose: "Nulling out object references should be the exception rather than the
> norm." Do it only where your class, rather than the JVM, owns the array or
> table. **Suggestion.**

```java
// bad — the popped element stays reachable through the backing array forever
public Object pop() {
  if (size == 0) {
    throw new EmptyStackException();
  }
  return elements[--size];
}

// good
public Object pop() {
  if (size == 0) {
    throw new EmptyStackException();
  }
  Object result = elements[--size];
  elements[size] = null; // let the GC reclaim it
  return result;
}
```

## 9.14 Remove every `ThreadLocal` value in a `finally` block.

> Why? `ThreadLocal` entries are keyed by thread, and application servers,
> connection pools, and `ForkJoinPool` all reuse threads indefinitely. A value
> that is set and never removed lives as long as the thread does — which leaks
> memory, and worse, leaks *data*: the next request served by that thread sees
> the previous request's tenant id, user, or trace context. In a container the
> retained value can also pin an entire web application classloader after
> redeploy. No tool can prove you called `remove()`, so that half is a
> **Suggestion**; the storage half is a **Violation — a `ThreadLocal` held in a
> non-`static` field is enforced by `error-prone/ThreadLocalUsage`**, whose
> rationale is the same leak ("there will be `M * N` instances of the
> `ThreadLocal` value").

```java
// bad — on a pooled thread, the next request inherits this tenant
public final class TenantContext {
  private static final ThreadLocal<TenantId> CURRENT = new ThreadLocal<>();

  public static void run(TenantId tenant, Runnable body) {
    CURRENT.set(tenant);
    body.run();
  }
}

// good
public final class TenantContext {
  private static final ThreadLocal<TenantId> CURRENT = new ThreadLocal<>();

  private TenantContext() {
    throw new AssertionError("no instances");
  }

  public static void run(TenantId tenant, Runnable body) {
    CURRENT.set(tenant);
    try {
      body.run();
    } finally {
      CURRENT.remove();
    }
  }
}
```

## 9.15 Use a `Cleaner` only as a safety net behind an explicit `close()`, and keep its state in a `static` nested class.

> Why? Effective Java, 3rd ed., Item 8 permits exactly two uses for a cleaner:
> "as a safety net" for a caller who forgot to `close()`, and for native peers
> whose resources are not critical. It is never the primary mechanism, because
> the JVM never promises to run it. The implementation detail that catches people
> out is in the JDK 21 `Cleaner` docs: "the cleaning action must not refer to the
> object being registered. If so, the object will not become phantom reachable
> and the cleaning action will not be invoked automatically." A lambda that
> touches a field of the enclosing instance captures `this`, so it guarantees the
> cleaner never fires. **Suggestion.**

```java
// bad — the lambda captures `this`, so the object is never phantom reachable
// and the cleaner never runs; there is also no explicit close for callers
public final class NativeBuffer {
  private static final Cleaner CLEANER = Cleaner.create();
  private final long address;

  public NativeBuffer(long size) {
    this.address = allocate(size);
    CLEANER.register(this, () -> free(this.address)); // captures `this`
  }
}

// good — explicit close is the primary path; the cleaner is the net; state lives
// in a static nested class that holds no reference to the outer instance
public final class NativeBuffer implements AutoCloseable {
  private static final Cleaner CLEANER = Cleaner.create();

  private final State state;
  private final Cleaner.Cleanable cleanable;

  public NativeBuffer(long size) {
    this.state = new State(allocate(size));
    this.cleanable = CLEANER.register(this, state);
  }

  @Override
  public void close() {
    cleanable.clean(); // idempotent: Cleanable.clean runs the action at most once
  }

  private static final class State implements Runnable {
    private long address;

    State(long address) {
      this.address = address;
    }

    @Override
    public void run() {
      if (address != 0L) {
        free(address);
        address = 0L;
      }
    }
  }
}
```

## 9.16 Never swallow an exception thrown by `close()`; log it or attach it, and say why if you truly do nothing.

> Why?
> [Google Java Style §6.2](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions)
> states that "it is very rarely correct to do nothing in response to a caught
> exception", and that where no action is taken "the reason this is justified is
> explained in a comment". A failed `close()` on a write path means data may not
> have reached the disk or the socket — reporting success after swallowing it is
> a correctness bug, not a tidiness one.
> **Violation — enforced by `checkstyle/EmptyCatchBlock` and
> `error-prone/EmptyCatch`.**

```java
// bad — a failed flush-on-close means the bytes never landed, and nobody knows
try {
  writer.close();
} catch (IOException e) {
}

// good — either propagate…
try (Writer writer = Files.newBufferedWriter(path, UTF_8)) {
  writer.write(payload);
}

// good — …or, when the resource is read-only and the failure is genuinely
// immaterial, say so explicitly
try {
  reader.close();
} catch (IOException e) {
  // Read-only stream already fully consumed; a close failure cannot affect the
  // result and there is no recovery action available.
  log.debug("ignoring close failure on read-only stream", e);
}
```

## 9.17 Never `return` from a `finally` block, and never throw from one.

> Why? A `return` or `throw` in `finally` discards any exception propagating out
> of the `try` block — including the one that told you the operation failed. The
> method reports success while the work did not happen. This is the same failure
> mode as §9.1, and it is the reason `try`-with-resources exists.
> **Violation — enforced by `error-prone/Finally`.**

```java
// bad — an IOException from write() is discarded and the method returns true
boolean save(Path path, String payload) throws IOException {
  try {
    Files.writeString(path, payload, UTF_8);
    return true;
  } finally {
    return true; // swallows everything
  }
}

// good
boolean save(Path path, String payload) {
  try {
    Files.writeString(path, payload, UTF_8);
    return true;
  } catch (IOException e) {
    log.warn("could not save path={}", path, e);
    return false;
  }
}
```

## 9.18 Make a class `final`, or make it immune to finalizer attacks, before you let it be subclassed.

> Why? A non-final class whose constructor can throw is vulnerable to the
> finalizer attack: an attacker subclasses it, overrides `finalize()`, and
> triggers a constructor failure. The partially constructed object still becomes
> eligible for finalization, so the malicious `finalize()` runs and captures a
> reference to an object that failed its own invariant checks. Effective Java,
> 3rd ed., Item 8 gives the two defences: make the class `final`, or declare a
> `final` no-op `finalize()` that a subclass cannot override. Since Java 21 the
> cheapest correct answer is almost always "make it `final`", or make the
> hierarchy [`sealed`](13-sealed-types.md).
> **Suggestion** — no check can tell that a subclassable class *should* have
> been final. `checkstyle/FinalClass` sounds like it does, but it only flags a
> class whose constructors are all private, which is not the case here. The
> other half is mechanical: declaring `finalize()` at all is a **Violation —
> enforced by `checkstyle/NoFinalizer` and `error-prone/Finalize`**, so the
> "`final` no-op `finalize()`" defence must be an explicit suppression if you
> use it.

```java
// bad — subclassable, constructor can throw, no defence
public class AccountToken {
  private final byte[] secret;

  public AccountToken(byte[] secret) {
    if (secret.length != 32) {
      throw new IllegalArgumentException("secret must be 32 bytes, was " + secret.length);
    }
    this.secret = secret.clone();
  }
}

// good — final class; no subclass, so no finalizer to attack with
public final class AccountToken {
  private final byte[] secret;

  public AccountToken(byte[] secret) {
    if (secret.length != 32) {
      throw new IllegalArgumentException("secret must be 32 bytes, was " + secret.length);
    }
    this.secret = secret.clone();
  }
}
```
