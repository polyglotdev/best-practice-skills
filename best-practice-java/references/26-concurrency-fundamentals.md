<!-- Part of the `best-practice-java` skill. See SKILL.md for the index. -->

# 26. Concurrency Fundamentals

Almost every concurrency bug that reaches production is a *visibility* bug
wearing an atomicity bug's clothes. Two threads read the same field, one
writes it, and the reader keeps seeing the old value forever — not because
the write was lost, but because nothing in the program established a
happens-before edge between the write and the read. The code looks obviously
correct, passes every test on a laptop, and hangs on a server under load.
This chapter is about the discipline that makes such code actually correct:
what has to be synchronized, what may not be done while holding a lock, and
which higher-level abstraction to reach for instead of writing lock code at
all.

The rules here come almost entirely from Effective Java, 3rd ed., Chapter 11
(Items 78–84), and from the `java.util.concurrent` API contracts in the
[JDK 21 API documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/package-summary.html).
Google's Java Style Guide contributes one directly relevant normative rule,
[§6.2 Caught exceptions: not ignored](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions),
which §26.25 applies to `InterruptedException`.

Three neighbouring topics live elsewhere. **Virtual threads**, which change
the economics of "one thread per task" but change none of the memory-model
rules in this chapter, are [Chapter 27](27-virtual-threads.md) — every rule
below applies unchanged to a virtual thread, and §26.7 in particular becomes
sharper there. The mechanics of closing an `ExecutorService` in
`try`-with-resources belong to
[Chapter 9, §9.12](09-object-lifecycle-and-resources.md); §26.13 here covers
only the shutdown *protocol*. And the exception-handling rules that §26.14
and §26.25 lean on are in [Chapter 24](24-exceptions.md).

**Tool alignment:** Error Prone catches a large share of this chapter
mechanically — `NonAtomicVolatileUpdate`, `SynchronizeOnNonFinalField`,
`GuardedBy`, `StaticGuardedByInstance`, `DoubleCheckedLocking`,
`WaitNotInLoop`, `LockNotBeforeTry`, `ThreadJoinLoop`,
`UnsynchronizedOverridesSynchronized`, `FutureReturnValueIgnored`,
`ThreadPriorityCheck`, and `InterruptedExceptionSwallowed` — backed by
Checkstyle's `EmptyCatchBlock`. Design rules no tool can judge, such as "is
this the right lock granularity?", are labeled **Suggestion**.

## 26.1 Synchronize every access to shared mutable data — on the read side as well as the write side.

