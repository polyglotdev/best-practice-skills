<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 34. Dispatchers & Coroutine Context

Every coroutine carries a `CoroutineContext` — a small, immutable, type-keyed map
that answers four questions: which `Job` owns me, which `CoroutineDispatcher`
resumes me, what am I called, and who hears about an unhandled failure. Getting
the dispatcher wrong is the most expensive mistake in the set, because a blocking
call on the wrong pool does not fail: it quietly consumes a thread that the rest
of the application was counting on, and the symptom shows up somewhere else
entirely, minutes later, as latency.

This chapter covers context composition, the four standard dispatchers and what
each is actually for, `limitedParallelism`, dispatcher injection, and how
thread-local state (notably the SLF4J MDC) survives — or does not survive — a
suspension. It draws on
[Coroutine context and dispatchers](https://kotlinlang.org/docs/coroutine-context-and-dispatchers.html),
the [`Dispatchers`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/)
API reference, and
[`CoroutineDispatcher.limitedParallelism`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-dispatcher/limited-parallelism.html).

Three neighbouring topics are deferred. The `Job` half of the context — parents,
children, supervision, and how failure travels — is
[Chapter 33, Coroutine Fundamentals](33-coroutine-fundamentals.md). Cancellation,
`NonCancellable`, and timeouts are
[Chapter 35, Cancellation & Timeouts](35-cancellation-and-timeouts.md).
Substituting a `TestDispatcher` for the real one, which is the entire payoff of
§34.8, is [Chapter 39, Coroutine Testing](39-coroutine-testing.md). The structured
logging conventions the MDC rules assume are
[Chapter 31, Logging](31-logging.md).

**Tool alignment:** detekt's `coroutines` rule set covers part of this chapter.
`InjectDispatcher` is active in detekt's default configuration.
`SleepInsteadOfDelay` is active too, though it belongs to
[Chapter 35](35-cancellation-and-timeouts.md). Rules a named check actually
enforces are marked **Violation**; the rest are **Suggestion**.

## 34.1 Read a `CoroutineContext` as a type-indexed set of elements, and remember that `+` lets the right-hand operand win.

> Why? `CoroutineContext` behaves like an immutable map keyed by each element's
> companion `Key`: at most one `Job`, one `ContinuationInterceptor` (the
> dispatcher), one `CoroutineName`, one `CoroutineExceptionHandler`. `plus`
> replaces same-keyed elements rather than accumulating them, so
> `Dispatchers.IO + Dispatchers.Default` is just `Dispatchers.Default`. Reading
> `+` as "and also" instead of "override" produces contexts that silently discard
> half of what you wrote. **Suggestion.**

```kotlin
// bad — two dispatchers, one key: Default wins and the IO intent is lost
val context = Dispatchers.IO + Dispatchers.Default + CoroutineName("import")

// good — one element per key, and an explicit lookup when you need one back
val context = Dispatchers.IO + CoroutineName("import") + SupervisorJob()
val name: CoroutineName? = context[CoroutineName]
```

## 34.2 Use `Dispatchers.Default` for CPU-bound work, and do not size it yourself.

> Why? `Dispatchers.Default` is backed by a shared pool whose maximum thread
> count is, per the API reference, "equal to the number of CPU cores, but is at
> least two". That is the right size for work that is genuinely computing: more
> threads than cores buys context switches, not throughput. It is also the
> dispatcher every builder falls back to when none is specified, so a coroutine
> that does CPU work needs no dispatcher argument at all. What it must never see
> is a blocking call — every blocked thread is a core the rest of the application
> cannot use. **Suggestion.**

```kotlin
// bad — a blocking JDBC call parked on the CPU pool; on an 8-core box, eight of
// these stall every other Default coroutine in the process
suspend fun report(ids: List<OrderId>): Report = withContext(Dispatchers.Default) {
    ids.map { orderDao.findBlocking(it) }.fold(Report.EMPTY, Report::plus)
}

// good — CPU work on Default, the blocking fetch on IO (§34.3)
suspend fun report(ids: List<OrderId>): Report {
    val orders = withContext(ioDispatcher) { ids.map { orderDao.findBlocking(it) } }
    return withContext(defaultDispatcher) { orders.fold(Report.EMPTY, Report::plus) }
}
```

## 34.3 Use `Dispatchers.IO` for blocking calls, and know that its 64-thread floor is a floor, not a budget.

> Why? The API reference states that IO parallelism "defaults to the limit of 64
> threads or the number of cores (whichever is larger)", configurable through the
> `kotlinx.coroutines.io.parallelism` system property. Two properties follow.
> First, `Dispatchers.IO` shares its threads with `Dispatchers.Default`, so
> "`withContext(Dispatchers.IO)` when already running on the `Default` dispatcher
> typically does not lead to an actual switching to another thread" — the switch
> is cheap. Second, 64 is a *concurrency* limit on blocking work, not a
> reservation: sixty-five slow HTTP calls will queue, and nothing tells you they
> are queueing. If a downstream needs a different bound, take a view (§34.7).
> **Suggestion.**

```kotlin
// bad — blocking HTTP on Default; the pool is core-sized, so a handful of slow
// calls starve every coroutine in the process
suspend fun fetch(url: Url): Payload = withContext(Dispatchers.Default) {
    httpClient.executeBlocking(url)
}

// good
suspend fun fetch(url: Url): Payload = withContext(ioDispatcher) {
    httpClient.executeBlocking(url)
}
```

## 34.4 Put the `withContext(Dispatchers.IO)` inside the function that blocks, not around the call to it.

> Why? This is the mechanical form of the main-safety rule in
> [§33.13](33-coroutine-fundamentals.md). A `withContext` at the call site has to
> be repeated at every call site and will eventually be forgotten at one of them;
> a `withContext` in the callee is written once and cannot be forgotten. It also
> puts the switch immediately adjacent to the blocking call it protects, so a
> reviewer can see that the two match. **Suggestion.**

```kotlin
// bad — the switch is the caller's job, so it is missing from the second caller
suspend fun sync() {
    withContext(ioDispatcher) { ledgerDao.appendBlocking(entry) }
}

suspend fun replay() {
    ledgerDao.appendBlocking(entry) // blocks whatever dispatcher we are on
}

// good — one switch, in the one place that blocks
class LedgerRepository(
    private val ledgerDao: LedgerDao,
    private val ioDispatcher: CoroutineDispatcher,
) {
    suspend fun append(entry: LedgerEntry) = withContext(ioDispatcher) {
        ledgerDao.appendBlocking(entry)
    }
}
```

## 34.5 Hoist `withContext` out of a loop; never switch dispatchers per element.

> Why? Every `withContext` that actually changes dispatcher is a suspension and a
> re-dispatch: the continuation is queued, a pool thread picks it up, and the
> coroutine resumes. Doing that once per element in a ten-thousand-element loop
> turns a cheap traversal into ten thousand scheduling round trips. Switch once,
> outside the loop, and do all the blocking work in one visit. **Suggestion.**

```kotlin
// bad — one dispatch per row
suspend fun importAll(rows: List<Row>) {
    rows.forEach { row ->
        withContext(ioDispatcher) { rowDao.insertBlocking(row) }
    }
}

// good — one dispatch for the whole batch
suspend fun importAll(rows: List<Row>) = withContext(ioDispatcher) {
    rows.forEach { row -> rowDao.insertBlocking(row) }
}
```

## 34.6 Do not create your own thread pool with `newSingleThreadContext` or `newFixedThreadPoolContext`.

> Why? Both are `@DelicateCoroutinesApi`, and `newSingleThreadContext` is
> `@ExperimentalCoroutinesApi` on top of that, so neither can be called without an
> explicit opt-in. The API reference warns that the result
> "is a closeable resource with the associated native resources (threads or
> native workers). It should not be allocated in place, should be closed at the
> end of its lifecycle, and has non-trivial memory and CPU footprint" — and in
> practice nobody closes it, so each call leaks a thread. The reference names the
> replacement directly: "If you do not need a separate thread pool, but only have
> to limit effective parallelism of the dispatcher, it is recommended to use
> `Dispatchers.IO.limitedParallelism(1)` or `Dispatchers.Default.limitedParallelism(1)`
> instead." **Suggestion.**

