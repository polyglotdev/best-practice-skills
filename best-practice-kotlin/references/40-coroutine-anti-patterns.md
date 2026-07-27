<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 40. Coroutine Anti-patterns

This chapter is the catalogue. Everything in it is a failure that reviewers
routinely wave through, either because it compiles and passes the happy-path
test, or because the damage lands in a different file, a different thread pool,
or three weeks later under load. Each entry names the failure, explains what it
costs, and gives the replacement.

Nothing here is new material. Structured concurrency and scope ownership are
[Chapter 33, Coroutine Fundamentals](33-coroutine-fundamentals.md); dispatcher
selection and injection are [Chapter 34, Dispatchers & Coroutine
Context](34-dispatchers-and-context.md); the mechanics of cancellation are
[Chapter 35, Cancellation & Timeouts](35-cancellation-and-timeouts.md); cold
versus hot streams are Chapters [36](36-flow.md) and
[37](37-stateflow-and-sharedflow.md); the exception rules these build on are
[Chapter 24, Exceptions & `Result`](24-exceptions-and-result.md). What this
chapter adds is the diff between "the rule exists" and "the rule is being
broken in this file right now", which is the form a reviewer actually needs.

The upstream sources are the
[coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html), the
[kotlinx.coroutines API
reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/),
and [Shared mutable state and
concurrency](https://kotlinlang.org/docs/shared-mutable-state-and-concurrency.html).

**Tool alignment:** this is the most heavily linted chapter in the skill. All
nine of detekt's coroutine rules are enabled in this repo's
`config/detekt/detekt.yml` — `GlobalCoroutineUsage`, `InjectDispatcher`,
`SleepInsteadOfDelay`, `SuspendFunSwallowedCancellation`,
`SuspendFunInFinallySection`, `SuspendFunWithFlowReturnType`,
`SuspendFunWithCoroutineScopeReceiver`, `RedundantSuspendModifier`, and
`CoroutineLaunchedInTestWithoutRunTest` — and `TooGenericExceptionCaught` from
the exceptions ruleset backs §40.10. Rules a named check actually enforces are
marked **Violation**; the rest are **Suggestion**.

## 40.1 Never launch work in `GlobalScope`.

> Why? `GlobalScope` is a `CoroutineScope` with no `Job`, so nothing can cancel
> it and nothing waits for it. Its own
> [reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-global-scope/)
> lists three consequences: computations continue "after a user leaves a
> screen", "a coroutine that never gets cancelled or resumed can be a resource
> leak", and because "GlobalScope does not have a `CoroutineExceptionHandler`
> installed", a failure reaches "platform-specific last-resort error
> propagation behavior". It is annotated `@DelicateCoroutinesApi` precisely so
> that using it is a deliberate, opt-in act. Own a scope, or use
> `coroutineScope`/`withContext` and stay structured.
> **Violation — enforced by `detekt/GlobalCoroutineUsage`.**

```kotlin
// bad — no owner, no cancellation, no error handling; survives shutdown
fun onOrderPlaced(order: Order) {
    GlobalScope.launch {
        analytics.track(OrderPlaced(order.id))
    }
}

// good — an owned scope with a cancellation path (see 40.5)
class OrderEvents(
    private val analytics: Analytics,
    private val scope: CoroutineScope,
) {
    fun onOrderPlaced(order: Order) {
        scope.launch {
            analytics.track(OrderPlaced(order.id))
        }
    }
}
```

## 40.2 Never call `runBlocking` inside a `suspend` function.

> Why?
> [`runBlocking`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/run-blocking.html)
> blocks the calling thread until its body completes. Inside a `suspend`
> function that thread is a dispatcher worker, so the call converts a
> suspension — which releases the thread — into a block, which does not. On
> `Dispatchers.Default`, sized to `availableProcessors`, a handful of these
> deadlocks the pool. The call is also pure ceremony: you are already in a
> coroutine, so the inner body can simply be awaited directly.
> **Suggestion** — no detekt rule covers this shape.

```kotlin
// bad — pins a dispatcher thread for the duration of the network call
suspend fun enrich(order: Order): EnrichedOrder {
    val customer = runBlocking { customers.load(order.customerId) }
    return EnrichedOrder(order, customer)
}

// good
suspend fun enrich(order: Order): EnrichedOrder {
    val customer = customers.load(order.customerId)
    return EnrichedOrder(order, customer)
}
```

## 40.3 Never call `runBlocking` on a request-serving thread.

> Why? On a servlet container the request thread pool is a fixed, small
> resource. A `runBlocking` in a controller holds one of those threads for the
> full latency of everything inside it, so throughput collapses to
> `poolSize / averageLatency` regardless of how much work is actually
> suspending underneath. On a reactive stack it is worse: blocking an event
> loop thread stalls every unrelated request multiplexed onto it. Make the
> handler `suspend` and let the framework drive the coroutine — see
> [Chapter 44](44-spring-web-and-coroutines.md). `runBlocking` belongs in
> `main`, in a JVM shutdown hook, and in a `@Test` that has no `runTest`
> alternative, and nowhere else. **Suggestion.**

```kotlin
// bad — one request thread held for the whole call chain
@GetMapping("/orders/{id}")
fun order(@PathVariable id: String): OrderResponse = runBlocking {
    OrderResponse.from(orders.load(OrderId(id)))
}

// good — the handler suspends; the thread is released at every suspension
@GetMapping("/orders/{id}")
suspend fun order(@PathVariable id: String): OrderResponse =
    OrderResponse.from(orders.load(OrderId(id)))
```

## 40.4 Never write a `launch` whose owning scope you cannot name.

> Why? `launch` returns a `Job` and attaches it to the receiver scope. If you
> cannot point at the object that owns that scope and at the line that cancels
> it, the coroutine is unbounded: it keeps running after the caller has
> returned, it holds every object it captured, and its failure surfaces
> somewhere unrelated. "Fire and forget" is only forgettable when a supervisor
> is remembering it for you. The fix is either an owned scope (§40.5) or
> dropping the `launch` and letting the function suspend. **Suggestion.**

```kotlin
// bad — an anonymous scope created at the call site; nothing holds the Job,
// so the work cannot be cancelled, joined, or observed
fun archive(orderId: OrderId) {
    CoroutineScope(Dispatchers.IO).launch {
        archiver.archive(orderId)
    }
}

// good — the work is part of the caller's structured lifetime
suspend fun archive(orderId: OrderId) {
    archiver.archive(orderId)
}

// good — genuinely background work, on a scope with a named owner
class ArchiveWorker(private val scope: CoroutineScope, private val archiver: Archiver) {
    fun enqueue(orderId: OrderId): Job = scope.launch { archiver.archive(orderId) }
}
```

## 40.5 Never construct a `CoroutineScope` you do not also cancel.

> Why? `CoroutineScope(...)` is a factory, not a lifecycle. Creating one per
> call, per request, or per object without a matching `cancel()` leaks the
> `Job`, every child coroutine under it, and everything those children captured
> — and because the scope has no parent, no enclosing cancellation ever reaches
> it. A scope is a resource: create it once, at the level of a component that
> has a shutdown hook, and cancel it there. Use `SupervisorJob` so one failing
> child does not take down its siblings. **Suggestion.**

```kotlin
// bad — a fresh scope per call, never cancelled; every invocation leaks a Job
class ReportScheduler(private val reports: Reports) {
    fun schedule(id: ReportId) {
        CoroutineScope(SupervisorJob()).launch { reports.build(id) }
    }
}

// good — one owned scope, cancelled on close
class ReportScheduler(
    private val reports: Reports,
    dispatcher: CoroutineDispatcher = Dispatchers.Default,
) : AutoCloseable {
    private val scope = CoroutineScope(SupervisorJob() + dispatcher)

    fun schedule(id: ReportId): Job = scope.launch { reports.build(id) }

    override fun close() {
        scope.cancel()
    }
}
```

## 40.6 Never leave an `async` un-awaited.

> Why? `async` stores its failure in the returned `Deferred` and rethrows it
> from `await()`. If nothing ever calls `await()`, the only remaining path to
> the surface is parent-failure propagation — and under `supervisorScope`, or
> any scope built on a `SupervisorJob`, there is no such propagation. The
> exception is then lost completely: the work silently did not happen, no log
> line is written, and the caller proceeds on partial data. If you want
> fire-and-forget, say `launch`, which reports its failures. **Suggestion.**

```kotlin
// bad — under a SupervisorJob the failure of `audit` disappears entirely
suspend fun settle(invoice: Invoice) = supervisorScope {
    async { auditLog.record(invoice) }
    payments.charge(invoice.amount)
}

// good — await it, so the failure has somewhere to go
suspend fun settle(invoice: Invoice) = supervisorScope {
    val audit = async { auditLog.record(invoice) }
    payments.charge(invoice.amount)
    audit.await()
}

// good — or say what you mean: launch reports its own failures
suspend fun settle(invoice: Invoice) = supervisorScope {
    launch { auditLog.record(invoice) }
    payments.charge(invoice.amount)
}
```

## 40.7 Never use `async { ... }.await()` for a single value — that is `withContext`.

> Why? `async` exists to start work that overlaps with *other* work. Starting
> one and immediately awaiting it is sequential execution with a `Deferred`, a
> child `Job`, and an extra dispatch added on top, and it reads to a reviewer
> as though concurrency was intended, which invites someone to "fix" the
> sequential await later. `withContext` expresses the same thing — run this
> body on that dispatcher, give me the result — with none of the machinery.
> `async` earns its keep only when two or more are in flight before the first
> `await`. **Suggestion.**

```kotlin
// bad — a Deferred and a child Job to perform one sequential call
suspend fun loadProfile(id: UserId): Profile = coroutineScope {
    val profile = async(ioDispatcher) { repo.load(id) }
    profile.await()
}

// good
suspend fun loadProfile(id: UserId): Profile =
    withContext(ioDispatcher) { repo.load(id) }

// good — async is correct here: both are in flight before either is awaited
suspend fun loadDashboard(id: UserId): Dashboard = coroutineScope {
    val profile = async(ioDispatcher) { repo.load(id) }
    val orders = async(ioDispatcher) { orderRepo.recent(id) }
    Dashboard(profile.await(), orders.await())
}
```

## 40.8 Never make a blocking call without moving it to a dispatcher sized for blocking.

> Why? JDBC, `java.io`, `java.net.http.HttpClient.send`, `Files.*`, and every
> synchronous SDK block the calling thread. `Dispatchers.Default` has roughly
> `availableProcessors` threads, so a handful of concurrent blocking calls
> starve every CPU-bound coroutine in the process, including ones in unrelated
> features. `withContext(ioDispatcher)` moves the blocking region onto a pool
> that is allowed to grow, and makes the region visible in the source. Where
> the blocking API responds to `Thread.interrupt`, prefer
> [`runInterruptible`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/run-interruptible.html),
> which turns coroutine cancellation into an interrupt rather than leaving the
> call to run to completion. **Suggestion** — detekt cannot recognise an
> arbitrary blocking call.

```kotlin
// bad — both calls block whichever dispatcher the caller happened to be on
suspend fun fetchAndCache(url: URI): ByteArray {
    val cached = Files.readAllBytes(cachePath(url))
    if (cached.isNotEmpty()) return cached
    return httpClient.send(request(url), BodyHandlers.ofByteArray()).body()
}

// good — the blocking region is explicit and on an injected IO dispatcher
suspend fun fetchAndCache(url: URI): ByteArray = withContext(ioDispatcher) {
    val cached = Files.readAllBytes(cachePath(url))
    if (cached.isNotEmpty()) return@withContext cached
    httpClient.send(request(url), BodyHandlers.ofByteArray()).body()
}

// good — cancellation interrupts the blocking call instead of waiting it out
suspend fun take(queue: BlockingQueue<Task>): Task =
    runInterruptible(ioDispatcher) { queue.take() }
```

## 40.9 Never call `Thread.sleep` in a coroutine.

> Why? `Thread.sleep` blocks the carrier thread and is not a cancellation
> point, so it both starves the dispatcher and makes the surrounding coroutine
> uncancellable for its duration — a `withTimeout` wrapped around it will not
> fire until the sleep is over. detekt's rationale is that one coroutine
> calling it "could potentially halt the execution of unrelated coroutines and
> cause unpredictable behavior". `delay` suspends instead, releases the
> thread, is cancellable, and is skipped entirely under `runTest`
> ([Chapter 39, §39.11](39-coroutine-testing.md)).
> **Violation — enforced by `detekt/SleepInsteadOfDelay`.**

```kotlin
// bad — blocks the dispatcher thread; withTimeout cannot interrupt it
suspend fun pollUntilReady(job: JobId) {
    while (!api.isReady(job)) {
        Thread.sleep(500L)
    }
}

// good
suspend fun pollUntilReady(job: JobId) {
    while (!api.isReady(job)) {
        delay(500L)
    }
}
```

## 40.10 Never catch `Exception` or `Throwable` around a suspending call without rethrowing `CancellationException`.

> Why? Cancellation in Kotlin is delivered *as* an exception.
> `CancellationException` extends `IllegalStateException`, so `catch (e:
> Exception)` catches it, and a coroutine that catches its own cancellation and
> carries on is no longer cancellable — `job.cancel()` returns, the caller
> believes the work stopped, and the work keeps running and keeps holding its
> resources. This is the most damaging entry in the chapter because the symptom
> (a slow leak under load) never points back at the `catch`. Catch the specific
> type, or rethrow cancellation first. See [Chapter 24,
> §24.17](24-exceptions-and-result.md) and
> [Chapter 35](35-cancellation-and-timeouts.md).
> **Violation — enforced by `detekt/TooGenericExceptionCaught`.**

```kotlin
// bad — swallows CancellationException; this coroutine can never be cancelled
suspend fun sync(feed: FeedId) {
    while (true) {
        try {
            feeds.pull(feed)
        } catch (e: Exception) {
            logger.warn(e) { "pull failed for $feed" }
        }
        delay(30.seconds)
    }
}

// good — cancellation propagates, real failures are still handled
suspend fun sync(feed: FeedId) {
    while (true) {
        try {
            feeds.pull(feed)
        } catch (e: CancellationException) {
            throw e
        } catch (e: IOException) {
            logger.warn(e) { "pull failed for $feed" }
        }
        delay(30.seconds)
    }
}
```

## 40.11 Never wrap a suspending call in `runCatching`.

> Why? `runCatching` catches `Throwable`, which is strictly worse than §40.10:
> it swallows `CancellationException` *and* `OutOfMemoryError` *and*
> `StackOverflowError`, and it does so in one word with no `catch` clause for a
> reviewer to notice. detekt's own wording is that `suspend` functions
> "should not be called inside `runCatching`'s lambda block, because
> `runCatching` catches all the `Exception`s", and that a swallowed
> `CancellationException` must "always be immediately rethrown in the same
> context". If you want a `Result`-shaped return, build it from an explicit
> `try`/`catch` that rethrows cancellation first.
> **Violation — enforced by `detekt/SuspendFunSwallowedCancellation`.**

```kotlin
// bad — one word, and the coroutine is no longer cancellable
suspend fun tryPull(feed: FeedId): Result<Batch> = runCatching { feeds.pull(feed) }

// good — cancellation escapes, everything else becomes a failed Result
suspend fun tryPull(feed: FeedId): Result<Batch> =
    try {
        Result.success(feeds.pull(feed))
    } catch (e: CancellationException) {
        throw e
    } catch (e: IOException) {
        Result.failure(e)
    }
```

## 40.12 Never call a suspending function from `finally` without `withContext(NonCancellable)`.

> Why? Once a coroutine is cancelled its `Job` is in the cancelling state, and
> every suspension point in it throws `CancellationException` immediately. A
> `finally` block that awaits a cleanup call therefore never completes the
> cleanup: the connection is not returned, the lock is not released, the
> compensating write is not made. `withContext(NonCancellable)` is the
> documented escape hatch, and it must wrap only the cleanup — never the main
> body, which would make the whole operation uncancellable.
> **Violation — enforced by `detekt/SuspendFunInFinallySection`.**

```kotlin
// bad — on cancellation, `release` throws before it does anything
suspend fun withLease(id: LeaseId, block: suspend () -> Unit) {
    leases.acquire(id)
    try {
        block()
    } finally {
        leases.release(id)
    }
}

// good — the cleanup runs to completion even on a cancelled coroutine
suspend fun withLease(id: LeaseId, block: suspend () -> Unit) {
    leases.acquire(id)
    try {
        block()
    } finally {
        withContext(NonCancellable) {
            leases.release(id)
        }
    }
}
```

## 40.13 Never hardcode a dispatcher inside the function that uses it.

> Why? A `withContext(Dispatchers.IO)` written into the body is a dependency
> the caller cannot see and a test cannot replace, so the only remaining lever
> is `Dispatchers.setMain`, which mutates global state and makes the suite
> order-dependent ([Chapter 39, §39.12](39-coroutine-testing.md)). detekt's
> rule is one line — "always use dependency injection to inject dispatchers for
> easier testing" — and its compliant form is a constructor or parameter
> default, so the production call site is unchanged. See
> [Chapter 34](34-dispatchers-and-context.md) for which dispatcher to pick.
> **Violation — enforced by `detekt/InjectDispatcher`.**

```kotlin
// bad — untestable without mutating process-wide state
class ExportService(private val store: DocumentStore) {
    suspend fun export(id: DocumentId): Path = withContext(Dispatchers.IO) {
        store.writeTo(tempFile(), id)
    }
}

// good — injected, with the production dispatcher as the default
class ExportService(
    private val store: DocumentStore,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) {
    suspend fun export(id: DocumentId): Path = withContext(ioDispatcher) {
        store.writeTo(tempFile(), id)
    }
}
```

## 40.14 Never mark a function `suspend` when it returns a `Flow`.

> Why? Building a `Flow` does not execute it. The `suspend` modifier promises
> the caller that the function may suspend before returning, which is false for
> a cold flow builder, and it forces every caller into a coroutine just to
> obtain a value that is inert until collected. The result is a signature that
> lies about its cost and needlessly restricts where it can be called. If real
> suspending work must happen before the first emission, do it *inside* the
> flow builder, where it belongs. See [Chapter 36](36-flow.md).
> **Violation — enforced by `detekt/SuspendFunWithFlowReturnType`.**

```kotlin
// bad — nothing here suspends; the modifier restricts callers for no reason
suspend fun observePrices(symbol: Symbol): Flow<Price> =
    priceFeed.subscribe(symbol).map { it.toPrice() }

// good
fun observePrices(symbol: Symbol): Flow<Price> =
    priceFeed.subscribe(symbol).map { it.toPrice() }

// good — genuinely suspending setup, moved inside the builder
fun observePrices(symbol: Symbol): Flow<Price> = flow {
    val session = auth.openSession() // suspends, at collection time
    emitAll(priceFeed.subscribe(symbol, session).map { it.toPrice() })
}
```

## 40.15 Never leave a `suspend` modifier on a function that never suspends.

> Why? `suspend` is part of the contract: it tells the caller this function may
> yield, and it restricts the call to a coroutine body. A function that only
> does arithmetic, mapping, or validation makes both statements false, and the
> restriction spreads — the caller has to become `suspend` too, and so does
> theirs. detekt's rationale is that the function then "can only be used from
> other suspending functions", which "needlessly restricts use of the
> function". These usually appear as leftovers after the one suspending call
> inside was refactored away.
> **Violation — enforced by `detekt/RedundantSuspendModifier`.**

```kotlin
// bad — nothing in the body suspends
suspend fun toSummary(order: Order): OrderSummary =
    OrderSummary(order.id, order.lines.sumOf { it.total })

// good
fun toSummary(order: Order): OrderSummary =
    OrderSummary(order.id, order.lines.sumOf { it.total })
```

## 40.16 Never declare a `suspend` function with a `CoroutineScope` receiver.

> Why? The two mechanisms mean different things and combining them is
> ambiguous: the `suspend` modifier says "this runs inside *my* caller's
> coroutine", while the `CoroutineScope` receiver says "launch children into
> *that* scope". A reader cannot tell which scope a `launch` inside the body
> attaches to, and the function can silently outlive the caller that awaited
> it. Pick one — a non-suspending extension on `CoroutineScope`, or a `suspend`
> function that opens its own `coroutineScope { }`.
> **Violation — enforced by `detekt/SuspendFunWithCoroutineScopeReceiver`.**

```kotlin
// bad — is the launch a child of the receiver, or of the caller?
suspend fun CoroutineScope.prefetch(ids: List<OrderId>) {
    ids.forEach { id -> launch { cache.warm(id) } }
}

// good — a plain extension: children clearly belong to the receiver
fun CoroutineScope.prefetch(ids: List<OrderId>) {
    ids.forEach { id -> launch { cache.warm(id) } }
}

// good — a suspend function that owns its own scope and waits for it
suspend fun prefetch(ids: List<OrderId>) = coroutineScope {
    ids.forEach { id -> launch { cache.warm(id) } }
}
```

## 40.17 Never share mutable state between coroutines without confinement or a lock.

> Why? Coroutines on `Dispatchers.Default` or `Dispatchers.IO` run on multiple
> threads, so `count++` and `list += item` are the same data races they are in
> plain Java — with the extra trap that the code *looks* single-threaded
> because there is no `Thread` in sight. Single-threaded test runs (including
> `runTest`, which uses one thread) hide the bug completely. [Shared mutable
> state and
> concurrency](https://kotlinlang.org/docs/shared-mutable-state-and-concurrency.html)
> gives the options: confine the state to one place, make it immutable
> ([Chapter 25](25-immutability.md)), use an atomic, or guard it with a `Mutex`
> (§40.18). **Suggestion** — no linter can see this.

```kotlin
// bad — `results` is written from many threads; entries are silently lost
suspend fun priceAll(items: List<Item>): List<Price> = coroutineScope {
    val results = mutableListOf<Price>()
    items.forEach { item ->
        launch(Dispatchers.Default) { results += pricer.price(item) }
    }
    results
}

// good — no shared state at all: each coroutine returns its own value
suspend fun priceAll(items: List<Item>): List<Price> = coroutineScope {
    items
        .map { item -> async(Dispatchers.Default) { pricer.price(item) } }
        .awaitAll()
}
```

## 40.18 When shared mutable state is unavoidable, guard it with a `Mutex`, not a `synchronized` block.

> Why? `synchronized` blocks the thread while it waits. Inside a coroutine that
> means a dispatcher worker is parked on a monitor, and if the critical section
> itself suspends you cannot use `synchronized` at all — a `suspend` call is
> not allowed inside it. The
> [coroutines guide](https://kotlinlang.org/docs/shared-mutable-state-and-concurrency.html)
> states the distinction: "the key difference is that `Mutex.lock()` is a
> suspending function. It does not block a thread." Note that
> [`Mutex`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.sync/-mutex/)
> "is non-reentrant" — re-entering `withLock` on the same mutex from the same
> coroutine deadlocks, so keep critical sections flat. **Suggestion.**

```kotlin
// bad — parks a dispatcher thread, and cannot contain a suspending call
class SessionRegistry {
    private val lock = Any()
    private val sessions = mutableMapOf<UserId, Session>()

    fun put(id: UserId, session: Session) {
        synchronized(lock) { sessions[id] = session }
    }
}

// good — suspends rather than blocking, and the body may suspend
class SessionRegistry(private val store: SessionStore) {
    private val mutex = Mutex()
    private val sessions = mutableMapOf<UserId, Session>()

    suspend fun put(id: UserId, session: Session) {
        mutex.withLock {
            sessions[id] = session
            store.persist(id, session)
        }
    }
}
```

## 40.19 Never collect a hot flow in a scope that outlives the consumer.

> Why? `collect` on a `StateFlow` or `SharedFlow` never returns, so the
> collecting coroutine lives exactly as long as its scope. Attach it to an
> application-wide scope on behalf of a shorter-lived consumer and every
> consumer ever created stays subscribed: memory grows with the number of
> screens visited or requests served, and each stale collector still runs its
> side effects. The scope must be the *consumer's*, not the producer's. Where
> the sharing itself is the point, bound it with
> `SharingStarted.WhileSubscribed` so the upstream stops when the last
> subscriber leaves. See [Chapter 37](37-stateflow-and-sharedflow.md).
> **Suggestion.**

```kotlin
// bad — every DetailPresenter ever constructed keeps collecting forever
class DetailPresenter(private val appScope: CoroutineScope, private val repo: Repo) {
    init {
        appScope.launch {
            repo.updates.collect { render(it) }
        }
    }
}

// good — the collector dies with the presenter that owns it
class DetailPresenter(
    private val repo: Repo,
    dispatcher: CoroutineDispatcher = Dispatchers.Default,
) : AutoCloseable {
    private val scope = CoroutineScope(SupervisorJob() + dispatcher)

    init {
        scope.launch { repo.updates.collect { render(it) } }
    }

    override fun close() {
        scope.cancel()
    }
}

// good — a shared upstream that stops when the last subscriber leaves
val updates: StateFlow<Snapshot> = source.snapshots()
    .stateIn(appScope, SharingStarted.WhileSubscribed(5_000), Snapshot.EMPTY)
```

## 40.20 Never install a `CoroutineExceptionHandler` on `async`, or on a coroutine that has a parent.

> Why? The handler is a last-resort hook, not a `catch`. Its
> [reference](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-exception-handler/)
> says it is invoked only "if a coroutine fails without a clear propagation
> path", and gives both failing cases explicitly: on `async` "the caller of
> `async` is responsible for handling the exceptions in the returned
> `Deferred` value", so the handler is never called; and on a nested `launch`
> the exception goes to the parent first, so a handler installed on the child
> is dead code. Reviewers read the handler as error handling and stop looking —
> which is exactly why an unreachable one is worse than none. Handle `async`
> failures at `await()`, and install the handler on the root of a scope.
> **Suggestion.**

```kotlin
// bad — neither handler ever runs: async reports through await, and the
// nested launch propagates to its parent first
suspend fun refresh() = coroutineScope {
    val handler = CoroutineExceptionHandler { _, e -> logger.error(e) { "failed" } }
    async(handler) { index.rebuild() }
    launch { launch(handler) { cache.warm() } }
}

// good — the failure of an async is handled where it surfaces
suspend fun refresh() = coroutineScope {
    val rebuild = async { index.rebuild() }
    try {
        rebuild.await()
    } catch (e: CancellationException) {
        throw e
    } catch (e: IndexException) {
        logger.error(e) { "index rebuild failed" }
    }
}

// good — the handler belongs on the root of an owned scope
private val scope = CoroutineScope(
    SupervisorJob() +
        dispatcher +
        CoroutineExceptionHandler { _, e -> logger.error(e) { "background failure" } },
)
```