> Why? Effective Java, 3rd ed., Item 78 ("Synchronize access to shared
> mutable data") makes the point that most programmers get wrong:
> synchronization is not only about mutual exclusion, it is also about
> *visibility*. A `boolean` write is already atomic under the Java Memory
> Model, so the loop below never sees a torn value — it sees no value at
> all. Without a happens-before edge the JIT is free to hoist the field read
> out of the loop, turning `while (!stopped)` into `if (!stopped) while
> (true) {}`. The program hangs forever, and it hangs only under
> optimisation, which is why it passes in a debugger. **Suggestion.**

```java
// bad — the write is atomic but invisible; requestStop() never stops anything
public final class Poller {
  private boolean stopped = false;

  public void run() {
    long i = 0;
    while (!stopped) {
      i++;
    }
  }

  public void requestStop() {
    stopped = true;
  }
}

// good — volatile establishes a happens-before edge on every read and write
public final class Poller {
  private volatile boolean stopped = false;

  public void run() {
    long i = 0;
    while (!stopped) {
      i++;
    }
  }

  public void requestStop() {
    stopped = true;
  }
}
```

## 26.2 Use `volatile` only when a write depends on nothing that was read; use an atomic class the moment it does.

> Why? Effective Java, 3rd ed., Item 78 shows the trap directly: `volatile`
> gives communication, not mutual exclusion, so `nextSerial++` on a
> `volatile` field is still a read-modify-write with a race in the middle.
> Two threads can read the same value, each increment it, and both write the
> same result — the classic "safety failure" where the method silently
> returns a duplicate serial number. Error Prone flags exactly this shape.
> **Violation — enforced by Error Prone `NonAtomicVolatileUpdate`.**

```java
// bad — ++ is read-modify-write; volatile does not make it atomic
private static volatile long nextSerialNumber = 0;

public static long generateSerialNumber() {
  return nextSerialNumber++;
}

// good — the atomic class performs the whole operation as one step
private static final AtomicLong nextSerialNumber = new AtomicLong();

public static long generateSerialNumber() {
  return nextSerialNumber.getAndIncrement();
}
```

## 26.3 Prefer an atomic class or `LongAdder` to a `synchronized` counter.

> Why? Effective Java, 3rd ed., Item 79 ("Avoid excessive synchronization")
> and Item 81 both push toward `java.util.concurrent.atomic`: a
> compare-and-swap counter has no lock to contend on, no monitor to inflate,
> and no possibility of a deadlock. Under heavy write contention prefer
> [`LongAdder`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/atomic/LongAdder.html),
> which spreads updates across internal cells and only reconciles them in
> `sum()` — its javadoc states it is "usually preferable to `AtomicLong`
> when multiple threads update a common sum that is used for purposes such
> as collecting statistics." **Suggestion.**

```java
// bad — every increment takes a monitor, and reads must take it too
public final class RequestCounter {
  private long count;

  public synchronized void record() {
    count++;
  }

  public synchronized long count() {
    return count;
  }
}

// good — lock-free, and LongAdder scales under write contention
public final class RequestCounter {
  private final LongAdder count = new LongAdder();

  public void record() {
    count.increment();
  }

  public long count() {
    return count.sum();
  }
}
```

## 26.4 Prefer confining mutable state to one thread, or making it immutable, to synchronizing shared access.

> Why? Effective Java, 3rd ed., Item 78 closes with the strongest available
> advice: "the best way to avoid the problems associated with concurrency is
> not to share mutable data." Immutable objects and thread-confined objects
> need no synchronization at all, which means they cannot deadlock, cannot
> livelock, and cannot exhibit a visibility bug. Every lock you do not take
> is a lock you cannot get wrong. See
> [Chapter 12](12-records.md) for the record idiom that makes immutability
> the default. **Suggestion.**

```java
// bad — a shared, mutable accumulator guarded by ad-hoc synchronization
public final class Aggregator {
  private final List<Reading> readings = new ArrayList<>();

  public synchronized void add(Reading reading) {
    readings.add(reading);
  }

  public synchronized Summary summarize() {
    return Summary.of(readings);
  }
}

// good — each task builds its own immutable result; nothing is shared
public record Summary(long count, double total) {
  public static Summary of(List<Reading> readings) {
    return new Summary(
        readings.size(), readings.stream().mapToDouble(Reading::value).sum());
  }

  public Summary merge(Summary other) {
    return new Summary(count + other.count, total + other.total);
  }
}
```

## 26.5 Never let a reference to a partially constructed object escape its constructor.

> Why? Until a constructor returns, the object's `final` fields are not
> guaranteed to be visible to other threads, and its non-final fields may
> hold defaults. Registering `this` with a listener, starting a thread that
> captures `this`, or storing `this` in a static registry from inside the
> constructor publishes an object another thread can observe half-built —
> reading `null` from a field the constructor already assigned. Publish from
> a static factory after construction completes instead. See
> [Chapter 8](08-object-creation.md) for the factory idiom. **Suggestion.**

```java
// bad — the listener can be invoked before the constructor finishes
public final class PriceWatcher implements PriceListener {
  private final Threshold threshold;

  public PriceWatcher(EventBus bus, Threshold threshold) {
    bus.register(this);  // `this` escapes; threshold may still be null
    this.threshold = threshold;
  }

  @Override
  public void onPrice(Price price) {
    if (threshold.exceededBy(price)) {
      alert(price);
    }
  }
}

// good — fully construct, then publish
public final class PriceWatcher implements PriceListener {
  private final Threshold threshold;

  private PriceWatcher(Threshold threshold) {
    this.threshold = threshold;
  }

  public static PriceWatcher register(EventBus bus, Threshold threshold) {
    PriceWatcher watcher = new PriceWatcher(threshold);
    bus.register(watcher);
    return watcher;
  }

  @Override
  public void onPrice(Price price) {
    if (threshold.exceededBy(price)) {
      alert(price);
    }
  }
}
```

## 26.6 Never call an alien method from inside a `synchronized` block.

> Why? Effective Java, 3rd ed., Item 79 is unambiguous: "never cede control
> to the client within a synchronized method or block." A method you do not
> control — a listener callback, an overridable method, a `Function` passed
> in by the caller — can do anything, including calling back into your
> object (`ConcurrentModificationException` while you iterate), taking
> another lock in the opposite order (deadlock), or blocking indefinitely
> while holding yours. Take a snapshot outside the lock, or use
> `CopyOnWriteArrayList`, whose snapshot iterator makes the copy for you.
> **Suggestion.**

```java
// bad — the observer runs while the lock is held; it can re-enter or deadlock
public void notifyElementAdded(E element) {
  synchronized (observers) {
    for (SetObserver<E> observer : observers) {
      observer.added(this, element);  // alien method, holding the lock
    }
  }
}

// good — copy under the lock, invoke outside it
public void notifyElementAdded(E element) {
  List<SetObserver<E>> snapshot;
  synchronized (observers) {
    snapshot = List.copyOf(observers);
  }
  for (SetObserver<E> observer : snapshot) {
    observer.added(this, element);
  }
}
```

## 26.7 Do as little as possible inside a `synchronized` block — never blocking I/O, never a sleep, never an unbounded wait.

> Why? Effective Java, 3rd ed., Item 79 frames the cost correctly: the real
> price of over-synchronization is not the monitor itself, it is "the lost
> opportunities for parallelism" plus the delays imposed by memory-model
> consistency. A lock held across a network call serializes every thread in
> the system behind the slowest remote peer. On a virtual thread this is
> worse still, because a `synchronized` block pins the carrier platform
> thread for the whole blocking call — see
> [Chapter 27, §27.5](27-virtual-threads.md). **Suggestion.**

```java
// bad — the HTTP call runs with the lock held; every other thread waits on it
public synchronized Rate refresh(String symbol) {
  Rate rate = httpClient.fetchRate(symbol);  // blocking I/O under the lock
  cache.put(symbol, rate);
  return rate;
}

// good — fetch outside the lock; only the mutation is guarded
public Rate refresh(String symbol) {
  Rate rate = httpClient.fetchRate(symbol);
  synchronized (lock) {
    cache.put(symbol, rate);
  }
  return rate;
}
```

## 26.8 Synchronize on a private final lock object, never on `this`, a public field, or a non-final field.

> Why? Synchronizing on `this` or on a publicly reachable object makes the
> lock part of your public API: any caller can `synchronized (yourObject)`
> and stall your internals, and any subclass can take the same lock in a
> different order. Synchronizing on a *non-final* field is worse — if the
> field is reassigned, two threads synchronize on two different objects and
> the block provides no mutual exclusion at all. **Violation — enforced by
> Error Prone `SynchronizeOnNonFinalField`.**

```java
// bad — the lock is reassignable, so the block guarantees nothing
public class Registry {
  private Map<String, Entry> entries = new HashMap<>();

  public void put(String key, Entry entry) {
    synchronized (entries) {  // entries can be swapped out from under us
      entries.put(key, entry);
    }
  }

  public void reset() {
    entries = new HashMap<>();
  }
}

// good — a dedicated, private, final lock nobody else can reach or replace
public class Registry {
  private final Object lock = new Object();
  private Map<String, Entry> entries = new HashMap<>();

  public void put(String key, Entry entry) {
    synchronized (lock) {
      entries.put(key, entry);
    }
  }

  public void reset() {
    synchronized (lock) {
      entries = new HashMap<>();
    }
  }
}
```

## 26.9 Never synchronize on a boxed primitive, a `String` literal, or any other interned or cached object.

> Why? `Integer.valueOf` caches values in `[-128, 127]` and the compiler
> interns every `String` literal, so two unrelated classes that synchronize
> on `Integer.valueOf(1)` or on `"lock"` end up sharing one monitor across
> the entire JVM. The resulting contention and deadlocks are effectively
> undebuggable, because the two participants have no visible relationship.
> **Suggestion.**

```java
// bad — every class in the JVM that locks on this literal shares one monitor
private static final String LOCK = "cache-lock";

void evict() {
  synchronized (LOCK) {
    cache.clear();
  }
}

// good — an identity nobody else can obtain
private static final Object LOCK = new Object();

void evict() {
  synchronized (LOCK) {
    cache.clear();
  }
}
```

## 26.10 Annotate every guarded field with `@GuardedBy`, naming the lock that protects it.

> Why? A lock relationship that lives only in a reviewer's head is a lock
> relationship that gets dropped in the next refactor.
> `@GuardedBy("lock")` turns that relationship into something the compiler
> plugin can verify: Error Prone's `GuardedBy` check reports any read or
> write of the field that does not hold the named lock, and
> `StaticGuardedByInstance` reports the specific error of guarding a static
> field with an instance lock (where each instance has its own monitor, so
> nothing is actually guarded). **Violation — enforced by Error Prone
> `GuardedBy` and `StaticGuardedByInstance`.**

```java
// bad — nothing records that `pending` needs the lock, and drain() forgets it
public final class Outbox {
  private final Object lock = new Object();
  private final List<Message> pending = new ArrayList<>();

  public void enqueue(Message message) {
    synchronized (lock) {
      pending.add(message);
    }
  }

  public List<Message> drain() {
    List<Message> copy = List.copyOf(pending);  // unguarded read
    pending.clear();
    return copy;
  }
}

// good — the invariant is declared and mechanically checked
public final class Outbox {
  private final Object lock = new Object();

  @GuardedBy("lock")
  private final List<Message> pending = new ArrayList<>();

  public void enqueue(Message message) {
    synchronized (lock) {
      pending.add(message);
    }
  }

  public List<Message> drain() {
    synchronized (lock) {
      List<Message> copy = List.copyOf(pending);
      pending.clear();
      return copy;
    }
  }
}
```

## 26.11 Submit tasks to an `ExecutorService`; do not create `Thread` objects by hand.

> Why? Effective Java, 3rd ed., Item 80 ("Prefer executors, tasks, and
> streams to threads") separates the *unit of work* (a `Runnable` or
> `Callable`) from the *mechanism that runs it* (the executor), so you can
> change the execution policy without touching the work. A hand-rolled
> `new Thread(...).start()` has no queue, no lifecycle, no rejection policy,
> no way to observe a failure, and no way to wait for completion — you
> rebuild all of that badly, in every class that needs it. **Suggestion.**

```java
// bad — no lifecycle, no result, no way to observe a failure
for (Order order : orders) {
  new Thread(() -> process(order)).start();
}

// good — one execution policy, results you can inspect
public void processAll(List<Order> orders) throws InterruptedException, ExecutionException {
  List<Callable<Receipt>> tasks =
      orders.stream().<Callable<Receipt>>map(order -> () -> process(order)).toList();
  try (ExecutorService executor = Executors.newFixedThreadPool(8)) {
    for (Future<Receipt> receipt : executor.invokeAll(tasks)) {
      record(receipt.get());
    }
  }
}
```

## 26.12 Choose the executor from the workload, and never point a production server at `Executors.newCachedThreadPool`.

> Why? Effective Java, 3rd ed., Item 80 singles this out: a cached thread
> pool hands work straight to a thread and creates a new one if none is
> free, so under load "if the server is so heavily loaded that all of its
> CPUs are fully utilized and more tasks arrive, more threads will be
> created, which will only make matters worse." Bloch's guidance is
> `newFixedThreadPool` for a heavily loaded production server, or a directly
> configured `ThreadPoolExecutor` when you need control over the queue and
> the rejection policy. For thread-per-request blocking I/O on Java 21, see
> [Chapter 27, §27.1](27-virtual-threads.md). **Suggestion.**

```java
// bad — unbounded thread creation under load
private static final ExecutorService POOL = Executors.newCachedThreadPool();

// good — bounded threads, bounded queue, explicit rejection policy
private static final ExecutorService POOL =
    new ThreadPoolExecutor(
        8,
        8,
        0L,
        TimeUnit.MILLISECONDS,
        new ArrayBlockingQueue<>(1_000),
        new ThreadPoolExecutor.CallerRunsPolicy());
```

## 26.13 Shut an executor down deterministically: `shutdown`, then `awaitTermination`, then `shutdownNow`, then await again.

> Why? `shutdown()` only *initiates* an orderly shutdown; it returns
> immediately and does not wait. A process that calls `shutdown()` and exits
> abandons in-flight work, and a process that never calls it at all keeps
> running if the pool's threads are non-daemon. The
> [`ExecutorService`
> javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ExecutorService.html)
> documents this two-phase idiom directly. When the executor's lifetime is
> exactly one method, use `try`-with-resources instead — `ExecutorService`
> extends `AutoCloseable` since Java 19, and `close()` performs the orderly
> shutdown-and-wait for you (see
> [Chapter 9, §9.12](09-object-lifecycle-and-resources.md)). **Suggestion.**

```java
// bad — returns before any task has finished; work is abandoned at exit
public void stop() {
  executor.shutdown();
}

// good — bounded, two-phase, interrupt-safe shutdown
public void stop() {
  executor.shutdown();
  try {
    if (!executor.awaitTermination(30, TimeUnit.SECONDS)) {
      executor.shutdownNow();
      if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
        log.error("executor did not terminate");
      }
    }
  } catch (InterruptedException e) {
    executor.shutdownNow();
    Thread.currentThread().interrupt();
  }
}
```

## 26.14 Never discard the `Future` returned by `submit` — an exception thrown by the task vanishes with it.

> Why? `ExecutorService.submit` captures any `Throwable` the task threw
> inside the returned `Future` and rethrows it, wrapped in an
> `ExecutionException`, only when someone calls `get()`. Drop the `Future`
> and the failure is never reported anywhere: no stack trace, no log line,
> just a task that silently did nothing. `execute(Runnable)` has the
> opposite behaviour (the uncaught-exception handler fires), which is why
> "fire and forget" work should use `execute`, not a discarded `submit`.
> **Violation — enforced by Error Prone `FutureReturnValueIgnored`.**

```java
// bad — if index() throws, nobody will ever know
public void reindex(List<Document> documents) {
  for (Document document : documents) {
    executor.submit(() -> index(document));
  }
}

// good — collect the futures and surface every failure
public void reindex(List<Document> documents) throws InterruptedException {
  List<Future<?>> futures = new ArrayList<>();
  for (Document document : documents) {
    futures.add(executor.submit(() -> index(document)));
  }
  for (Future<?> future : futures) {
    try {
      future.get();
    } catch (ExecutionException e) {
      throw new IndexingException("indexing failed", e.getCause());
    }
  }
}
```

## 26.15 Reach for a `java.util.concurrent` utility before you write `wait` and `notify`.

> Why? Effective Java, 3rd ed., Item 81 ("Prefer concurrency utilities to
> wait and notify") states the position plainly: "given the difficulty of
> using `wait` and `notify` correctly, you should use the higher-level
> concurrency utilities instead." `CountDownLatch`, `Semaphore`,
> `CyclicBarrier`, `BlockingQueue`, and `ConcurrentHashMap` are tested,
> documented, and impossible to get wrong in the specific ways `wait`/
> `notify` invite. Item 81 also notes the corollary for new code: "there is
> seldom, if ever, a reason to use `wait` and `notify` in new code."
> **Suggestion.**

```java
// bad — hand-rolled rendezvous with wait/notify
private int remaining;

public synchronized void awaitAll() throws InterruptedException {
  while (remaining > 0) {
    wait();
  }
}

public synchronized void taskDone() {
  if (--remaining == 0) {
    notifyAll();
  }
}

// good — the library already models "wait for N things"
private final CountDownLatch remaining = new CountDownLatch(taskCount);

public void awaitAll() throws InterruptedException {
  remaining.await();
}

public void taskDone() {
  remaining.countDown();
}
```

## 26.16 Use `ConcurrentHashMap` and its atomic compound operations instead of a synchronized map plus check-then-act.

> Why? Effective Java, 3rd ed., Item 81 recommends `ConcurrentHashMap` over
> `Collections.synchronizedMap` outright: the synchronized wrapper
> serializes every operation behind one lock and still leaves compound
> operations racy, because the lock is released between your `containsKey`
> and your `put`. `computeIfAbsent`, `putIfAbsent`, `merge`, and `compute`
> are atomic as a whole, which removes both the race and the contention.
> See also [Chapter 20, §20.23](20-collections.md). **Suggestion.**

```java
// bad — atomic per call, racy across calls; two threads both create a session
Map<String, Session> sessions = Collections.synchronizedMap(new HashMap<>());
if (!sessions.containsKey(id)) {
  sessions.put(id, openSession(id));
}
return sessions.get(id);

// good — one atomic compound operation
Map<String, Session> sessions = new ConcurrentHashMap<>();
return sessions.computeIfAbsent(id, this::openSession);
```

## 26.17 If you must use `wait`, call it inside a `while` loop that rechecks the condition, and prefer `notifyAll` to `notify`.

> Why? Effective Java, 3rd ed., Item 81 calls the loop idiom the "standard
> idiom for using the wait method" and requires it: a thread can wake from
> `wait` without any corresponding `notify` (a spurious wakeup), or a third
> thread can grab the lock and invalidate the condition between the `notify`
> and the waiter's reacquisition. Testing the condition with `if` and
> proceeding is therefore always wrong. `notifyAll` is the safe default
> because `notify` wakes exactly one waiter — and if the waiters are waiting
> on different conditions, it may wake the wrong one, which then goes back
> to sleep and the signal is lost forever. **Violation — enforced by Error
> Prone `WaitNotInLoop`.**

```java
// bad — spurious wakeup or a lost race proceeds with an unmet condition
synchronized (lock) {
  if (queue.isEmpty()) {
    lock.wait();
  }
  return queue.remove();
}

// good — recheck in a loop, and wake every waiter
synchronized (lock) {
  while (queue.isEmpty()) {
    lock.wait();
  }
  return queue.remove();
}
```

## 26.18 Use `ReentrantLock` when you need a timeout, interruptibility, or fairness — and put `lock()` immediately before the `try` whose `finally` unlocks.

> Why? `synchronized` cannot time out, cannot be interrupted, and cannot be
> acquired in one method and released in another. `ReentrantLock` can do all
> three, at the cost of manual release: if the `unlock()` is not in a
> `finally`, any exception between `lock()` and `unlock()` leaks the lock
> permanently and every subsequent caller deadlocks. Putting anything
> between the `lock()` call and the `try` is the same bug in slower motion —
> if that statement throws, the `finally` never runs. On a virtual thread
> `ReentrantLock` has a second advantage: it does not pin the carrier thread
> (see [Chapter 27, §27.5](27-virtual-threads.md)). **Violation — enforced
> by Error Prone `LockNotBeforeTry`.**

```java
// bad — the statement between lock() and try can throw and leak the lock
lock.lock();
Metrics.recordAcquire();
try {
  mutate();
} finally {
  lock.unlock();
}

// good — nothing can run between the acquire and the try
lock.lock();
try {
  Metrics.recordAcquire();
  mutate();
} finally {
  lock.unlock();
}

// good — the timeout variant, which synchronized cannot express
if (!lock.tryLock(500, TimeUnit.MILLISECONDS)) {
  throw new TimeoutException("could not acquire ledger lock");
}
try {
  mutate();
} finally {
  lock.unlock();
}
```

## 26.19 Document every public class's thread safety in its Javadoc, using the standard vocabulary.

> Why? Effective Java, 3rd ed., Item 82 ("Document thread safety") is
> explicit that the `synchronized` modifier "is an implementation detail,
> not a part of its exported API" — its presence in a signature tells a
> caller nothing reliable. Item 82 defines five levels a class can document:
> **immutable**, **unconditionally thread-safe**, **conditionally
> thread-safe**, **not thread-safe**, and **thread-hostile**. A
> conditionally thread-safe class must additionally document which sequences
> require external synchronization and which lock to hold. Without this, the
> caller guesses, and half the time guesses wrong. See
> [Chapter 4](04-javadoc.md) for the Javadoc form. **Suggestion.**

```java
// bad — the caller has no idea whether concurrent access is safe
/** A bounded cache of rendered templates. */
public final class TemplateCache { ... }

// good — states the level and, for a conditionally safe view, the lock
/**
 * A bounded cache of rendered templates.
 *
 * <p>This class is unconditionally thread-safe: all methods may be called
 * concurrently without external synchronization. The iterator returned by
 * {@link #keys()} is conditionally thread-safe — callers must hold the
 * cache instance's monitor for the entire iteration:
 *
 * <pre>{@code
 * synchronized (cache) {
 *   for (String key : cache.keys()) { ... }
 * }
 * }</pre>
 */
public final class TemplateCache { ... }
```

## 26.20 Never drop `synchronized` when overriding a synchronized method.

> Why? A subclass that overrides a synchronized method without the modifier
> silently removes the lock from every call that goes through the subclass,
> while the superclass's Javadoc still promises thread safety. Callers
> holding a superclass-typed reference have no way to see the difference.
> This is the concrete mechanism behind Item 82's warning that
> synchronization is an implementation detail — and it is exactly why a
> class that documents thread safety should be `final` or should keep its
> synchronization in a private final lock the subclass cannot bypass.
> **Violation — enforced by Error Prone
> `UnsynchronizedOverridesSynchronized`.**

```java
// bad — the override quietly removes the lock the base class promised
public class BufferedSink {
  public synchronized void write(byte[] data) { ... }
}

public class CountingSink extends BufferedSink {
  @Override
  public void write(byte[] data) {  // no longer synchronized
    written += data.length;
    super.write(data);
  }
}

// good — the override preserves the contract
public class CountingSink extends BufferedSink {
  @Override
  public synchronized void write(byte[] data) {
    written += data.length;
    super.write(data);
  }
}
```

## 26.21 Initialize eagerly by default; use the holder idiom for lazy statics and correct double-checked locking for lazy instance fields.

> Why? Effective Java, 3rd ed., Item 83 ("Use lazy initialization
> judiciously") gives the rule as "under most circumstances, normal
> initialization is preferable to lazy initialization." When you do need it,
> the *lazy initialization holder class idiom* is the correct form for a
> static field: the JVM guarantees class initialization is thread-safe and
> happens exactly once, so the accessor needs no synchronization on any
> call. For an instance field, double-checked locking is correct **only** if
> the field is `volatile` — without it, another thread can see a non-null
> reference to a not-yet-initialized object, which is the single most
> common broken concurrency idiom in Java. **Violation — enforced by Error
> Prone `DoubleCheckedLocking`.**

```java
// bad — non-volatile field; a reader can see a partially constructed Parser
private static Parser instance;

public static Parser getInstance() {
  if (instance == null) {
    synchronized (Parser.class) {
      if (instance == null) {
        instance = new Parser();
      }
    }
  }
  return instance;
}

// good — holder idiom: no synchronization on the fast path, and no way to
// get it wrong
private static class ParserHolder {
  static final Parser INSTANCE = new Parser();
}

public static Parser getInstance() {
  return ParserHolder.INSTANCE;
}

// good — the instance-field form, with the volatile the idiom requires
private volatile FieldType field;

private FieldType getField() {
  FieldType result = field;  // one volatile read on the common path
  if (result == null) {
    synchronized (this) {
      if (field == null) {
        field = result = computeFieldValue();
      }
    }
  }
  return result;
}
```

## 26.22 Never make correctness depend on the thread scheduler — no `Thread.yield`, no thread priorities.

> Why? Effective Java, 3rd ed., Item 84 ("Don't depend on the thread
> scheduler") states that "any program that relies on the thread scheduler
> for correctness or performance is likely to be nonportable," and is blunt
> about the two usual patches: `Thread.yield` "has no testable semantics,"
> and thread priorities "are among the least portable features of Java." A
> `yield` that fixes a race on your laptop is a race that still exists on
> every other JVM and CPU. Fix the synchronization instead. Virtual threads
> make the priority case moot as well — a virtual thread's priority is fixed
> and cannot be changed. **Violation — enforced by Error Prone
> `ThreadPriorityCheck`.**

```java
// bad — papering over a race with the scheduler
private boolean ready;

void awaitReady() {
  while (!ready) {
    Thread.yield();
  }
  worker.setPriority(Thread.MAX_PRIORITY);
}

// good — a real happens-before edge, and a real blocking wait
private final CountDownLatch ready = new CountDownLatch(1);

void awaitReady() throws InterruptedException {
  ready.await();
}
```

## 26.23 Never busy-wait on a shared field when a blocking primitive exists.

> Why? Effective Java, 3rd ed., Item 84 identifies busy-waiting as the main
> cause of programs whose behaviour depends on the scheduler: a spin loop
> "greatly increases the load on the scheduler," burns a core doing nothing,
> and makes every other runnable thread slower. `CountDownLatch`,
> `BlockingQueue.take`, `Future.get`, and `Condition.await` all park the
> thread instead, costing nothing while they wait. (`Thread.onSpinWait` is a
> hint for genuine sub-microsecond spin loops in lock implementations, not a
> licence to spin at application level.) **Suggestion.**

```java
// bad — burns a CPU core until the flag flips
while (!job.isComplete()) {
  // spin
}
return job.result();

// good — blocks with no CPU cost, and propagates failures
return future.get();
```

## 26.24 Compose `CompletableFuture` chains instead of blocking on `get`, and always pass an explicit executor.

> Why? Every `get()` inside an async pipeline gives back the thread you were
> trying to save, and a `get()` executed on the same pool that must run the
> awaited task deadlocks outright. The `*Async` overloads that take no
> executor run on
> [`ForkJoinPool.commonPool()`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ForkJoinPool.html#commonPool()),
> which is sized for CPU-bound work and shared with parallel streams —
> putting a blocking JDBC call there starves everything else in the process.
> Name the executor so the execution policy is visible at the call site.
> **Suggestion.**

```java
// bad — blocking gets, and the common pool used for blocking I/O
CompletableFuture<User> user = CompletableFuture.supplyAsync(() -> loadUser(id));
CompletableFuture<Cart> cart = CompletableFuture.supplyAsync(() -> loadCart(id));
return new Page(user.get(), cart.get());

// good — composed, non-blocking, on a pool chosen for blocking I/O
CompletableFuture<User> user = CompletableFuture.supplyAsync(() -> loadUser(id), ioExecutor);
CompletableFuture<Cart> cart = CompletableFuture.supplyAsync(() -> loadCart(id), ioExecutor);
return user.thenCombine(cart, Page::new)
    .orTimeout(2, TimeUnit.SECONDS)
    .exceptionally(Page::degraded);
```

## 26.25 Never swallow `InterruptedException` — rethrow it, or restore the interrupt status.

> Why? `InterruptedException` is the JDK's cancellation signal, and catching
> it clears the thread's interrupt status. Swallowing it therefore destroys
> the only evidence that cancellation was requested: the enclosing loop
> keeps running, the executor's `shutdownNow` never takes effect, and the
> JVM refuses to exit. Google's Java Style Guide
> [§6.2](https://google.github.io/styleguide/javaguide.html#s6.2-caught-exceptions)
> already forbids an empty `catch` without a justifying comment; for this
> exception specifically the only two correct responses are to propagate it
> or to re-assert the interrupt before returning. See
> [Chapter 24, §24.21](24-exceptions.md) for the general form. **Violation —
> the empty-catch form below is enforced by Checkstyle `EmptyCatchBlock`;
> Error Prone `InterruptedExceptionSwallowed` covers the related shape where
> a declared `InterruptedException` is caught as a broader
> `Exception`/`Throwable` and the interruption is not handled separately. A
> `catch` that logs but neither rethrows nor re-interrupts is caught by
> neither tool — that one is on the reviewer.**

```java
// bad — cancellation is silently discarded and the loop keeps going
while (running) {
  try {
    Thread.sleep(1_000);
    poll();
  } catch (InterruptedException e) {
    // ignored
  }
}

// good — restore the flag and stop
while (running) {
  try {
    Thread.sleep(1_000);
    poll();
  } catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    return;
  }
}
```

## 26.26 Wait for a thread with `join` inside a loop that rechecks the termination condition.

> Why? `Thread.join()` can be interrupted, and Error Prone states the
> consequence directly: "`Thread.join()` can be interrupted, and so requires
> users to catch `InterruptedException`. Most users should be looping until
> the `join()` actually succeeds." A single `join()` whose
> `InterruptedException` is caught and handled locally is therefore not proof
> of termination — the code goes on to read state the joined thread had not
> finished writing. Loop until the thread is genuinely gone, or, better, use
> an executor and a `Future` so the JDK does the bookkeeping. (The join
> itself does not wake spuriously: the Java 21 `Thread` javadoc's
> implementation note records that for platform threads "the implementation
> uses a loop of `this.wait` calls conditioned on `this.isAlive`.")
> **Violation — enforced by Error Prone `ThreadJoinLoop`.**

```java
// bad — a single join is not proof the thread finished
worker.join();
return worker.getResult();

// good — loop until the thread is genuinely gone
while (worker.isAlive()) {
  try {
    worker.join();
  } catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new CancellationException("interrupted while joining worker");
  }
}
return worker.getResult();
```

## 26.27 Never call `Thread.stop`, `Thread.suspend`, or `Thread.resume` — cancel cooperatively instead.

> Why? All three are deprecated for removal and, as of Java 20, throw
> `UnsupportedOperationException` unconditionally — see the
> [`Thread`
> javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html),
> which explains that `stop` "was inherently unsafe" because it unlocked
> every monitor the victim held, publishing objects in an inconsistent
> state, and that `suspend` "was inherently deadlock-prone." The supported
> mechanism is cooperative: interrupt the thread and have the task check
> `Thread.currentThread().isInterrupted()` at a safe point. **Suggestion.**

```java
// bad — throws UnsupportedOperationException on Java 20+, and was never safe
worker.stop();

// good — cooperative cancellation the task can honour at a safe point
worker.interrupt();

// inside the task
while (!Thread.currentThread().isInterrupted()) {
  processNextBatch();
}
```

## 26.28 Do not share a `SimpleDateFormat`, a `Random`, or any other stateful utility that is not documented as safe to share, across threads.

> Why? These are the most common accidental shared-mutable-state bugs,
> because the objects look like value helpers and are naturally hoisted into
> a `static final` field. `SimpleDateFormat` mutates an internal `Calendar`
> on every call and will silently return wrong dates under concurrency;
> `java.util.Random` is documented as thread-safe, but its shared seed makes
> it a contention point rather than a safe thing to share. Both have modern
> replacements that are immutable or
> thread-confined: `DateTimeFormatter` (see
> [Chapter 28](28-dates-and-times.md)) and `ThreadLocalRandom`.
> **Suggestion.**

```java
// bad — shared mutable formatter; concurrent calls corrupt each other
private static final SimpleDateFormat FORMAT = new SimpleDateFormat("yyyy-MM-dd");

String render(Instant instant) {
  return FORMAT.format(Date.from(instant));
}

// good — DateTimeFormatter is immutable and thread-safe by contract
private static final DateTimeFormatter FORMAT =
    DateTimeFormatter.ISO_LOCAL_DATE.withZone(ZoneOffset.UTC);

String render(Instant instant) {
  return FORMAT.format(instant);
}
```