```kotlin
// bad — a dedicated thread per call site, never closed
suspend fun applyMigration(migration: Migration) {
    withContext(newSingleThreadContext("migrations")) {
        migrationRunner.runBlocking(migration)
    }
}

// good — a serialised view over the shared IO pool; no new threads, nothing to close
private val migrationDispatcher = Dispatchers.IO.limitedParallelism(1, "migrations")

suspend fun applyMigration(migration: Migration) = withContext(migrationDispatcher) {
    migrationRunner.runBlocking(migration)
}
```

## 34.7 Bound a shared downstream with `limitedParallelism`, and do not mistake it for a mutex.

> Why? `limitedParallelism(parallelism, name)` returns "a view of the current
> dispatcher that limits the parallelism to the given value", using the original
> dispatcher's threads. On `Dispatchers.IO` the views are *elastic*: the reference
> notes their parallelism "is not restricted by the `Dispatchers.IO` parallelism",
> so per-downstream views are the intended way to stop one slow dependency from
> consuming the whole IO budget. What it does not give you is mutual exclusion —
> the docs are explicit that it "is not a mutex", because a limited view still
> lets a coroutine suspend and another one run on the same thread. For mutual
> exclusion use `Mutex` or `Semaphore` — the reference says as much, pointing at
> both by name. One version note: the second `name` parameter is a recent
> addition, so on older kotlinx.coroutines releases only the one-argument
> `limitedParallelism(parallelism)` overload exists. **Suggestion.**

