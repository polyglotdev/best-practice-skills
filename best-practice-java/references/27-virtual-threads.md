<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 27. Virtual Threads & Structured Concurrency

Virtual threads went final in Java 21 (JEP 444). They do exactly one thing:
they make a thread cheap enough that you can have one per task instead of
one per CPU. Nothing else about Java concurrency changed. A virtual thread
is still a `java.lang.Thread`, still obeys every rule in
[Chapter 26](26-concurrency-fundamentals.md), still needs `volatile` for
visibility, and still deadlocks if you take two locks in two orders. The
mistake this chapter exists to prevent is treating "virtual" as a synonym
for "fast" and sprinkling them over code that was never blocking in the
first place.

The correct mental model is the one Oracle's
[Java 21 core-libraries
guide](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html)
states directly: "virtual threads aren't scarce and therefore should never
be pooled," and "the number of virtual threads is always equal to the number
of concurrent tasks in your application." A virtual thread is a *task*, not
a *worker*. Every rule below follows from that one sentence.

Structured concurrency (`StructuredTaskScope`, JEP 453) is a **preview API
in Java 21**. It is genuinely good and it is genuinely not shippable without
`--enable-preview`, which is not a production flag. §27.18 through §27.21
cover it honestly: what it looks like, why you probably cannot use it yet,
and what to do instead on Java 21. The same caveat applies to scoped values
(JEP 446), which are also preview in 21 — see §27.11.

**Tool alignment:** almost nothing here is mechanically checkable, so nearly
every rule is labeled **Suggestion**. Error Prone's `ThreadPriorityCheck`
(§27.14) and `FutureReturnValueIgnored` (§27.2) cover the only fragments
that are. The diagnostics that matter for this chapter are runtime, not
compile-time: `-Djdk.tracePinnedThreads` and `jcmd Thread.dump_to_file`.

## 27.1 Use virtual threads for thread-per-task code that spends its time blocking on I/O — nothing else.

> Why? A virtual thread's only advantage is that blocking it costs almost
> nothing: when it blocks, the JDK unmounts it from its carrier platform
> thread and the carrier picks up other work. If the task never blocks, that
> advantage never materialises, and you have paid for a mount/unmount
> mechanism to run code that would have been faster on a plain platform
> thread. Virtual threads increase *throughput* under concurrent blocking
> I/O. They do not reduce *latency* of any individual operation, and they do
> not make CPU-bound work faster. **Suggestion.**

```java
// bad — CPU-bound work on virtual threads; no blocking, so nothing is gained
// and the scheduler now has thousands of runnable tasks fighting over N cores
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
  for (Matrix matrix : matrices) {
    executor.execute(matrix::invert);
  }
}

// good — blocking I/O, one virtual thread per in-flight request
List<Callable<HttpResponse<String>>> fetches =
    urls.stream()
        .<Callable<HttpResponse<String>>>map(
            url -> () -> httpClient.send(request(url), BodyHandlers.ofString()))
        .toList();
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
  for (Future<HttpResponse<String>> response : executor.invokeAll(fetches)) {
    record(response.get());
  }
}
```

## 27.2 Create virtual threads with `Executors.newVirtualThreadPerTaskExecutor()`, and scope it with try-with-resources.

> Why? The
> [`Executors`
> javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Executors.html)
> describes this factory as creating "an Executor that starts a new virtual
> `Thread` for each task," with an unbounded thread count — which is the
> point. Because `ExecutorService` extends `AutoCloseable` (Java 19+),
> wrapping it in try-with-resources gives you a lexically scoped fan-out:
> `close()` performs the orderly shutdown and blocks until every submitted
> task has finished, so control cannot leave the block with work still
> running. See [Chapter 9, §9.12](09-object-lifecycle-and-resources.md).
> **Suggestion.**

```java
// bad — threads created by hand; nothing waits for them, nothing collects
// their failures
for (Shipment shipment : shipments) {
  Thread.ofVirtual().start(() -> dispatch(shipment));
}

// good — scoped fan-out that cannot outlive the block; execute() rather than
// a discarded submit(), so a thrown exception reaches the uncaught handler
// (see Chapter 26, §26.14)
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
  for (Shipment shipment : shipments) {
    executor.execute(() -> dispatch(shipment));
  }
}  // close() waits for every task
```

## 27.3 Never pool virtual threads, and never put a virtual-thread factory behind a fixed-size pool.

