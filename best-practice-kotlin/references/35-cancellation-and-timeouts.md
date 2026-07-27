<!-- Part of the `best-practice-kotlin` skill. See SKILL.md for the index. -->

# 35. Cancellation & Timeouts

Cancellation in Kotlin is not preemption. Nothing stops a running coroutine: the
runtime sets a flag on its `Job` and then waits for the coroutine to notice, and
the only places it can notice are suspension points and explicit checks. A
coroutine that neither suspends nor checks is uncancellable, and a coroutine that
catches the exception cancellation is delivered with is *worse* than
uncancellable — it reports success while the work it was asked to abandon carries
on.

That exception is `CancellationException`, and almost every rule in this chapter
is a consequence of one fact about it: it is a perfectly ordinary
`RuntimeException` as far as the language is concerned, so every broad `catch`
and every `runCatching` in the codebase swallows it by default. On the JVM,
`kotlin.coroutines.cancellation.CancellationException` is a typealias for
`java.util.concurrent.CancellationException`, which means a Java library's
`catch (Exception e)` will eat it too.

This chapter covers cooperative cancellation, the handling rules for
`CancellationException`, cancellation checks in non-suspending code, cleanup
under cancellation, and the timeout builders. It draws on
[Cancellation and timeouts](https://kotlinlang.org/docs/cancellation-and-timeouts.html),
[`withTimeout`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-timeout.html),
[`NonCancellable`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-non-cancellable/),
and
[`runInterruptible`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/run-interruptible.html).

Three neighbouring topics are deferred. Scopes, jobs, and how failure (as opposed
to cancellation) propagates are
[Chapter 33, Coroutine Fundamentals](33-coroutine-fundamentals.md). Which
dispatcher a blocking call belongs on is
[Chapter 34, Dispatchers & Coroutine Context](34-dispatchers-and-context.md).
The general Kotlin rules for `runCatching`, `Result`, and exception granularity —
which §35.2 and §35.3 specialise for coroutines — are
[Chapter 24, Exceptions & `Result`](24-exceptions-and-result.md). Virtual-time
testing of timeouts is [Chapter 39, Coroutine Testing](39-coroutine-testing.md).

**Tool alignment:** detekt's `coroutines` rule set covers part of this chapter.
`SleepInsteadOfDelay` is active in detekt's default configuration;
`SuspendFunInFinallySection` and `SuspendFunSwallowedCancellation` exist but are
**inactive by default** and must be switched on in `detekt.yml`. The general
`exceptions` rules `TooGenericExceptionCaught` and `SwallowedException` catch the
broad-`catch` half of §35.2. Rules a named check actually enforces are marked
**Violation**; the rest are **Suggestion**.

## 35.1 Treat cancellation as cooperative: a coroutine stops only where it suspends or where you check.

> Why? Cancelling a `Job` marks it and resumes its suspended continuation with a
> `CancellationException`. Every suspending function in `kotlinx.coroutines` —
> `delay`, `await`, `join`, `withContext`, channel operations — checks that flag
> and throws. Code that does none of those runs to completion regardless, so a
> `cancel()` on a tight computational loop achieves precisely nothing while the
> caller sits waiting for a `join` that will not return early. **Suggestion.**

```kotlin
// bad — nothing in the body suspends, so cancelling this job has no effect until
// the loop finishes on its own, ten minutes later
val job = scope.launch(defaultDispatcher) {
    var checksum = 0L
    for (block in blocks) {
        checksum = checksum xor block.hash()
    }
    results.record(checksum)
}
job.cancel()

// good — an explicit check makes the loop cancellable (§35.4)
val job = scope.launch(defaultDispatcher) {
    var checksum = 0L
    for (block in blocks) {
        ensureActive()
        checksum = checksum xor block.hash()
    }
    results.record(checksum)
}
job.cancel()
```

## 35.2 Never let a `catch` swallow `CancellationException` — and `catch (e: Exception)` does exactly that.

> Why? `CancellationException` is how cancellation is delivered. Catching it and
> continuing tells the parent "I finished normally" while the work it cancelled
> keeps running, so `join` returns, resources are released underneath a live
> coroutine, and shutdown hangs or corrupts. Because it is an ordinary
> `RuntimeException`, `catch (e: Exception)` — and `catch (e: Throwable)`, and a
> `catch` around a whole coroutine body — all capture it. Either catch a type
> narrow enough to exclude it, or rethrow it first.
> **Violation — enforced by `detekt/TooGenericExceptionCaught`** for the
> `catch (e: Exception)` form, and `detekt/SwallowedException` where the caught
> exception is neither rethrown nor passed on.

```kotlin
// bad — cancellation is reported as a failed import; the parent believes this
// coroutine ran to completion and the retry loop starts it all over again
suspend fun import(batch: Batch): ImportResult =
    try {
        ImportResult.Ok(importer.run(batch))
    } catch (e: Exception) {
        logger.warn("import failed", e)
        ImportResult.Failed(e)
    }

// good — rethrow cancellation first, then handle the errors you meant
suspend fun import(batch: Batch): ImportResult =
    try {
        ImportResult.Ok(importer.run(batch))
    } catch (e: CancellationException) {
        throw e
    } catch (e: ImportException) {
        logger.warn("import failed", e)
        ImportResult.Failed(e)
    }
```

## 35.3 Do not call a `suspend` function inside `runCatching`.

> Why? `runCatching` catches `Throwable`, so it has the §35.2 problem with no
> `catch` clause to fix. detekt states the rule directly: "Suspend functions
> should not be called inside `runCatching`'s lambda block, because `runCatching`
> catches all the `Exception`s. For Coroutines to work in all cases, developers
> should make sure to propagate `CancellationException` exceptions." The
> replacement detekt shows is an explicit `try`/`catch` with a
> `catch (e: CancellationException) { throw e }` clause first. If you want a
> `Result`-shaped return, build it from the narrow `catch`.
> **Violation — enforced by `detekt/SuspendFunSwallowedCancellation`** once
> enabled; it is inactive in detekt's default configuration. See
> [Chapter 24](24-exceptions-and-result.md) for the non-coroutine rules on
> `runCatching`.

```kotlin
// bad — a cancelled `deliver` becomes Result.failure and the caller retries it
suspend fun deliver(event: Event): Result<Receipt> =
    runCatching { webhookClient.deliver(event) }

// good
suspend fun deliver(event: Event): Result<Receipt> =
    try {
        Result.success(webhookClient.deliver(event))
    } catch (e: CancellationException) {
        throw e
    } catch (e: IOException) {
        Result.failure(e)
    }
```

## 35.4 Put `ensureActive()` inside any loop that computes without suspending.

> Why? `ensureActive()` "throws the `CancellationException` that was the scope's
> cancellation cause if the scope is no longer active" — it is the cancellation
> check for code that has no suspension point of its own. Prefer it to
> `if (!isActive) return`: returning normally tells the parent the work succeeded,
> whereas throwing propagates the actual cancellation cause and lets `join` and
> `await` behave correctly. Three receivers exist — `CoroutineScope`, `Job`, and
> `CoroutineContext` — so inside a `suspend` function with no scope receiver, use
> `currentCoroutineContext().ensureActive()`. **Suggestion.**

```kotlin
// bad — `isActive` plus a plain return: the parent sees a normal completion and
// the partially built index is treated as valid
scope.launch(defaultDispatcher) {
    for (document in corpus) {
        if (!isActive) return@launch
        index.add(analyser.analyse(document))
    }
}

// good — inside a launch, the CoroutineScope receiver supplies ensureActive()
scope.launch(defaultDispatcher) {
    for (document in corpus) {
        ensureActive()
        index.add(analyser.analyse(document))
    }
}

// good — inside a plain suspend function there is no scope receiver
suspend fun buildIndex(corpus: List<Document>): Index {
    val index = Index()
    for (document in corpus) {
        currentCoroutineContext().ensureActive()
        index.add(analyser.analyse(document))
    }
    return index
}
```

## 35.5 Use `yield()` when a long loop should also give the thread back, not merely observe cancellation.

> Why? `ensureActive()` is a check and nothing more: a CPU loop that calls it
> still monopolises its dispatcher thread for the whole run. `yield()` is a
> suspension point — it checks cancellation *and* offers the thread to other
> coroutines waiting on the same dispatcher. On a core-sized `Dispatchers.Default`
> pool, a handful of `ensureActive`-only loops will still starve every other
> coroutine in the process. Use `yield()` when the loop is long and shares a pool;
> use `ensureActive()` when it is short or already on a dedicated view.
> **Suggestion.**

```kotlin
// bad — cancellable, but the eight Default threads are held for the duration and
// nothing else in the service gets scheduled
suspend fun render(frames: List<Frame>) {
    for (frame in frames) {
        currentCoroutineContext().ensureActive()
        rasteriser.render(frame)
    }
}

// good — cancellable and fair
suspend fun render(frames: List<Frame>) {
    for (frame in frames) {
        yield()
        rasteriser.render(frame)
    }
}
```

## 35.6 Never write `Thread.sleep` where `delay` belongs.

> Why? `Thread.sleep` is not a suspension point, so it is not a cancellation
> point: a coroutine asleep for thirty seconds ignores cancellation for thirty
> seconds. It also blocks the carrier thread, and detekt spells out why that
> matters: "A thread can contain multiple coroutines at one time due to
> coroutines' lightweight nature, so if one coroutine invokes `Thread.sleep`, it
> could potentially halt the execution of unrelated coroutines and cause
> unpredictable behavior." `delay` suspends, releases the thread, and throws on
> cancellation. **Violation — enforced by `detekt/SleepInsteadOfDelay`.**

```kotlin
// bad — blocks a pool thread and ignores cancellation for the whole backoff
suspend fun retryAfter(backoff: Duration, block: suspend () -> Unit) {
    Thread.sleep(backoff.inWholeMilliseconds)
    block()
}

// good
suspend fun retryAfter(backoff: Duration, block: suspend () -> Unit) {
    delay(backoff)
    block()
}
```

## 35.7 Wrap suspending cleanup in `withContext(NonCancellable)` — and put nothing else in there.

> Why? A cancelled coroutine's `finally` block still runs, but it is running in a
> cancelled context, so the first `suspend` call inside it throws immediately and
> the rest of the cleanup never happens. detekt describes the failure exactly:
> "Without a non-cancellable context, these functions will not execute if the
> parent coroutine is cancelled." `withContext(NonCancellable)` is the sanctioned
> exception to §34.14's ban on overriding the `Job`. Keep the block minimal — it
> is unkillable by construction, so anything slow inside it turns cancellation
> into a hang — and, as the API reference advises, call `ensureActive()` after it
> before doing anything else.
> **Violation — enforced by `detekt/SuspendFunInFinallySection`** once enabled;
> it is inactive in detekt's default configuration.

```kotlin
// bad — on cancellation, `releaseBlocking` never runs and the lease leaks until
// its TTL expires
suspend fun withLease(key: Key, block: suspend () -> Unit) {
    val lease = leaseClient.acquire(key)
    try {
        block()
    } finally {
        leaseClient.release(lease)   // suspends; throws instantly if cancelled
    }
}

// good — cleanup completes; nothing but cleanup is protected
suspend fun withLease(key: Key, block: suspend () -> Unit) {
    val lease = leaseClient.acquire(key)
    try {
        block()
    } finally {
        withContext(NonCancellable) {
            leaseClient.release(lease)
        }
    }
}
```

## 35.8 Use `withTimeoutOrNull` when a timeout is an expected outcome, and `withTimeout` when it is a failure.

> Why? `withTimeout` throws `TimeoutCancellationException`; `withTimeoutOrNull`
> returns `null`. The choice is about what the timeout *means*. If exceeding the
> budget is normal — a cache probe, a best-effort enrichment, a health check —
> then a `null` you must handle is better than an exception you will be tempted
> to catch broadly (and thereby violate §35.2). If exceeding the budget means the
> operation failed, `withTimeout` gives you a stack trace and propagates.
> **Suggestion.**

```kotlin
// bad — a routine, expected timeout expressed as an exception, then caught with
// a clause broad enough to swallow real cancellation as well
val enrichment: Enrichment? =
    try {
        withTimeout(50.milliseconds) { enrichmentClient.lookup(key) }
    } catch (e: Exception) {
        null
    }

// good — the expected outcome is a value
val enrichment: Enrichment? =
    withTimeoutOrNull(50.milliseconds) { enrichmentClient.lookup(key) }

// good — a breached SLA is a failure, so let it throw
val settlement: Settlement =
    withTimeout(2.seconds) { settlementClient.settle(paymentId) }
```

## 35.9 Treat a timeout as asynchronous: assume any value produced inside `withTimeout` can be lost.

> Why? The API reference is blunt about the race: cancellation on timeout "runs
> concurrently the code running in the block and may happen at any time, even
> after the block finishes executing but before the caller gets resumed with the
> result." So a `withTimeout` block that acquires something — opens a connection,
> takes a permit, starts a transfer — can complete successfully and *still* have
> its result discarded, leaking whatever it acquired. Acquire outside the timeout,
> or release inside a `finally` (§35.7). **Suggestion.**

```kotlin
// bad — the connection can be opened microseconds before the timeout fires; the
// value is discarded and the socket is never closed
val connection = withTimeout(1.seconds) { pool.open(endpoint) }

// good — the resource is owned by a try/finally inside the timeout
withTimeout(1.seconds) {
    val connection = pool.open(endpoint)
    try {
        connection.handshake()
    } finally {
        withContext(NonCancellable) { connection.close() }
    }
}
```

## 35.10 Catch `TimeoutCancellationException` specifically; never catch `CancellationException` to detect a timeout.

> Why? `TimeoutCancellationException` is a subclass of `CancellationException`, so
> a `catch (e: CancellationException)` intended to spot a timeout will also
> capture a genuine cancellation from the parent and convert it into a "timed
> out" result — the §35.2 failure, wearing a plausible disguise. Catch the exact
> subtype, and note that it only escapes the `withTimeout` block it belongs to;
> catching it further out means catching someone else's timeout too.
> **Suggestion.**

```kotlin
// bad — a shutdown-driven cancellation is reported to the client as a gateway
// timeout, and the coroutine continues into the fallback path
suspend fun quote(request: QuoteRequest): Quote =
    try {
        withTimeout(quoteBudget) { pricingClient.quote(request) }
    } catch (e: CancellationException) {
        Quote.unavailable(request)
    }

// good
suspend fun quote(request: QuoteRequest): Quote =
    try {
        withTimeout(quoteBudget) { pricingClient.quote(request) }
    } catch (e: TimeoutCancellationException) {
        logger.warn("pricing timed out after {}", quoteBudget)
        Quote.unavailable(request)
    }
```

## 35.11 Use `cancelAndJoin` when you need the work to have stopped; `cancel` only asks.

> Why? `cancel()` returns as soon as the flag is set — the coroutine may still be
> mid-`finally`, mid-flush, or holding the file you are about to delete.
> `cancelAndJoin()` cancels and then suspends until the job has actually
> completed, which is what "stopped" means anywhere resources are involved.
> Getting this wrong produces the classic shutdown bug: the process exits, the
> cleanup coroutine never finishes, and the lock file survives.
> **Suggestion.**

```kotlin
// bad — the file may still be open when it is deleted
suspend fun abortUpload(job: Job, path: Path) {
    job.cancel()
    Files.deleteIfExists(path)
}

// good
suspend fun abortUpload(job: Job, path: Path) {
    job.cancelAndJoin()
    withContext(ioDispatcher) { Files.deleteIfExists(path) }
}
```

## 35.12 Cancel a scope you own exactly once, from a lifecycle hook, and never reuse it afterwards.

> Why? Cancelling a scope cancels its `Job`, and a cancelled `Job` is terminal:
> every subsequent `launch` on that scope produces a coroutine that is already
> cancelled and does nothing. There is no "restart" — the failure mode is silent,
> because `launch` still returns a `Job` and no exception is thrown. So the cancel
> belongs in the one place that runs at end of life (`DisposableBean.destroy`,
> `@PreDestroy`, a `close()`), and a scope that needs to come back must be
> replaced, not revived. **Suggestion.**

```kotlin
// bad — "pause" cancels the scope permanently; resume() silently does nothing
class Poller(private val source: Source) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    fun pause() = scope.cancel()
    fun resume() = scope.launch { source.poll() } // already-cancelled Job
}

// good — cancel the unit of work, not the scope; the scope dies with the bean
class Poller(private val source: Source) : DisposableBean {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var polling: Job? = null

    fun start() {
        polling = scope.launch { source.poll() }
    }

    suspend fun pause() {
        polling?.cancelAndJoin()
        polling = null
    }

    override fun destroy() = scope.cancel()
}
```

## 35.13 Cancel with a named cause whenever the reason will be read later.

> Why? `cancel()` with no argument produces a cancellation exception with a
> generic "Job was cancelled" message, and that is what lands in the log when it
> reaches a `catch` or a handler. `cancel(CancellationException("..."))` attaches
> a reason that `ensureActive()` rethrows verbatim — the API reference notes that
> "if the job was cancelled, thrown exception contains the original cancellation
> cause" — so the log line tells you whether this was shutdown, a client
> disconnect, or a budget breach. **Suggestion.**

```kotlin
// bad — the log says "Job was cancelled" and nothing else
fun onClientDisconnect(job: Job) = job.cancel()

// good
fun onClientDisconnect(job: Job) =
    job.cancel(CancellationException("client disconnected before response"))
```

## 35.14 Remember that a blocking call cannot be cancelled; make it interruptible with `runInterruptible` or bound it another way.

> Why? Cancellation reaches a coroutine at suspension points, and a thread parked
> inside `InputStream.read` or `PreparedStatement.executeQuery` has none.
> `withContext(Dispatchers.IO)` moves the blocking off the CPU pool but does
> nothing to make it stoppable — a cancelled coroutine will not return until the
> blocking call does, and a `withTimeout` around it expires without freeing the
> thread. `runInterruptible` is the bridge: it runs the block such that "the
> blocking code block will be interrupted and this function will throw
> `CancellationException` if the coroutine is cancelled", by interrupting the
> carrier thread. It only helps for APIs that honour `Thread.interrupt`; for the
> rest, the only real bound is the client's own socket or statement timeout.
> **Suggestion.**

```kotlin
// bad — withTimeout expires, the coroutine reports a timeout, and the IO thread
// stays parked in take() forever
suspend fun nextCommand(queue: BlockingQueue<Command>): Command? =
    withTimeoutOrNull(5.seconds) {
        withContext(ioDispatcher) { queue.take() }
    }

// good — cancellation interrupts the thread, so take() actually returns
suspend fun nextCommand(queue: BlockingQueue<Command>): Command? =
    withTimeoutOrNull(5.seconds) {
        runInterruptible(ioDispatcher) { queue.take() }
    }
```

## 35.15 Compose timeouts outer-longest to inner-shortest, and never rely on an inner timeout to bound an outer one.

> Why? Timeouts do not add up the way people expect. An outer `withTimeout` bounds
> the whole block including every retry, so an inner per-attempt timeout of 2
> seconds inside a 3-attempt retry loop needs an outer budget of at least 6
> seconds plus backoff, or the outer one fires mid-retry and the per-attempt
> timeout never gets to do its job. The subtle direction is the other one: an
> inner timeout *cannot* bound an outer operation, because the outer one may be
> stuck in code the inner one does not cover — a connection acquisition, a mutex,
> a blocking call (§35.14). State the end-to-end budget at the outermost layer and
> derive the inner ones from it. (`repeatWithBackoff` below stands in for whatever
> retry helper the project owns; `kotlinx.coroutines` ships no such builder.)
> **Suggestion.**

```kotlin
// bad — the outer budget is smaller than the retries it contains, so attempts 2
// and 3 are dead code and the failure always looks like an outer timeout
suspend fun fetchWithRetry(url: Url): Payload =
    withTimeout(2.seconds) {
        repeatWithBackoff(times = 3) {
            withTimeout(2.seconds) { httpClient.get(url) }
        }
    }

// good — the outer budget is the contract; the inner one is derived from it
private val totalBudget = 6.seconds
private val attemptBudget = 1500.milliseconds

suspend fun fetchWithRetry(url: Url): Payload =
    withTimeout(totalBudget) {
        repeatWithBackoff(times = 3) {
            withTimeout(attemptBudget) { httpClient.get(url) }
        }
    }
```