```kotlin
// bad — limitedParallelism(1) used as a lock; `read` suspends inside the block,
// a second coroutine enters, and the read-modify-write interleaves
private val lockLike = Dispatchers.IO.limitedParallelism(1)

suspend fun increment(key: Key) = withContext(lockLike) {
    val current = store.read(key)      // suspends — the "lock" is released
    store.write(key, current + 1)
}

// good — a view to bound the downstream, a Mutex for exclusion
private val storeDispatcher = Dispatchers.IO.limitedParallelism(8, "store")
private val mutex = Mutex()

suspend fun increment(key: Key) = withContext(storeDispatcher) {
    mutex.withLock {
        store.write(key, store.read(key) + 1)
    }
}
```

## 34.8 Inject dispatchers as constructor parameters; never reference `Dispatchers.*` inline.

> Why? A hardcoded `Dispatchers.IO` cannot be replaced by a `TestDispatcher`, so
> every test of that class runs on real threads with real scheduling and either
> becomes flaky or grows a `delay`-and-hope. detekt's rule is explicit: "Always
> use dependency injection to inject dispatchers for easier testing." A default
> argument keeps production call sites unchanged while leaving the seam open.
> **Violation — enforced by `detekt/InjectDispatcher`**, whose `dispatcherNames`
> default is `['IO', 'Default', 'Unconfined']`.

```kotlin
// bad — no seam; the test has to tolerate the real IO pool
class SettlementService(private val gateway: Gateway) {
    suspend fun settle(id: PaymentId) = withContext(Dispatchers.IO) {
        gateway.settleBlocking(id)
    }
}

// good — injected, with a production-shaped default
class SettlementService(
    private val gateway: Gateway,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) {
    suspend fun settle(id: PaymentId) = withContext(ioDispatcher) {
        gateway.settleBlocking(id)
    }
}
```

## 34.9 Never use `Dispatchers.Unconfined` in production code.

> Why? `Dispatchers.Unconfined` "starts a coroutine in the caller thread, but only
> until the first suspension point. After suspension it resumes the coroutine in
> the thread that is fully determined by the suspending function that was
> invoked." That means the thread your code runs on after a suspension is chosen
> by whichever library you happened to call — an HTTP client's event-loop thread,
> a driver's callback thread — and you are now doing work there. The guide's own
> verdict: "The unconfined dispatcher should not be used in general code."
> Its legitimate uses are inside coroutine machinery and, as
> `UnconfinedTestDispatcher`, in tests ([Chapter 39](39-coroutine-testing.md)).
> **Suggestion** — `detekt/InjectDispatcher` lists `Unconfined` among the names
> it flags when referenced inline, but nothing flags an injected one.