> Why? Oracle's
> [Java 21 guide](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html)
> is emphatic: "virtual threads aren't scarce and therefore should never be
> pooled!" Pooling exists to amortise the cost of creating an expensive
> resource. A virtual thread is not expensive, so a pool buys nothing — and
> it actively destroys the property you wanted, because a fixed-size pool
> caps concurrency at the pool size no matter how many tasks are blocked on
> I/O. `newFixedThreadPool(200, virtualFactory)` is 200 concurrent requests,
> exactly as if you had used platform threads, with extra indirection.
> **Suggestion.**

```java
// bad — a pool of virtual threads: all of the constraint, none of the benefit
ThreadFactory factory = Thread.ofVirtual().factory();
ExecutorService executor = Executors.newFixedThreadPool(200, factory);

// good — one virtual thread per task, unbounded by construction
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();

// also good — the explicit spelling, when you need a custom factory
ThreadFactory factory = Thread.ofVirtual().name("ingest-", 0).factory();
ExecutorService executor = Executors.newThreadPerTaskExecutor(factory);
```

## 27.4 Limit concurrency against a downstream dependency with a `Semaphore`, not by shrinking the executor.

> Why? Once threads are no longer the scarce resource, the pool size stops
> being a meaningful concurrency limit and starts being an accidental one.
> Express the actual constraint where it lives — "this database accepts 20
> concurrent connections", "this partner API allows 5 requests in flight" —
> with a `Semaphore` around the specific call. Blocking on
> `Semaphore.acquire()` is cheap on a virtual thread, so the waiting tasks
> cost nothing while they queue. This also keeps two different downstreams
> from sharing one artificial limit. **Suggestion.**

```java
// bad — one pool size stands in for every downstream limit at once
private static final ExecutorService POOL = Executors.newFixedThreadPool(20);

// good — the limit is stated where it actually applies
public final class PartnerGateway {
  private static final int MAX_IN_FLIGHT = 5;

  private final Semaphore permits = new Semaphore(MAX_IN_FLIGHT);

  public Quote fetch(String symbol) throws InterruptedException {
    permits.acquire();
    try {
      return partnerClient.quote(symbol);
    } finally {
      permits.release();
    }
  }
}
```

## 27.5 On Java 21, never hold a `synchronized` monitor across a blocking call in a virtual thread — use a `ReentrantLock`.

> Why? This is the one Java 21 footgun that turns a virtual-thread migration
> into an outage. Oracle's
> [guide](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html)
> states that "a virtual thread is pinned in the following situations: the
> virtual thread runs code inside a `synchronized` block or method [or] the
> virtual thread runs a `native` method or a foreign function," and that
> "performing a blocking operation while inside a `synchronized` block or
> method causes the JDK's virtual thread scheduler to block a precious OS
> thread." A pinned virtual thread cannot unmount, so its carrier is held
> hostage for the whole call. With a default parallelism equal to the core
> count, a handful of pinned threads can deadlock the entire application.
> `ReentrantLock` releases the carrier correctly. **Suggestion.**

```java
// bad — the carrier platform thread is pinned for the duration of the RPC
private final Object lock = new Object();

public Response call(Request request) {
  synchronized (lock) {
    return remote.send(request);  // blocking call while pinned
  }
}

// good — ReentrantLock lets the virtual thread unmount while it blocks
private final ReentrantLock lock = new ReentrantLock();

public Response call(Request request) {
  lock.lock();
  try {
    return remote.send(request);
  } finally {
    lock.unlock();
  }
}
```

## 27.6 Diagnose pinning with `-Djdk.tracePinnedThreads` before changing any code.

> Why? Pinning is invisible in ordinary metrics: throughput plateaus, CPU
> sits idle, and nothing throws. Oracle's guide documents the switch that
> makes it visible — "running with the option `-Djdk.tracePinnedThreads=full`
> prints a complete stack trace when a thread blocks while pinned,
> highlighting native frames and frames holding monitors," while
> `-Djdk.tracePinnedThreads=short` "limits the output to just the
> problematic frames." Run this in a load test before you start rewriting
> `synchronized` blocks on suspicion; the culprit is frequently a third-party
> library, not your code. **Suggestion.**

```java
// bad — guessing which synchronized block is the problem and rewriting
// all of them

// good — reproduce under load with the diagnostic enabled, then fix
// exactly what it names
//   java -Djdk.tracePinnedThreads=short -jar app.jar
```

## 27.7 Do not "fix" pinning by raising `jdk.virtualThreadScheduler.parallelism`.

> Why? The scheduler's parallelism defaults to the number of available
> processors and, as
> [dev.java](https://dev.java/learn/new-features/virtual-threads/) puts it,
> "you can tune that count with the `jdk.virtualThreadScheduler.parallelism`
> VM option." Raising it to work around pinning replaces a small pool of
> blocked carriers with a large pool of blocked carriers: you have rebuilt a
> thread pool, badly, and reintroduced exactly the OS-thread scarcity
> virtual threads exist to remove. The knob is for tuning genuine CPU
> parallelism, not for hiding a pinning bug. **Suggestion.**

```java
// bad — masking pinning with more carrier threads
//   java -Djdk.virtualThreadScheduler.parallelism=512 -jar app.jar

// good — remove the pin; the default parallelism is then correct
private final ReentrantLock lock = new ReentrantLock();
```

## 27.8 Treat pinning as a property of the JDK you actually run on, and pin your JDK version in the build.

> Why? The `synchronized` pinning described in §27.5 is a Java 21
> implementation limitation, not a permanent language rule — dev.java scopes
> the statement precisely to "JDK 21, 22, and 23," and later JDKs remove it.
> Two failure modes follow. First, advice found online may describe a JDK
> you are not on. Second, code that is correct on 21 because you replaced
> `synchronized` with `ReentrantLock` stays correct forever, whereas code
> that relies on a newer JDK's behaviour breaks the moment someone builds it
> on 21. Write for the floor, and make the floor explicit. **Suggestion.**

```groovy
// good — the toolchain declares the floor this code was verified against
java {
  toolchain {
    languageVersion.set(JavaLanguageVersion.of(21))
  }
}
```

## 27.9 Use `ForkJoinPool.commonPool()` or a bounded platform pool for CPU-bound parallelism — never virtual threads.

> Why? CPU-bound work is limited by cores, not by threads, so the right
> number of workers is roughly the core count and the right structure is
> work-stealing. Submitting ten thousand CPU-bound tasks to a virtual-thread
> executor creates ten thousand runnable threads that all contend for the
> same cores, adding scheduling overhead and cache thrash for no gain.
> Parallel streams and `ForkJoinPool` are built for this shape;
> `newFixedThreadPool(availableProcessors())` is the explicit form.
> **Suggestion.**

```java
// bad — ten thousand runnable virtual threads on eight cores
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
  for (Image image : images) {
    executor.execute(() -> resample(image));
  }
}

// good — work-stealing on the common ForkJoinPool, one worker per core
List<Image> resampled = images.parallelStream().map(this::resample).toList();

// also good — an explicit, bounded platform pool when you need one
ExecutorService cpuPool =
    Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
```

## 27.10 Never use a `ThreadLocal` as a cache for an expensive object when tasks run on virtual threads.

> Why? The `ThreadLocal`-as-cache idiom only pays off because platform
> threads are pooled and reused, so one expensive object serves thousands of
> tasks. Oracle's guide spells out why it inverts under virtual threads:
> "virtual threads are never pooled and never reused by unrelated tasks…
> every call to `foo` from a different task would trigger the instantiation
> of a new `SimpleDateFormat`," and "because there may be a great many
> virtual threads running concurrently, the expensive object may consume
> quite a lot of memory." A per-request cache with a million requests is a
> million allocations. Use an immutable, shareable object instead. See also
> [Chapter 9, §9.14](09-object-lifecycle-and-resources.md) on removing
> `ThreadLocal` values. No static-analysis check knows whether a
> `ThreadLocal` is being used as a cache or as context, so this one is on the
> reviewer. **Suggestion.**

```java
// bad — one SimpleDateFormat per virtual thread, i.e. per request
private static final ThreadLocal<SimpleDateFormat> FORMAT =
    ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));

String render(Date date) {
  return FORMAT.get().format(date);
}

// good — DateTimeFormatter is immutable, so one instance serves every thread
private static final DateTimeFormatter FORMAT =
    DateTimeFormatter.ISO_LOCAL_DATE.withZone(ZoneOffset.UTC);

String render(Instant instant) {
  return FORMAT.format(instant);
}
```

## 27.11 Do not ship scoped values on Java 21 — they are a preview API. Pass context explicitly, or keep a deliberate `ThreadLocal`.

> Why? `ScopedValue` (JEP 446) is the intended replacement for context-
> carrying `ThreadLocal`s under virtual threads, and Oracle's guide does
> point at it ("consider using the safer and more efficient scoped values").
> But in Java 21 it is a **preview API**: compiling and running it requires
> `--enable-preview`, which ties your artifact to one exact JDK feature
> release and is not a supportable production configuration. Until you are
> on a release where it is final, either pass the context through as a
> parameter — which is clearer anyway — or keep a `ThreadLocal` you set and
> remove in a `finally`. **Suggestion.**

```java
// bad — preview API in production code on Java 21; needs --enable-preview
// and is not binary-compatible across releases
private static final ScopedValue<TenantId> TENANT = ScopedValue.newInstance();

// good — the context is part of the call, visible to every reader
public Invoice render(TenantId tenant, InvoiceId id) {
  return renderer.render(tenant, repository.load(tenant, id));
}

// acceptable — a deliberate ThreadLocal, always cleared
private static final ThreadLocal<TenantId> TENANT = new ThreadLocal<>();

public Invoice render(TenantId tenant, InvoiceId id) {
  TENANT.set(tenant);
  try {
    return renderer.render(repository.load(id));
  } finally {
    TENANT.remove();
  }
}
```

## 27.12 Name virtual threads when you need to identify them — they have no name by default.

> Why? The
> [`Thread`
> javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html)
> states that "virtual threads do not have a thread name by default. The
> `getName` method returns the empty string if a thread name is not set."
> Any log pattern, MDC key, or dashboard that groups by thread name silently
> collapses every virtual thread into one blank bucket. `Thread.Builder`
> gives you `name(String prefix, long start)`, which appends an
> auto-incrementing counter — cheap, and it makes thread dumps readable.
> **Suggestion.**

```java
// bad — every thread in the dump and in the logs has an empty name
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();

// good — named threads, numbered from zero
ThreadFactory factory = Thread.ofVirtual().name("order-worker-", 0).factory();
ExecutorService executor = Executors.newThreadPerTaskExecutor(factory);
```

## 27.13 Capture virtual threads in diagnostics with `jcmd Thread.dump_to_file`, not a legacy thread dump.

> Why? A traditional `jstack`-style dump lists platform threads. With
> thread-per-request virtual threads the interesting state is in the
> hundred thousand virtual threads that dump does not show. Oracle's guide
> documents the replacement: `jcmd <PID> Thread.dump_to_file -format=json
> <file>` "lists all threads, including both platform and virtual threads,"
> though "it doesn't include object addresses, locks, JNI statistics, heap
> statistics, and other information that appears in traditional thread
> dumps." Wire the JSON form into your incident runbook before you need it.
> **Suggestion.**

```java
// bad — only shows carrier platform threads; the blocked work is invisible
//   jstack <pid>

// good — includes every virtual thread, in a machine-readable form
//   jcmd <pid> Thread.dump_to_file -format=json /tmp/threads.json
```

## 27.14 Do not set a priority or clear the daemon flag on a virtual thread.

> Why? Both are silently or loudly ignored, and code that sets them is
> stating an intent the platform will not honour. The `Thread` javadoc is
> explicit: "the priority of a virtual thread is always `NORM_PRIORITY`" and
> `newPriority` "is ignored"; and "the daemon status of a virtual thread is
> always `true` and cannot be changed by this method to `false`" —
> `setDaemon(false)` throws `IllegalArgumentException` on a virtual thread.
> The daemon consequence matters: virtual threads never keep the JVM alive,
> so an executor you forget to close will not block shutdown, and in-flight
> work will simply disappear at exit. That is what §27.2's try-with-resources
> prevents. **Violation — the `setPriority` call is enforced by Error Prone
> `ThreadPriorityCheck` ("Relying on the thread scheduler is discouraged");
> no check covers the `setDaemon` half.**

```java
// bad — one call is a no-op, the other throws IllegalArgumentException
Thread thread = Thread.ofVirtual().unstarted(task);
thread.setPriority(Thread.MAX_PRIORITY);  // ignored
thread.setDaemon(false);                  // IllegalArgumentException

// good — express urgency in the work queue, not in thread metadata, and
// keep the JVM alive by joining the executor rather than by daemon status;
// execute() rather than a discarded submit(), per Chapter 26, §26.14
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
  executor.execute(task);
}
```

## 27.15 Do not branch on `Thread.isVirtual()` in business logic.

> Why? `isVirtual()` is a diagnostic, not a feature flag. Code that behaves
> differently depending on how it was scheduled has two behaviours to test,
> two behaviours to reason about, and a bug the moment someone moves the
> call site. Whatever the branch was protecting — a `ThreadLocal` cache, a
> lock choice, a batch size — should be decided by the code's own
> requirements, and the resulting choice should be correct on both kinds of
> thread. **Suggestion.**

```java
// bad — two code paths, one of which is exercised only in some deployments
if (Thread.currentThread().isVirtual()) {
  return computeWithoutCache();
}
return CACHE.get().compute();

// good — one path that is correct on any thread
return computeWithSharedImmutableCache();
```

## 27.16 Cheap threads are not free capacity — keep the backpressure you already had.

> Why? A virtual thread costs almost nothing to *create*, but each live one
> holds its own stack and everything reachable from it for as long as it
> runs, and — more importantly — every one of them is an in-flight request
> against something downstream. Removing a bounded queue because "threads
> are cheap now" moves the bottleneck from your thread pool, where it was
> visible and bounded, to your database's connection limit, where it
> manifests as cascading timeouts. Accept work at a bounded rate and let the
> queue push back. **Suggestion.**

```java
// bad — unbounded acceptance; the database discovers the limit for you
while (running) {
  Request request = listener.next();
  executor.execute(() -> handle(request));
}

// good — a bounded intake queue provides backpressure at the edge
private final BlockingQueue<Request> intake = new ArrayBlockingQueue<>(10_000);

void accept() {
  while (running) {
    Request request = listener.next();
    if (!intake.offer(request)) {
      reject(request, Status.SERVICE_UNAVAILABLE);
    }
  }
}
```

## 27.17 When adopting virtual threads, change the executor — do not rewrite blocking code as asynchronous.

> Why? The entire value proposition of virtual threads is that ordinary,
> readable, blocking, sequential code becomes scalable without being turned
> inside out. Migrating to virtual threads *and* to a reactive pipeline at
> the same time gets you the debuggability cost of async with none of the
> readability benefit of virtual threads — and a callback chain never blocks,
> so it gains nothing from unmounting either. Pick one model per code path.
> **Suggestion.**

```java
// bad — virtual threads and a callback chain, so neither pays off
CompletableFuture.supplyAsync(() -> loadUser(id), virtualExecutor)
    .thenComposeAsync(user -> loadCartAsync(user), virtualExecutor)
    .thenApplyAsync(this::render, virtualExecutor)
    .join();

// good — plain sequential code, running on a virtual thread
User user = loadUser(id);
Cart cart = loadCart(user);
return render(user, cart);
```

## 27.18 Treat `StructuredTaskScope` as unavailable on Java 21 unless you can accept `--enable-preview` end to end.

> Why? Structured concurrency (JEP 453) is a **preview API in Java 21**. The
> [`StructuredTaskScope`
> javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/StructuredTaskScope.html)
> carries the standard warning: "programs can only use `StructuredTaskScope`
> when preview features are enabled," and "preview features may be removed
> in a future release, or upgraded to permanent features of the Java
> platform." `--enable-preview` must be passed at compile time *and* at run
> time, the resulting class files refuse to load on any other feature
> release, and the API changed shape between Java 19, 20, and 21. That is
> acceptable for a spike and not acceptable for a library or a service you
> intend to upgrade. **Suggestion.**

```kotlin
// bad — a production build that pins itself to exactly one JDK release
tasks.withType<JavaCompile>().configureEach {
  options.compilerArgs.add("--enable-preview")
}
tasks.withType<JavaExec>().configureEach {
  jvmArgs("--enable-preview")
}

// good — no preview flag; use §27.21's supported equivalents on Java 21
```

## 27.19 If you do use `StructuredTaskScope` (preview), open it in try-with-resources and `join()` before reading any `Subtask`.

> Why? The scope's whole guarantee is that a subtask cannot outlive the
> block that forked it, and that guarantee is implemented by `close()` — so
> the scope must be a try-with-resources resource, always. Reading a result
> before `join()` is a programming error the API detects: `Subtask.get()`
> throws `IllegalStateException` if the subtask has not completed, and the
> scope's `ensureOwnerAndJoined()` precondition means the owning thread must
> have joined first. In Java 21, `fork` returns
> `StructuredTaskScope.Subtask<T>`, not a `Future` — that changed from
> earlier previews, which is one more reason §27.18 exists. **Suggestion.**

```java
// bad — result read before join, and the scope is never closed
var scope = new StructuredTaskScope.ShutdownOnFailure();
StructuredTaskScope.Subtask<User> user = scope.fork(() -> loadUser(id));
return user.get();  // IllegalStateException

// good — Java 21 preview; requires --enable-preview
public Page loadPage(UserId id) throws InterruptedException, ExecutionException {
  try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    StructuredTaskScope.Subtask<User> user = scope.fork(() -> loadUser(id));
    StructuredTaskScope.Subtask<Cart> cart = scope.fork(() -> loadCart(id));
    scope.join().throwIfFailed();
    return new Page(user.get(), cart.get());
  }
}
```

## 27.20 Use the built-in `ShutdownOnFailure` and `ShutdownOnSuccess` policies rather than hand-rolling cancellation.

> Why? These two subclasses encode the two shapes almost every fan-out
> needs, and they cancel the remaining subtasks for you.
> `ShutdownOnFailure` captures the first failure and shuts the scope down,
> so `join().throwIfFailed()` gives you all-or-nothing semantics.
> `ShutdownOnSuccess<T>` captures the first success and shuts the scope
> down, so `join().result()` gives you a race between redundant sources.
> Writing that cancellation logic yourself against raw `Future` objects is
> where leaked tasks come from. Both are preview in Java 21 — §27.18
> applies. **Suggestion.**

```java
// bad — a hand-rolled race that leaks the losing calls
List<Future<Quote>> futures = sources.stream()
    .map(source -> executor.submit(() -> source.quote(symbol)))
    .toList();
for (Future<Quote> future : futures) {
  if (future.isDone()) {
    return future.get();  // the other calls keep running forever
  }
}

// good — Java 21 preview; losers are cancelled when the first winner lands
public Quote fastestQuote(String symbol)
    throws InterruptedException, ExecutionException {
  try (var scope = new StructuredTaskScope.ShutdownOnSuccess<Quote>()) {
    for (QuoteSource source : sources) {
      scope.fork(() -> source.quote(symbol));
    }
    return scope.join().result();
  }
}
```

## 27.21 On Java 21 production code, get structured semantics from `invokeAll` and `invokeAny` over a virtual-thread executor.

> Why? You can have most of what structured concurrency offers today, with
> no preview flag. `ExecutorService.invokeAll` submits every task and blocks
> until all of them complete, cancelling any that are unfinished if the
> waiting thread is interrupted. `invokeAny` returns the first successful
> result and cancels the rest, which really is `ShutdownOnSuccess`. Wrap
> either in a try-with-resources virtual-thread executor and the tasks cannot
> outlive the block. Be precise about what you give up, though: unlike
> `ShutdownOnFailure`, `invokeAll` does **not** cancel the siblings when one
> subtask fails — it waits for every task, and you discover the failure at
> `Future.get()`. You get the scope's containment guarantee, not its eager
> cancellation or its error-propagation ergonomics. **Suggestion.**

```java
// bad — futures escape the method; nothing cancels them if the caller gives up
public List<Future<Report>> buildAll(List<Region> regions) {
  return regions.stream().map(region -> executor.submit(() -> build(region))).toList();
}

// good — supported on Java 21; every task completes before close() returns,
// so nothing outlives the block, and the first failure surfaces at get()
public List<Report> buildAll(List<Region> regions)
    throws InterruptedException, ExecutionException {
  List<Callable<Report>> tasks =
      regions.stream().<Callable<Report>>map(region -> () -> build(region)).toList();
  try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Report> reports = new ArrayList<>();
    for (Future<Report> future : executor.invokeAll(tasks)) {
      reports.add(future.get());
    }
    return reports;
  }
}
```

## 27.22 Keep every rule from Chapter 26 — a virtual thread changes the cost of blocking, not the memory model.

> Why? The most expensive misconception about virtual threads is that they
> make shared mutable state safe. They do not. A field written by one
> virtual thread and read by another needs the same happens-before edge it
> always did; a `ConcurrentModificationException` is still a
> `ConcurrentModificationException`; two locks taken in two orders still
> deadlock, and now they deadlock across a hundred thousand threads instead
> of two hundred. Everything in
> [Chapter 26](26-concurrency-fundamentals.md) applies verbatim — with
> §26.7 (never block while holding a lock) upgraded from a performance
> concern to a correctness-adjacent one by §27.5. **Suggestion.**

```java
// bad — "it's on a virtual thread, so it's isolated" is not a thing
private int processed;  // written by every task, read by the reporter

// good — the same discipline as any other thread
private final LongAdder processed = new LongAdder();
```