```kotlin
// bad — after `awaitResponse` suspends, the rest of this block runs on the HTTP
// client's IO-selector thread, and the CPU work there stalls every other request
scope.launch(Dispatchers.Unconfined) {
    val response = httpClient.awaitResponse(request)
    reportBuilder.render(response) // expensive, on someone else's thread
}

// good
scope.launch(defaultDispatcher) {
    val response = httpClient.awaitResponse(request)
    reportBuilder.render(response)
}
```

## 34.10 Treat `Dispatchers.Main` as a client-side concern; on a server it is a startup failure waiting to happen.

> Why? `Dispatchers.Main` is supplied by a platform artifact —
> `kotlinx-coroutines-android`, `kotlinx-coroutines-javafx`, or
> `kotlinx-coroutines-swing` — selected through `ServiceLoader`. On a JVM server
> none of those is on the classpath, and the reference states that accessing
> `Dispatchers.Main` then throws `IllegalStateException`. Because the lookup is
> lazy, the failure surfaces the first time the code path executes, not at
> startup, so a `Dispatchers.Main` reference copied out of an Android sample can
> sit dormant in a service for weeks. **Suggestion.**

```kotlin
// bad — on a Spring Boot service this throws IllegalStateException the first time
// the handler runs, not at boot
scope.launch(Dispatchers.Main) {
    view.render(model)
}

// good — server-side, name the dispatcher the work actually needs
scope.launch(defaultDispatcher) {
    renderer.render(model)
}
```

## 34.11 Give every long-lived scope a `CoroutineName`.

> Why? A coroutine has no identity in a thread dump by default — you get
> `DefaultDispatcher-worker-3` and nothing else. `CoroutineName` "serves the same
> purpose as the thread name. It is included in the thread name that is executing
> this coroutine when the debugging mode is turned on"
> (`-Dkotlinx.coroutines.debug`), and it shows up in the IDE's coroutine debugger
> and in `DebugProbes` dumps. On a service with several background scopes, this is
> the difference between "something is stuck" and "the reconciliation scope is
> stuck". **Suggestion.**

```kotlin
// bad — indistinguishable from every other background scope in a thread dump
private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

// good
private val scope =
    CoroutineScope(SupervisorJob() + defaultDispatcher + CoroutineName("reconciler"))
```

## 34.12 Never read or write a bare `ThreadLocal` across a suspension point.

> Why? A coroutine is not pinned to a thread: it can resume on a different one
> after every suspension, so a `ThreadLocal` set before a `delay` is simply gone
> after it, and a `ThreadLocal` set *inside* a coroutine leaks onto whichever pool
> thread happened to run it. `ThreadLocal.asContextElement()` fixes the first
> problem — it "creates an additional context element which keeps the value of the
> given `ThreadLocal` and restores it every time the coroutine switches its
> context". It does not fix the second: the guide notes that "when a thread-local
> is mutated, a new value is not propagated to the coroutine caller". Treat
> thread-locals as read-only inside coroutines. **Suggestion.**

```kotlin
// bad — the value is set on one pool thread and read on another; usually null,
// occasionally another request's value, which is worse
private val tenant = ThreadLocal<TenantId>()

suspend fun handle(request: Request) {
    tenant.set(request.tenantId)
    val rows = repository.load()          // suspends; may resume on another thread
    audit.record(tenant.get(), rows.size) // null, or someone else's tenant
}

// good — carried by the context, restored on every resume
suspend fun handle(request: Request) =
    withContext(tenant.asContextElement(value = request.tenantId)) {
        val rows = repository.load()
        audit.record(tenant.get(), rows.size)
    }
```

## 34.13 Propagate the SLF4J MDC with `MDCContext`, and re-capture it whenever you add a key inside a coroutine.

> Why? Correlation ids live in the SLF4J MDC, which is a `ThreadLocal`, so
> §34.12 applies: without help, a coroutine that suspends resumes with an empty
> or foreign MDC and every log line after the first suspension loses its trace id.
> `MDCContext` from the `kotlinx-coroutines-slf4j` artifact is the
> `ThreadContextElement` that fixes it — it captures `MDC.getCopyOfContextMap()`
> at construction and reinstalls it on every resume. The trap is that it captures
> *at construction*: an `MDC.put` performed inside the coroutine is discarded at
> the next suspension unless you enter a fresh `withContext(MDCContext())`.
> See [Chapter 31, Logging](31-logging.md) for the surrounding conventions.
> **Suggestion.**

```kotlin
// bad — `orderId` is captured by nothing; after `delay` the MDC is back to what
// the enclosing MDCContext captured, and the key is gone
scope.launch(MDCContext()) {
    MDC.put("orderId", order.id.value)
    delay(100.milliseconds)
    logger.info("settled")            // no orderId
}

// good — mutate, then re-capture
scope.launch(MDCContext()) {
    MDC.put("orderId", order.id.value)
    withContext(MDCContext()) {
        delay(100.milliseconds)
        logger.info("settled")        // orderId present
    }
}
```

## 34.14 Know what a child inherits and what `withContext` replaces — and never pass a `Job` to `withContext`.

> Why? A child inherits its parent's context wholesale and then adds its own
> `Job`, whose parent is the inherited one; that parent link is what makes
> cancellation and failure propagation work. `withContext(x)` overrides only the
> same-keyed elements of `x` and keeps everything else. Passing a `Job` overrides
> the one element that must not be overridden: the API reference says doing so
> "breaks structured concurrency and is not a supported pattern", tolerated only
> for backward compatibility — the block no longer fails its caller, and the
> caller's cancellation no longer reaches the block. `NonCancellable` is the one
> sanctioned exception, for cleanup only
> ([Chapter 35, §35.7](35-cancellation-and-timeouts.md)). **Suggestion.**

```kotlin
// bad — a detached Job: cancelling the caller no longer cancels this work, and a
// failure inside no longer fails the caller
suspend fun flush() = withContext(Job() + ioDispatcher) {
    writer.flushBlocking()
}

// good — override only the dispatcher; the Job link stays intact
suspend fun flush() = withContext(ioDispatcher) {
    writer.flushBlocking()
}
```

## 34.15 On JDK 21+, choose either virtual threads or coroutines per layer; if you bridge them, adapt the executor and keep the bound.

> Why? Virtual threads and coroutines solve the same problem — making blocking
> cheap — and stacking them buys nothing while doubling the number of schedulers
> in a stack trace. Coroutines do not run on virtual threads automatically:
> `Dispatchers.IO` is a platform-thread pool regardless of the JDK. If you do want
> coroutine work on virtual threads, the bridge is
> `Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()` — but note
> that it is unbounded, so it silently removes the back-pressure that
> `Dispatchers.IO`'s 64-thread floor was providing, and the resulting
> `ExecutorCoroutineDispatcher` must be closed. Also note the JDK floor: before
> [JEP 491](https://openjdk.org/jeps/491), delivered in **JDK 24**, a virtual
> thread that blocked inside a `synchronized` block pinned its carrier, so on JDK
> 21 through 23 a `synchronized`-heavy library defeats the whole exercise.
> **Suggestion.**

```kotlin
// bad — a coroutine per request wrapped in a virtual thread per request: two
// schedulers, unbounded concurrency, and a runBlocking parked on every one of them
fun handle(request: Request): Response {
    val result = AtomicReference<Response>()
    val thread = Thread.ofVirtual().start {
        result.set(runBlocking { service.handle(request) })
    }
    thread.join()
    return result.get()
}

// good — one model. Coroutines all the way down, IO for the blocking calls.
suspend fun handle(request: Request): Response = service.handle(request)

// good — if a virtual-thread executor is genuinely wanted, adapt it once, bound
// it, and close it with the component that owns it
private val vtDispatcher: ExecutorCoroutineDispatcher =
    Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()
private val boundedVt = vtDispatcher.limitedParallelism(256, "legacy-jdbc")

override fun destroy() {
    vtDispatcher.close()
}
```
